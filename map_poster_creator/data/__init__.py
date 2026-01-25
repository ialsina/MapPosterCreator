"""Data models package."""

# Lazy import from data.py to maintain backward compatibility
# This allows "from map_poster_creator.data import get_city_df" to work
def __getattr__(name):
    """Lazily import attributes from the parent data.py module."""
    import importlib.util
    import sys
    from pathlib import Path
    
    # Load data.py as a separate module to avoid circular imports
    _module_name = 'map_poster_creator._data_functions'
    if _module_name not in sys.modules:
        _data_py_path = Path(__file__).parent.parent / 'data.py'
        _spec = importlib.util.spec_from_file_location(_module_name, _data_py_path)
        _data_module = importlib.util.module_from_spec(_spec)
        sys.modules[_module_name] = _data_module
        _spec.loader.exec_module(_data_module)
    
    _data_module = sys.modules[_module_name]
    if hasattr(_data_module, name):
        return getattr(_data_module, name)
    raise AttributeError(f"module 'map_poster_creator.data' has no attribute '{name}'")
