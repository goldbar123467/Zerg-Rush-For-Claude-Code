"""Kernel implementations for GPU and CPU operations."""

from .reference import matmul_cpu_ref

__all__ = ["matmul_cpu_ref"]
