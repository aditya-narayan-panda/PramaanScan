import tensorflow as tf
from tensorflow.keras import layers, Model
from tensorflow.keras.applications import EfficientNetV2B0


# ============================================================
# CONFIG
# ============================================================

IMG_SIZE = 224
SEQ_LEN = 16

FEATURE_DIM = 256
NUM_HEADS = 4
FF_DIM = 512
NUM_TRANSFORMER_BLOCKS = 2

DENSE_DROPOUT = 0.35


# ============================================================
# WEIGHTED TEMPORAL POOLING
# ============================================================

@tf.keras.utils.register_keras_serializable(
    package="PramaanScan"
)
class WeightedAverage(layers.Layer):

    def call(self, inputs):

        x, weights = inputs

        return tf.reduce_sum(
            x * weights,
            axis=1
        )

    def compute_output_shape(self, input_shape):

        return (
            None,
            input_shape[0][-1]
        )

    def get_config(self):

        return super().get_config()


# ============================================================
# TEMPORAL POSITION EMBEDDING
# ============================================================

@tf.keras.utils.register_keras_serializable(
    package="PramaanScan"
)
class TemporalPositionEmbedding(layers.Layer):

    def __init__(
        self,
        sequence_length,
        feature_dim,
        **kwargs
    ):
        super().__init__(**kwargs)

        self.sequence_length = sequence_length
        self.feature_dim = feature_dim

        self.position_embedding = layers.Embedding(
            input_dim=sequence_length,
            output_dim=feature_dim,
            name="position_embedding"
        )

    def build(self, input_shape):
        """
        Explicitly build the nested Embedding layer.

        This is important for Keras .keras serialization/loading.
        """

        self.position_embedding.build(
            (self.sequence_length,)
        )

        super().build(input_shape)

    def call(self, x):

        positions = tf.range(
            start=0,
            limit=self.sequence_length,
            delta=1
        )

        positions = self.position_embedding(
            positions
        )

        positions = tf.expand_dims(
            positions,
            axis=0
        )

        return x + positions

    def compute_output_shape(self, input_shape):
        return input_shape

    def get_config(self):

        config = super().get_config()

        config.update({
            "sequence_length": self.sequence_length,
            "feature_dim": self.feature_dim
        })

        return config

# ============================================================
# TRANSFORMER BLOCK
# ============================================================

def transformer_block(
    x,
    block_id,
    feature_dim=FEATURE_DIM,
    num_heads=NUM_HEADS,
    ff_dim=FF_DIM,
    dropout=DENSE_DROPOUT
):

    prefix = f"transformer_{block_id}"

    # --------------------------------------------------------
    # ATTENTION NORMALIZATION
    # --------------------------------------------------------

    attn_input = layers.LayerNormalization(
        epsilon=1e-6,
        name=f"{prefix}_attention_normalization"
    )(x)

    # --------------------------------------------------------
    # MULTI HEAD SELF ATTENTION
    # --------------------------------------------------------

    attention = layers.MultiHeadAttention(
        num_heads=num_heads,
        key_dim=feature_dim // num_heads,
        dropout=dropout,
        name=f"{prefix}_multi_head_attention"
    )(
        attn_input,
        attn_input
    )

    attention = layers.Dropout(
        dropout,
        name=f"{prefix}_attention_dropout"
    )(attention)

    # --------------------------------------------------------
    # RESIDUAL CONNECTION
    # --------------------------------------------------------

    x = layers.Add(
        name=f"{prefix}_attention_residual"
    )(
        [
            x,
            attention
        ]
    )

    # --------------------------------------------------------
    # FEED FORWARD NORMALIZATION
    # --------------------------------------------------------

    ff_input = layers.LayerNormalization(
        epsilon=1e-6,
        name=f"{prefix}_ffn_normalization"
    )(x)

    # --------------------------------------------------------
    # FEED FORWARD NETWORK
    # --------------------------------------------------------

    ff = layers.Dense(
        ff_dim,
        activation="gelu",
        name=f"{prefix}_ffn_dense_1"
    )(ff_input)

    ff = layers.Dropout(
        dropout,
        name=f"{prefix}_ffn_dropout_1"
    )(ff)

    ff = layers.Dense(
        feature_dim,
        name=f"{prefix}_ffn_dense_2"
    )(ff)

    ff = layers.Dropout(
        dropout,
        name=f"{prefix}_ffn_dropout_2"
    )(ff)

    # --------------------------------------------------------
    # RESIDUAL CONNECTION
    # --------------------------------------------------------

    x = layers.Add(
        name=f"{prefix}_ffn_residual"
    )(
        [
            x,
            ff
        ]
    )

    return x


# ============================================================
# BUILD MODEL
# ============================================================

