"""Sanity check functions for quantitative data validation."""

import warnings
import numpy as np


def check_no_nans(arr: np.ndarray, name: str = "array") -> None:
    """Raise if any NaNs present."""
    nan_mask = np.isnan(arr)
    if np.any(nan_mask):
        nan_indices = np.where(nan_mask)
        if arr.ndim == 1:
            locations = nan_indices[0].tolist()
        else:
            locations = list(zip(*[idx.tolist() for idx in nan_indices]))
        raise ValueError(
            f"NaN values found in '{name}' at indices: {locations[:10]}"
            + (f" (and {len(locations) - 10} more)" if len(locations) > 10 else "")
        )


def check_no_lookahead(signal_idx: np.ndarray, data_idx: np.ndarray) -> None:
    """Raise if signal timestamps precede data timestamps."""
    signal_idx = np.asarray(signal_idx)
    data_idx = np.asarray(data_idx)

    if signal_idx.shape != data_idx.shape:
        raise ValueError(
            f"Shape mismatch: signal_idx {signal_idx.shape} vs data_idx {data_idx.shape}"
        )

    violations = signal_idx < data_idx
    if np.any(violations):
        violation_indices = np.where(violations)[0]
        examples = violation_indices[:5].tolist()
        raise ValueError(
            f"Lookahead detected: signal generated before data at indices {examples}"
            + (f" (and {len(violation_indices) - 5} more)" if len(violation_indices) > 5 else "")
        )


def check_no_future_leakage(signal: np.ndarray, prices: np.ndarray) -> None:
    """Basic leakage check: signal should not correlate perfectly with future."""
    signal = np.asarray(signal)
    prices = np.asarray(prices)

    if signal.shape != prices.shape:
        raise ValueError(
            f"Shape mismatch: signal {signal.shape} vs prices {prices.shape}"
        )

    if len(signal) < 3:
        return  # Not enough data

    # Calculate future returns and align signal
    future_returns = np.diff(prices)
    signal_aligned = signal[:-1]

    # Remove NaNs for correlation
    valid_mask = ~(np.isnan(signal_aligned) | np.isnan(future_returns))
    if np.sum(valid_mask) < 2:
        return

    signal_clean = signal_aligned[valid_mask]
    returns_clean = future_returns[valid_mask]

    # Skip if zero variance
    if np.std(signal_clean) == 0 or np.std(returns_clean) == 0:
        return

    correlation = np.corrcoef(signal_clean, returns_clean)[0, 1]

    if abs(correlation) > 0.99:
        warnings.warn(
            f"Potential future leakage detected: signal-future correlation = {correlation:.4f}",
            UserWarning
        )
