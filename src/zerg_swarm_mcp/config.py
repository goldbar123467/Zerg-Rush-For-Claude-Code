"""Configuration settings for the Zerg Swarm MCP Server."""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Server configuration with environment variable support."""

    model_config = SettingsConfigDict(env_prefix="ZERG_")

    swarm_root: Path = Path("/home/ubuntu/projects/zerg-swarm/SWARM")
    host: str = "127.0.0.1"
    port: int = 8766


settings = Settings()
