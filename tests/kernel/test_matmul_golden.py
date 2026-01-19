"""Golden test vectors and tolerance policy for matmul kernel."""
import pytest
import numpy as np

# Tolerance policy for floating-point comparison
TOLERANCE = {"atol": 1e-5, "rtol": 1e-5}

# Import the reference matmul implementation (depends on K001's reference.py)
try:
    from src.kernel.reference import matmul_reference
    HAS_REFERENCE = True
except ImportError:
    HAS_REFERENCE = False
    matmul_reference = None


def numpy_matmul(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """NumPy reference for comparison."""
    return np.matmul(a, b)


@pytest.fixture
def identity_matrices():
    """Identity matrix test case."""
    eye = np.eye(4, dtype=np.float32)
    return eye, eye, eye  # A, B, expected


@pytest.fixture
def zero_matrices():
    """Zero matrix test case."""
    zeros = np.zeros((4, 4), dtype=np.float32)
    return zeros, zeros, zeros


@pytest.fixture
def ones_matrices():
    """Ones matrix test case."""
    ones = np.ones((4, 4), dtype=np.float32)
    expected = np.full((4, 4), 4, dtype=np.float32)
    return ones, ones, expected


@pytest.fixture
def random_small_matrices():
    """Small random matrix for reproducible testing."""
    np.random.seed(42)
    a = np.random.randn(8, 8).astype(np.float32)
    b = np.random.randn(8, 8).astype(np.float32)
    return a, b, numpy_matmul(a, b)


@pytest.mark.skipif(not HAS_REFERENCE, reason="reference.py not available yet")
def test_matmul_golden_identity(identity_matrices):
    """Test matmul with identity matrices."""
    a, b, expected = identity_matrices
    result = matmul_reference(a, b)
    assert np.allclose(result, expected, **TOLERANCE), \
        f"Identity failed. Max diff: {np.max(np.abs(result - expected))}"


@pytest.mark.skipif(not HAS_REFERENCE, reason="reference.py not available yet")
def test_matmul_golden_zeros(zero_matrices):
    """Test matmul with zero matrices."""
    a, b, expected = zero_matrices
    result = matmul_reference(a, b)
    assert np.allclose(result, expected, **TOLERANCE), \
        f"Zeros failed. Max value: {np.max(np.abs(result))}"


@pytest.mark.skipif(not HAS_REFERENCE, reason="reference.py not available yet")
def test_matmul_golden_ones(ones_matrices):
    """Test matmul with ones matrices."""
    a, b, expected = ones_matrices
    result = matmul_reference(a, b)
    assert np.allclose(result, expected, **TOLERANCE), \
        f"Ones failed. Max diff: {np.max(np.abs(result - expected))}"


@pytest.mark.skipif(not HAS_REFERENCE, reason="reference.py not available yet")
def test_matmul_golden_small(random_small_matrices):
    """Test matmul against golden vectors with random small matrices."""
    a, b, expected = random_small_matrices
    result = matmul_reference(a, b)
    assert np.allclose(result, expected, **TOLERANCE), \
        f"Random small failed. Max diff: {np.max(np.abs(result - expected))}"
