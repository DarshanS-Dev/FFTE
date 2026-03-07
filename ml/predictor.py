"""
ml/predictor.py
---------------
Loads the trained XGBoost model and label encoders at import time and
exposes a single public function: predict_failure_probability().
"""

import logging
from pathlib import Path

import joblib

logger = logging.getLogger("ffte.ml.predictor")

# ---------------------------------------------------------------------------
# Module-level model / encoder loading
# ---------------------------------------------------------------------------
_ML_DIR = Path(__file__).parent

def _load(filename: str):
    """Load a joblib artifact, returning None on failure."""
    path = _ML_DIR / filename
    try:
        return joblib.load(path)
    except FileNotFoundError:
        logger.warning("ML artifact not found: %s – predictions will use fallback value", path)
        return None
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to load ML artifact %s: %s – predictions will use fallback value", path, exc)
        return None


model = _load("ffte_model.pkl")
le_field_type = _load("label_encoder_field_type.pkl")
le_edge_case = _load("label_encoder_edge_case.pkl")
le_http_method = _load("label_encoder_http_method.pkl")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def predict_failure_probability(
    http_method: str,
    field_type: str | None,
    edge_case_type: str | None,
    is_required: bool | None,
    field_name: str | None,
) -> float:
    """Return the predicted probability (0.0–1.0) that a test case causes
    a failure, as estimated by the trained XGBoost model.

    Falls back to 0.5 (neutral) when the model is unavailable or any
    unexpected error occurs during inference.

    Args:
        http_method:    HTTP verb (e.g. "GET", "POST").
        field_type:     OpenAPI field type string (e.g. "string", "integer"),
                        or None if unknown.
        edge_case_type: Edge-case category label produced by the fuzzer,
                        or None for baseline requests.
        is_required:    Whether the field is marked required in the schema,
                        or None if not applicable.
        field_name:     The raw field / parameter name from the schema,
                        used to derive semantic binary flags.

    Returns:
        A float in [0.0, 1.0] representing the failure probability.
    """
    if model is None:
        return 0.5

    try:
        # --- Encode categorical features, falling back to 0 for unseen labels ---
        def _encode(encoder, value):
            if encoder is None or value is None:
                return 0
            try:
                return int(encoder.transform([value])[0])
            except Exception:  # noqa: BLE001
                return 0

        http_method_enc = _encode(le_http_method, http_method)
        field_type_enc  = _encode(le_field_type,  field_type)
        edge_case_enc   = _encode(le_edge_case,   edge_case_type)

        # --- Boolean flag ---
        is_required_int = int(bool(is_required)) if is_required is not None else 0

        # --- Semantic field-name flags ---
        name_lower   = field_name.lower() if field_name else ""
        has_id       = 1 if field_name and "id"       in name_lower else 0
        has_email    = 1 if field_name and "email"    in name_lower else 0
        has_password = 1 if field_name and ("password" in name_lower or "pass" in name_lower) else 0
        has_user     = 1 if field_name and "user"     in name_lower else 0
        has_name     = 1 if field_name and "name"     in name_lower else 0

        # --- Feature vector (order must match training) ---
        import numpy as np  # local import to keep module-load fast if numpy absent
        features = np.array([[
            http_method_enc,
            field_type_enc,
            edge_case_enc,
            is_required_int,
            has_id,
            has_email,
            has_password,
            has_user,
            has_name,
        ]])

        probability: float = float(model.predict_proba(features)[0][1])
        return probability

    except Exception as exc:  # noqa: BLE001
        logger.warning("predict_failure_probability encountered an error: %s – returning 0.5", exc)
        return 0.5
