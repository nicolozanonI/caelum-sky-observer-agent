import numpy as np

def clean_numpy_types(obj):
    if isinstance(obj, dict):
        return {k: clean_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_numpy_types(v) for v in obj]
    elif isinstance(obj, np.generic):  # Cattura tutti i tipi numpy (np.bool_, np.float64, ecc.)
        return obj.item()
    return obj