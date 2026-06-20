"""
morpheus/config.py — Configuration management for Morpheus.

Loads config from (in priority order):
  1. CLI flags (highest)
  2. Environment variables
  3. Config file: ~/.morpheus/config.json
  4. Defaults (lowest)
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


CONFIG_DIR = Path.home() / ".morpheus"
CONFIG_PATH = CONFIG_DIR / "config.json"


@dataclass
class MorpheusConfig:
    """Complete configuration for Morpheus with defaults."""

    # LLM
    llm_backend: str = "ollama,openrouter"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "mistral"
    openrouter_api_key: str = ""
    openrouter_model: str = "mistralai/mistral-7b-instruct"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    llm_timeout: float = 120.0

    # Storage
    db_path: str = "~/.morpheus/history.db"

    # Dashboard
    dashboard_port: int = 4000

    # Behavior
    no_color: bool = False
    verbose: bool = False

    # Raw loaded data (for saving back)
    _raw: dict[str, Any] = field(default_factory=dict)


def load_config() -> MorpheusConfig:
    """
    Load configuration from all sources. Returns a merged MorpheusConfig.

    Priority: CLI > env > config file > defaults
    """
    cfg = MorpheusConfig()

    # Step 1: defaults (already set in dataclass)

    # Step 2: config file
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH) as f:
                file_data = json.load(f)
            cfg._raw = file_data
            _apply_dict(cfg, file_data)
        except (json.JSONDecodeError, OSError):
            pass

    # Step 3: environment variables
    _apply_env(cfg)

    return cfg


def save_config(cfg: MorpheusConfig) -> None:
    """Save configuration to ~/.morpheus/config.json."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    data = {
        "llm_backend": cfg.llm_backend,
        "ollama_url": cfg.ollama_url,
        "ollama_model": cfg.ollama_model,
        "openrouter_api_key": cfg.openrouter_api_key,
        "openrouter_model": cfg.openrouter_model,
        "openrouter_base_url": cfg.openrouter_base_url,
        "llm_timeout": cfg.llm_timeout,
        "db_path": cfg.db_path,
        "dashboard_port": cfg.dashboard_port,
        "no_color": cfg.no_color,
        "verbose": cfg.verbose,
    }
    CONFIG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def format_config(cfg: MorpheusConfig) -> str:
    """Pretty-print the config for display."""
    lines = [
        "Morpheus Configuration",
        "======================",
        "",
        "LLM Backend:",
        f"  Backend priority:  {cfg.llm_backend}",
        f"  Ollama URL:        {cfg.ollama_url}",
        f"  Ollama model:      {cfg.ollama_model}",
        f"  OpenRouter model:  {cfg.openrouter_model}",
        f"  OpenRouter URL:    {cfg.openrouter_base_url}",
        f"  LLM timeout:       {cfg.llm_timeout}s",
        "",
        "Storage:",
        f"  Database path:     {cfg.db_path}",
        "",
        "Dashboard:",
        f"  Port:              {cfg.dashboard_port}",
        "",
        "Behavior:",
        f"  Verbose:           {cfg.verbose}",
        f"  No color:          {cfg.no_color}",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
#  Internal helpers
# ---------------------------------------------------------------------------

_ENV_MAP: dict[str, str] = {
    "llm_backend": "MORPHEUS_LLM_BACKEND",
    "ollama_url": "MORPHEUS_OLLAMA_URL",
    "ollama_model": "MORPHEUS_OLLAMA_MODEL",
    "openrouter_api_key": "OPENROUTER_API_KEY",
    "openrouter_model": "OPENROUTER_MODEL",
    "openrouter_base_url": "OPENROUTER_BASE_URL",
    "llm_timeout": "MORPHEUS_LLM_TIMEOUT",
    "db_path": "MORPHEUS_DB_PATH",
    "dashboard_port": "MORPHEUS_DASHBOARD_PORT",
    "no_color": "MORPHEUS_NO_COLOR",
    "verbose": "MORPHEUS_VERBOSE",
}


def _apply_env(cfg: MorpheusConfig) -> None:
    for field_name, env_var in _ENV_MAP.items():
        val = os.getenv(env_var)
        if val is not None:
            current = getattr(cfg, field_name)
            if isinstance(current, bool):
                setattr(cfg, field_name, val.lower() in ("1", "true", "yes"))
            elif isinstance(current, int):
                try:
                    setattr(cfg, field_name, int(val))
                except (ValueError, TypeError):
                    pass
            elif isinstance(current, float):
                try:
                    setattr(cfg, field_name, float(val))
                except (ValueError, TypeError):
                    pass
            else:
                setattr(cfg, field_name, val)


def _apply_dict(cfg: MorpheusConfig, data: dict[str, Any]) -> None:
    for key, val in data.items():
        if hasattr(cfg, key) and val is not None:
            current = getattr(cfg, key)
            if isinstance(current, bool):
                setattr(cfg, key, bool(val))
            elif isinstance(current, int):
                try:
                    setattr(cfg, key, int(val))
                except (ValueError, TypeError):
                    pass
            elif isinstance(current, float):
                try:
                    setattr(cfg, key, float(val))
                except (ValueError, TypeError):
                    pass
            else:
                setattr(cfg, key, val)