def build_model():

    # --------------------------------------------------------
    # INPUT
    # --------------------------------------------------------

    video_input = layers.Input(
        shape=(
            SEQ_LEN,
            IMG_SIZE,
            IMG_SIZE,
            3
        ),
        name="video"
    )

    # --------------------------------------------------------
    # EFFICIENTNET V2 B0
    # --------------------------------------------------------

    backbone = EfficientNetV2B0(
        include_top=False,
        weights="imagenet",
        pooling="avg",
        input_shape=(
            IMG_SIZE,
            IMG_SIZE,
            3
        )
    )

    # Freeze ImageNet backbone initially

    backbone.trainable = False

    # --------------------------------------------------------
    # FRAME FEATURE EXTRACTION
    # --------------------------------------------------------

    x = layers.TimeDistributed(
        backbone,
        name="backbone"
    )(
        video_input
    )

    # Expected:
    #
    # (batch, 16, 1280)
    #

    # --------------------------------------------------------
    # FEATURE PROJECTION
    # --------------------------------------------------------

    x = layers.TimeDistributed(
        layers.Dense(
            FEATURE_DIM,
            activation="gelu"
        ),
        name="feature_projection"
    )(x)

    x = layers.TimeDistributed(
        layers.Dropout(
            DENSE_DROPOUT
        ),
        name="feature_dropout"
    )(x)

    # Expected:
    #
    # (batch, 16, 256)
    #

    # --------------------------------------------------------
    # POSITION INFORMATION
    # --------------------------------------------------------

    x = TemporalPositionEmbedding(
        sequence_length=SEQ_LEN,
        feature_dim=FEATURE_DIM,
        name="temporal_position_embedding"
    )(x)

    # Shape:
    #
    # (batch, 16, 256)
    #

    # --------------------------------------------------------
    # TRANSFORMER BLOCKS
    # --------------------------------------------------------

    for block_id in range(
        NUM_TRANSFORMER_BLOCKS
    ):

        x = transformer_block(
            x,
            block_id=block_id,
            feature_dim=FEATURE_DIM,
            num_heads=NUM_HEADS,
            ff_dim=FF_DIM,
            dropout=DENSE_DROPOUT
        )

    # --------------------------------------------------------
    # TEMPORAL ATTENTION
    # --------------------------------------------------------

    attention_logits = layers.Dense(
        1,
        name="temporal_attention_logits"
    )(x)

    attention_weights = layers.Softmax(
        axis=1,
        name="temporal_attention_weights"
    )(attention_logits)

    # --------------------------------------------------------
    # WEIGHTED TEMPORAL POOLING
    # --------------------------------------------------------

    x = WeightedAverage(
        name="weighted_temporal_pooling"
    )(
        [
            x,
            attention_weights
        ]
    )

    # Shape:
    #
    # (batch, 256)
    #

    # --------------------------------------------------------
    # CLASSIFICATION HEAD
    # --------------------------------------------------------

    x = layers.LayerNormalization(
        epsilon=1e-6,
        name="classification_normalization"
    )(x)

    x = layers.Dropout(
        DENSE_DROPOUT,
        name="classification_dropout"
    )(x)

    x = layers.Dense(
        128,
        activation="gelu",
        name="classification_dense"
    )(x)

    x = layers.Dropout(
        DENSE_DROPOUT,
        name="classification_dropout_2"
    )(x)

    # --------------------------------------------------------
    # OUTPUT
    # --------------------------------------------------------

    output = layers.Dense(
        1,
        activation="sigmoid",
        name="deepfake_probability"
    )(x)

    # --------------------------------------------------------
    # MODEL
    # --------------------------------------------------------

    model = Model(
        inputs=video_input,
        outputs=output,
        name="PramaanScan_EfficientNetV2_Transformer"
    )

    # --------------------------------------------------------
    # COMPILE
    # --------------------------------------------------------

    model.compile(
        optimizer=tf.keras.optimizers.AdamW(
            learning_rate=2e-4,
            weight_decay=1e-4
        ),

        loss=tf.keras.losses.BinaryCrossentropy(
            label_smoothing=0.02
        ),

        metrics=[
            tf.keras.metrics.BinaryAccuracy(
                name="accuracy"
            ),

            tf.keras.metrics.AUC(
                name="auc"
            ),

            tf.keras.metrics.Precision(
                name="precision"
            ),

            tf.keras.metrics.Recall(
                name="recall"
            )
        ]
    )

    return model


# ============================================================
# FINE TUNING
# ============================================================

def unfreeze_backbone(
    model,
    last_layers=30
):

    # --------------------------------------------------------
    # GET BACKBONE
    # --------------------------------------------------------

    backbone_wrapper = model.get_layer(
        "backbone"
    )

    backbone = backbone_wrapper.layer

    # --------------------------------------------------------
    # FREEZE ALL
    # --------------------------------------------------------

    backbone.trainable = True

    for layer in backbone.layers:

        layer.trainable = False

    # --------------------------------------------------------
    # UNFREEZE LAST N LAYERS
    # --------------------------------------------------------

    for layer in backbone.layers[
        -last_layers:
    ]:

        layer.trainable = True

    # --------------------------------------------------------
    # KEEP BATCH NORMALIZATION FROZEN
    # --------------------------------------------------------

    for layer in backbone.layers:

        if isinstance(
            layer,
            layers.BatchNormalization
        ):

            layer.trainable = False

    # --------------------------------------------------------
    # RECOMPILE
    # --------------------------------------------------------

    model.compile(
        optimizer=tf.keras.optimizers.AdamW(
            learning_rate=1e-5,
            weight_decay=1e-5
        ),

        loss=tf.keras.losses.BinaryCrossentropy(
            label_smoothing=0.01
        ),

        metrics=[
            tf.keras.metrics.BinaryAccuracy(
                name="accuracy"
            ),

            tf.keras.metrics.AUC(
                name="auc"
            ),

            tf.keras.metrics.Precision(
                name="precision"
            ),

            tf.keras.metrics.Recall(
                name="recall"
            )
        ]
    )

    return model