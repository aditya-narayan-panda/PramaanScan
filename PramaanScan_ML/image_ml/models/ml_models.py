"""
Praman Scan - Classical ML model definitions.

Only classical machine learning is used in this project (no deep learning,
no CNNs, no PyTorch/TensorFlow). This module simply centralises the
construction of the three estimators so that train.py and any future
retraining tooling stay in sync on hyperparameters, which are themselves
sourced from config.py (and therefore overridable via environment
variables without touching code).
"""
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression

from image_ml.config import get_settings

settings = get_settings()


def build_svm() -> SVC:
    """Support Vector Machine with probability estimates enabled so we can
    read out P(AI Generated) rather than just a hard label.

    If external probability calibration (CalibratedClassifierCV) is going
    to be applied afterwards in train.py, we skip SVC's own internal Platt
    scaling here (probability=False) to avoid calibrating twice and to
    speed up hyperparameter search - CalibratedClassifierCV will provide
    the final predict_proba either way, so this always stays safe."""
    return SVC(
        kernel=settings.SVM_KERNEL,
        C=settings.SVM_C,
        probability=not settings.ENABLE_PROBABILITY_CALIBRATION,
        class_weight="balanced",
        random_state=settings.RANDOM_STATE,
    )


def build_random_forest() -> RandomForestClassifier:
    return RandomForestClassifier(
        n_estimators=settings.RF_N_ESTIMATORS,
        max_depth=settings.RF_MAX_DEPTH,
        class_weight="balanced",
        random_state=settings.RANDOM_STATE,
        n_jobs=-1,
    )


def build_logistic_regression() -> LogisticRegression:
    return LogisticRegression(
        max_iter=settings.LOGISTIC_MAX_ITER,
        class_weight="balanced",
        random_state=settings.RANDOM_STATE,
    )


MODEL_REGISTRY = {
    "svm": build_svm,
    "random_forest": build_random_forest,
    "logistic": build_logistic_regression,
}

# Hyperparameter search grids used by train.py when
# settings.ENABLE_HYPERPARAMETER_TUNING is True. Kept intentionally modest
# in size so a full grid search finishes in a reasonable time even on a
# laptop CPU with a dataset in the low thousands of images.
PARAM_GRIDS = {
    "svm": {
        "C": [0.5, 1.0, 2.0, 5.0],
        "kernel": ["rbf", "linear"],
    },
    "random_forest": {
        "n_estimators": [150, 300],
        "max_depth": [15, 25, None],
    },
    "logistic": {
        "C": [0.01, 0.1, 1.0, 10.0],
    },
}

# Which models get wrapped in CalibratedClassifierCV. Random Forest is
# deliberately excluded - averaging many trees' votes already tends to
# produce reasonably well-calibrated probabilities, unlike the linear
# decision functions of SVM and Logistic Regression, which can saturate
# toward 0/1 on inputs far from the training distribution.
CALIBRATED_MODEL_KEYS = {"svm", "logistic"}