def get_backend():
    """
    Returns the backend used for data handling.
    """
    try:
        import polars  # NOQA: F401 # type: ignore[import]

        return "polars"
    except ImportError:
        pass

    try:
        import pandas  # NOQA: F401 # type: ignore[import]

        return "pandas"
    except ImportError:
        pass

    try:
        import modin  # NOQA: F401 # type: ignore[import]

        return "modin"
    except ImportError:
        pass

    try:
        import pyarrow  # NOQA: F401 # type: ignore[import]

        return "pyarrow"
    except ImportError:
        pass

    raise ImportError("No suitable backend found. Please install pandas, polars, pyarrow or modin.")


BACKEND = get_backend()
