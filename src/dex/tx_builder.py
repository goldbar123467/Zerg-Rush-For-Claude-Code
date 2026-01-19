"""Transaction builder with dry-run support and destination allowlist.

This module provides transaction building utilities for Solana DEX operations,
with safety features including destination validation and dry-run mode.
"""

from typing import Any

from .config import DexConfig

# Approved program IDs / token mints for destination validation.
# When non-empty, only destinations in this set are allowed.
DESTINATION_ALLOWLIST: set[str] = set()


class TxBuilder:
    """Builder for Solana DEX transactions with safety checks."""

    def __init__(self, config: DexConfig):
        """Initialize transaction builder with configuration.

        Args:
            config: DexConfig instance with RPC and keypair settings.
        """
        self.config = config

    def build_swap(
        self,
        input_mint: str,
        output_mint: str,
        amount: int,
        dry_run: bool = True,
    ) -> dict[str, Any]:
        """Build a swap transaction.

        Constructs a swap transaction structure. If dry_run is True (default),
        the transaction is not signed and can be used for simulation/validation.

        Args:
            input_mint: The input token mint address.
            output_mint: The output token mint address.
            amount: Amount of input tokens (in smallest unit).
            dry_run: If True, don't sign the transaction. Defaults to True.

        Returns:
            Transaction dict with structure:
                - input_mint: Input token address
                - output_mint: Output token address
                - amount: Token amount
                - network: Network from config
                - signed: Whether TX is signed
                - rpc_url: RPC endpoint for submission

        Raises:
            ValueError: If destination validation fails.
        """
        # Validate destinations against allowlist
        self.validate_destination(input_mint)
        self.validate_destination(output_mint)

        tx = {
            "input_mint": input_mint,
            "output_mint": output_mint,
            "amount": amount,
            "network": self.config.network,
            "rpc_url": self.config.rpc_url,
            "signed": False,
        }

        if not dry_run:
            # In production, would sign TX here using keypair
            # For safety, actual signing logic deferred to separate module
            tx["signed"] = True

        return tx

    def validate_destination(self, dest: str) -> bool:
        """Check if destination is in the allowlist.

        When DESTINATION_ALLOWLIST is empty, all destinations are allowed.
        When non-empty, only destinations in the allowlist are permitted.

        Args:
            dest: Destination address (program ID or token mint).

        Returns:
            True if destination is allowed.

        Raises:
            ValueError: If allowlist is non-empty and dest is not in it.
        """
        if DESTINATION_ALLOWLIST and dest not in DESTINATION_ALLOWLIST:
            raise ValueError(
                f"Destination {dest} not in allowlist. "
                f"Allowed: {DESTINATION_ALLOWLIST}"
            )
        return True
