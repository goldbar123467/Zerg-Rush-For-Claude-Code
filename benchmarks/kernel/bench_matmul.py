"""Minimal benchmark harness for matrix multiplication."""
import time
import statistics
from typing import Tuple, Dict, Any

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


def bench_matmul(shape: Tuple[int, int], warmup: int = 3, runs: int = 10) -> Dict[str, Any]:
    """Benchmark matmul for given shape. Returns timing stats.

    Args:
        shape: Tuple of (M, N) for square matrix multiplication (M x N) @ (N x M)
        warmup: Number of warmup runs to discard
        runs: Number of timed runs

    Returns:
        dict with keys: mean_ms, std_ms, shape
    """
    if not HAS_NUMPY:
        raise ImportError("numpy is required for matrix multiplication benchmarks")

    m, n = shape

    # Create random matrices
    a = np.random.randn(m, n).astype(np.float32)
    b = np.random.randn(n, m).astype(np.float32)

    # Warmup runs (discard)
    for _ in range(warmup):
        _ = np.matmul(a, b)

    # Timed runs
    timings_ms = []
    for _ in range(runs):
        start = time.perf_counter()
        _ = np.matmul(a, b)
        end = time.perf_counter()
        timings_ms.append((end - start) * 1000)

    # Calculate statistics
    mean_ms = statistics.mean(timings_ms)
    std_ms = statistics.stdev(timings_ms) if len(timings_ms) > 1 else 0.0

    result = {
        "mean_ms": mean_ms,
        "std_ms": std_ms,
        "shape": shape,
    }

    return result


def print_results(results: Dict[str, Any]) -> None:
    """Print benchmark results in a readable format."""
    print(f"Shape: {results['shape']}")
    print(f"  Mean: {results['mean_ms']:.4f} ms")
    print(f"  Std:  {results['std_ms']:.4f} ms")


if __name__ == "__main__":
    print("Matrix Multiplication Benchmark")
    print("=" * 40)

    # Benchmark for shape (256, 256)
    results = bench_matmul(shape=(256, 256))
    print_results(results)
