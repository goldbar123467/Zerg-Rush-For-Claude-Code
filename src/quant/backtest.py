"""
Simple backtest engine for single-asset, long-only strategies.

This module provides a minimal backtesting framework that takes price
and signal series and computes PnL from position changes.
"""

from dataclasses import dataclass
import numpy as np


@dataclass
class BacktestResult:
    """Results from a backtest run.

    Attributes:
        pnl: Cumulative profit/loss at each timestamp.
        positions: Position held at each timestamp (1 = long, 0 = flat).
        timestamps: Index array corresponding to the input data.
    """
    pnl: np.ndarray
    positions: np.ndarray
    timestamps: np.ndarray


def run_backtest(prices: np.ndarray, signals: np.ndarray) -> BacktestResult:
    """Run simple backtest. Single asset, long-only for now.

    Args:
        prices: Array of asset prices.
        signals: Array of trading signals. Signal > 0 means long,
                 signal <= 0 means flat (no position).

    Returns:
        BacktestResult containing PnL, positions, and timestamps.

    Raises:
        ValueError: If prices and signals have different lengths.

    Example:
        >>> prices = np.array([100, 101, 102, 100, 103])
        >>> signals = np.array([1, 1, 1, 0, 1])
        >>> result = run_backtest(prices, signals)
        >>> print(result.pnl[-1])  # Final PnL
    """
    prices = np.asarray(prices, dtype=np.float64)
    signals = np.asarray(signals, dtype=np.float64)

    if len(prices) != len(signals):
        raise ValueError(
            f"prices and signals must have same length, "
            f"got {len(prices)} and {len(signals)}"
        )

    n = len(prices)
    if n == 0:
        return BacktestResult(
            pnl=np.array([], dtype=np.float64),
            positions=np.array([], dtype=np.float64),
            timestamps=np.array([], dtype=np.int64),
        )

    # Compute positions: signal > 0 = long (1), signal <= 0 = flat (0)
    positions = (signals > 0).astype(np.float64)

    # Compute returns (price changes as percentage)
    returns = np.zeros(n, dtype=np.float64)
    returns[1:] = (prices[1:] - prices[:-1]) / prices[:-1]

    # PnL: position at t-1 determines if we capture return at t
    # (we need to be in position before the price move)
    position_returns = np.zeros(n, dtype=np.float64)
    position_returns[1:] = positions[:-1] * returns[1:]

    # Cumulative PnL (as percentage of initial capital)
    pnl = np.cumsum(position_returns)

    # Timestamps are just indices
    timestamps = np.arange(n, dtype=np.int64)

    return BacktestResult(
        pnl=pnl,
        positions=positions,
        timestamps=timestamps,
    )


if __name__ == "__main__":
    # Simple test
    test_prices = np.array([100.0, 101.0, 102.0, 100.0, 103.0])
    test_signals = np.array([1.0, 1.0, 1.0, 0.0, 1.0])
    result = run_backtest(test_prices, test_signals)
    print(f"Prices: {test_prices}")
    print(f"Signals: {test_signals}")
    print(f"Positions: {result.positions}")
    print(f"PnL: {result.pnl}")
    print(f"Final PnL: {result.pnl[-1]:.4f} ({result.pnl[-1]*100:.2f}%)")
