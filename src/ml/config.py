"""
ML Training Configuration Module.

Provides a dataclass-based configuration system for ML training
with YAML loading support and type validation.
"""

from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any, Dict, Optional, Type, TypeVar, get_type_hints
import yaml


T = TypeVar('T', bound='TrainConfig')


@dataclass
class TrainConfig:
    """Configuration for ML training runs.

    Attributes:
        batch_size: Number of samples per training batch.
        learning_rate: Learning rate for optimizer.
        max_epochs: Maximum number of training epochs.
        device: Device to use for training (cuda/cpu).
    """
    batch_size: int = 32
    learning_rate: float = 1e-4
    max_epochs: int = 100
    device: str = "cuda"

    def __post_init__(self) -> None:
        """Validate types after initialization."""
        self._validate_types()

    def _validate_types(self) -> None:
        """Validate that all fields have correct types."""
        hints = get_type_hints(self.__class__)
        for field_obj in fields(self):
            name = field_obj.name
            value = getattr(self, name)
            expected_type = hints.get(name)

            if expected_type is None:
                continue

            # Handle numeric type coercion (int/float)
            if expected_type == float and isinstance(value, int):
                setattr(self, name, float(value))
                continue

            if not isinstance(value, expected_type):
                raise TypeError(
                    f"Field '{name}' expected {expected_type.__name__}, "
                    f"got {type(value).__name__}"
                )

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create config from dictionary.

        Args:
            data: Dictionary with config values.

        Returns:
            TrainConfig instance.
        """
        valid_fields = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)


def load_config(path: Optional[str] = None) -> TrainConfig:
    """Load config from YAML or use defaults.

    Args:
        path: Optional path to YAML config file.

    Returns:
        TrainConfig instance with loaded or default values.

    Raises:
        FileNotFoundError: If path is provided but file doesn't exist.
        yaml.YAMLError: If YAML parsing fails.
        TypeError: If config values have incorrect types.
    """
    if path is None:
        return TrainConfig()

    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(config_path, 'r') as f:
        data = yaml.safe_load(f) or {}

    return TrainConfig.from_dict(data)
