"""Solana DEX configuration and keypair loading utilities."""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class DexConfig:
    """Configuration for Solana DEX operations."""
    rpc_url: str
    keypair_path: str
    network: str = "mainnet"  # mainnet, devnet

    def __post_init__(self):
        if self.network not in ("mainnet", "devnet"):
            raise ValueError(f"Invalid network: {self.network}. Must be 'mainnet' or 'devnet'")


def load_dex_config(path: Optional[str] = None) -> DexConfig:
    """Load DEX config from YAML file or environment variables.

    Priority: YAML file > env vars (RPC_URL, KEYPAIR_PATH, NETWORK).
    Raises ValueError if required fields missing, FileNotFoundError if files don't exist.
    """
    config_data = {}
    if path:
        config_path = Path(path)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        with open(config_path, "r") as f:
            config_data = yaml.safe_load(f) or {}

    rpc_url = config_data.get("rpc_url") or os.environ.get("RPC_URL")
    keypair_path = config_data.get("keypair_path") or os.environ.get("KEYPAIR_PATH")
    network = config_data.get("network") or os.environ.get("NETWORK", "mainnet")

    if not rpc_url:
        raise ValueError("RPC_URL is required (via config file or environment variable)")
    if not keypair_path:
        raise ValueError("KEYPAIR_PATH is required (via config file or environment variable)")
    if not Path(keypair_path).exists():
        raise FileNotFoundError(f"Keypair file not found: {keypair_path}")

    return DexConfig(rpc_url=rpc_url, keypair_path=keypair_path, network=network)


def load_keypair(path: str) -> bytes:
    """Load Solana keypair from JSON file. Returns 64-byte secret.

    Expects JSON array of 64 integers (standard Solana CLI format).
    Never logs or prints the secret key.
    """
    keypair_path = Path(path)
    if not keypair_path.exists():
        raise FileNotFoundError(f"Keypair file not found: {path}")

    with open(keypair_path, "r") as f:
        try:
            key_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in keypair file: {e}")

    if not isinstance(key_data, list):
        raise ValueError("Keypair file must contain a JSON array of integers")
    if len(key_data) != 64:
        raise ValueError(f"Keypair must be 64 bytes, got {len(key_data)}")

    for i, val in enumerate(key_data):
        if not isinstance(val, int) or val < 0 or val > 255:
            raise ValueError(f"Invalid byte value at index {i}: {val}")

    return bytes(key_data)  # Never log secret key
