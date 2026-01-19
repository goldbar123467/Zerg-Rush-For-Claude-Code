"""CPU reference implementations for kernel operations.

This module provides pure NumPy reference implementations for testing
and validation of GPU kernels. These are not optimized for performance
but for correctness and clarity.
"""

import numpy as np


def matmul_cpu_ref(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """CPU reference for matmul. Small shapes only (<=512x512).

    Performs matrix multiplication using NumPy as a reference implementation
    for validating GPU kernel outputs.

    Parameters
    ----------
    a : np.ndarray
        Left matrix, shape (M, K), dtype float32
    b : np.ndarray
        Right matrix, shape (K, N), dtype float32

    Returns
    -------
    np.ndarray
        Result matrix, shape (M, N), dtype float32

    Raises
    ------
    AssertionError
        If inputs are not 2D, not float32, shapes incompatible,
        or dimensions exceed 512.

    Examples
    --------
    >>> import numpy as np
    >>> a = np.array([[1, 2], [3, 4]], dtype=np.float32)
    >>> b = np.array([[5, 6], [7, 8]], dtype=np.float32)
    >>> matmul_cpu_ref(a, b)
    array([[19., 22.],
           [43., 50.]], dtype=float32)
    """
    # Validate input types
    assert isinstance(a, np.ndarray), f"a must be np.ndarray, got {type(a)}"
    assert isinstance(b, np.ndarray), f"b must be np.ndarray, got {type(b)}"

    # Validate dimensions
    assert a.ndim == 2, f"a must be 2D, got {a.ndim}D"
    assert b.ndim == 2, f"b must be 2D, got {b.ndim}D"

    # Validate dtypes
    assert a.dtype == np.float32, f"a must be float32, got {a.dtype}"
    assert b.dtype == np.float32, f"b must be float32, got {b.dtype}"

    # Validate shape compatibility for matrix multiplication
    m, k1 = a.shape
    k2, n = b.shape
    assert k1 == k2, f"Inner dimensions must match: a.shape[1]={k1} != b.shape[0]={k2}"

    # Validate size constraints (small shapes only)
    max_dim = 512
    assert m <= max_dim, f"a.shape[0]={m} exceeds maximum dimension {max_dim}"
    assert k1 <= max_dim, f"a.shape[1]={k1} exceeds maximum dimension {max_dim}"
    assert n <= max_dim, f"b.shape[1]={n} exceeds maximum dimension {max_dim}"

    # Perform matrix multiplication using NumPy
    result = np.matmul(a, b)

    # Ensure output dtype is float32
    return result.astype(np.float32, copy=False)
