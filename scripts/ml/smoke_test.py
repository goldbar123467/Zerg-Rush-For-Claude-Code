#!/usr/bin/env python3
"""Smoke test for ML pipeline - runs 1 batch through model."""
import sys
import json
from pathlib import Path

try:
    import torch
    import torch.nn as nn
except ImportError:
    print("ERROR: PyTorch not installed. Run: pip install torch")
    sys.exit(1)


def load_config(config_path: str = None) -> dict:
    """Load configuration from file or return defaults."""
    defaults = {"batch_size": 4, "input_dim": 128, "hidden_dim": 64, "output_dim": 10, "device": "cpu"}
    if config_path is None:
        return defaults
    path = Path(config_path)
    if not path.exists():
        print(f"WARNING: Config {config_path} not found, using defaults")
        return defaults
    try:
        with open(path, "r") as f:
            return {**defaults, **json.load(f)}
    except Exception as e:
        print(f"WARNING: Failed to load config: {e}, using defaults")
        return defaults


class SimpleModel(nn.Module):
    """Simple feedforward model for smoke testing."""
    def __init__(self, input_dim: int, hidden_dim: int, output_dim: int):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, output_dim)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.layers(x)


def smoke_test(config_path: str = None) -> bool:
    """Run 1 batch through model. Returns True if passes."""
    try:
        config = load_config(config_path)
        print(f"Config: {config}")
        device = torch.device(config["device"])
        print(f"Using device: {device}")

        model = SimpleModel(config["input_dim"], config["hidden_dim"], config["output_dim"]).to(device)
        model.eval()
        print(f"Model: {type(model).__name__}")

        # Create dummy batch (random tensor)
        batch = torch.randn(config["batch_size"], config["input_dim"], device=device)
        print(f"Input shape: {batch.shape}")

        # Forward pass only (no backward)
        with torch.no_grad():
            output = model(batch)

        print(f"Output shape: {output.shape}")
        expected = (config["batch_size"], config["output_dim"])
        if output.shape != torch.Size(expected):
            print(f"ERROR: Expected shape {expected}, got {output.shape}")
            return False

        print("SMOKE TEST PASSED")
        return True
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = smoke_test(sys.argv[1] if len(sys.argv) > 1 else None)
    sys.exit(0 if success else 1)
