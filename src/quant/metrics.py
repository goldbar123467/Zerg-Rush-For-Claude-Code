"""Quantitative metrics for portfolio and strategy analysis."""

import numpy as np


def sharpe_ratio(returns: np.ndarray, risk_free: float = 0.0) -> float:
    """Annualized Sharpe ratio.

    Args:
        returns: Array of daily returns (decimals, e.g., 0.01 for 1%).
        risk_free: Daily risk-free rate (default 0.0).

    Returns:
        Annualized Sharpe ratio. Returns 0.0 if std is zero.
        Assumes 252 trading days per year.
    """
    excess_returns = returns - risk_free
    mean_excess = np.mean(excess_returns)
    std_excess = np.std(excess_returns, ddof=1)

    if std_excess == 0:
        return 0.0

    daily_sharpe = mean_excess / std_excess
    annualized_sharpe = daily_sharpe * np.sqrt(252)

    return float(annualized_sharpe)


def max_drawdown(equity_curve: np.ndarray) -> float:
    """Maximum drawdown as positive fraction.

    Args:
        equity_curve: Array of equity values over time.

    Returns:
        Maximum drawdown as fraction (e.g., 0.15 for 15%).
        Measured as peak-to-trough decline divided by peak.
    """
    if len(equity_curve) == 0:
        return 0.0

    # Running maximum (peak values up to each point)
    running_max = np.maximum.accumulate(equity_curve)

    # Drawdown at each point
    drawdowns = (running_max - equity_curve) / running_max

    # Handle division by zero if running_max contains zeros
    drawdowns = np.nan_to_num(drawdowns, nan=0.0, posinf=0.0, neginf=0.0)

    return float(np.max(drawdowns))


def turnover(positions: np.ndarray) -> float:
    """Average daily turnover.

    Args:
        positions: Position values over time. 1D (single asset) or 2D
            (shape [time, assets]).

    Returns:
        Mean absolute position change. Returns 0.0 if < 2 time points.
        For multi-asset, changes are summed across assets before averaging.
    """
    positions = np.atleast_2d(positions)

    # Ensure shape is [time, assets]
    if positions.shape[0] < positions.shape[1]:
        positions = positions.T

    if positions.shape[0] < 2:
        return 0.0

    # Daily position changes
    position_changes = np.diff(positions, axis=0)

    # Sum absolute changes across assets, then take mean across time
    daily_turnover = np.sum(np.abs(position_changes), axis=1)

    return float(np.mean(daily_turnover))
