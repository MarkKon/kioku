"""Where the model lives and what it may use.

Each setting comes from the environment first, then from `config.toml` in the
model folder:

  READER_HOME          the model folder (default ~/.local/share/reader)
  READER_VAULT         vault = "…"        a folder of markdown notes (optional)
  READER_SCOUT_MODEL   scout_model = "…"  a pi model for drafting (optional)
  READER_TODAY         fixes the clock, for tests: a date (read as noon) or a
                       date and time, e.g. 2026-11-02T09:30
"""

from __future__ import annotations

import datetime as dt
import os
import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    home: Path
    vault: Path | None
    scout_model: str | None
    now: dt.datetime
    cache: Path

    @property
    def today(self) -> dt.date:
        return self.now.date()


def load() -> Config:
    home = Path(os.environ.get("READER_HOME") or Path.home() / ".local/share/reader")
    try:
        file = tomllib.loads((home / "config.toml").read_text())
    except FileNotFoundError:
        file = {}
    vault = os.environ.get("READER_VAULT") or file.get("vault")
    fixed = os.environ.get("READER_TODAY")
    cache = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "reader"
    return Config(
        home=home,
        vault=Path(vault).expanduser() if vault else None,
        scout_model=os.environ.get("READER_SCOUT_MODEL") or file.get("scout_model"),
        now=_moment(fixed) if fixed else dt.datetime.now().replace(microsecond=0),
        cache=cache,
    )


def _moment(s: str) -> dt.datetime:
    return dt.datetime.fromisoformat(s if "T" in s else s + "T12:00")
