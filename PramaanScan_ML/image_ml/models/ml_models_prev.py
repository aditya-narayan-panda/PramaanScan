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

from config import get_settings

settings = get_settings()


def build_svm() -> SVC:
    """Support Vector Machine with probability estimates enabled so we can
    read out P(AI Generated) rather than just a hard label."""
    return SVC(
        kernel=settings.SVM_KERNEL,
        C=settings.SVM_C,
        probability=True,
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
