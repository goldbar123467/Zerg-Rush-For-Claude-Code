"""DEX operation guardrails for slippage and trade size limits.

This module provides safety checks and logging for DEX trading operations.
All limits are hardcoded as module constants for security.
"""

import logging

# Configure module logger
logger = logging.getLogger(__name__)

# Hardcoded safety limits
MAX_SLIPPAGE_BPS = 100  # 1% maximum slippage (100 basis points)
MAX_TRADE_SIZE_USD = 1000  # Maximum trade size in USD


def check_slippage(slippage_bps: int) -> None:
    """Raise if slippage exceeds MAX_SLIPPAGE_BPS.

    Args:
        slippage_bps: Slippage tolerance in basis points (1 bps = 0.01%).

    Raises:
        ValueError: If slippage_bps exceeds the maximum allowed slippage.
    """
    if slippage_bps > MAX_SLIPPAGE_BPS:
        raise ValueError(
            f"Slippage {slippage_bps} bps exceeds maximum allowed "
            f"{MAX_SLIPPAGE_BPS} bps (1%)"
        )


def check_trade_size(amount_usd: float) -> None:
    """Raise if trade size exceeds MAX_TRADE_SIZE_USD.

    Args:
        amount_usd: Trade size in USD.

    Raises:
        ValueError: If amount_usd exceeds the maximum allowed trade size.
    """
    if amount_usd > MAX_TRADE_SIZE_USD:
        raise ValueError(
            f"Trade size ${amount_usd:.2f} exceeds maximum allowed "
            f"${MAX_TRADE_SIZE_USD}"
        )


def log_trade_attempt(
    input_mint: str, output_mint: str, amount: int, slippage: int
) -> None:
    """Log trade attempt (never log secrets).

    Logs a structured message about the trade attempt at INFO level.
    Only logs public trade parameters - never logs private keys or secrets.

    Args:
        input_mint: The input token mint address.
        output_mint: The output token mint address.
        amount: The amount of input tokens (in smallest unit).
        slippage: Slippage tolerance in basis points.
    """
    logger.info(
        "Trade attempt: input_mint=%s output_mint=%s amount=%d slippage_bps=%d",
        input_mint,
        output_mint,
        amount,
        slippage,
    )
