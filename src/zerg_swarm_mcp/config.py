"""Configuration settings for the Zerg Swarm MCP Server."""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Server configuration with environment variable support."""

    model_config = SettingsConfigDict(env_prefix="ZERG_")

    swarm_root: Path = Path("/home/ubuntu/projects/zerg-swarm/SWARM")
    host: str = "127.0.0.1"
    port: int = 8767

    # Flavor text settings
    verbose: bool = True  # Enable flavor text output
    serious_mode: bool = False  # Disable all flavor text (for demos/investors)


settings = Settings()


def init_flavor_config() -> None:
    """Initialize flavor text system from settings."""
    from . import flavor
    flavor.configure(verbose=settings.verbose, serious_mode=settings.serious_mode)
