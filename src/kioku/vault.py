"""An optional vault: a folder of markdown notes the learner wrote. Read, never written.

Notes live in `<vault>/notes/*.md`, with YAML frontmatter. A note's title is
its first alias (or its first heading, or its file name); `status: developed`
marks a finished note, and `type: daily` or `type: person` notes are skipped.
Vault notes are hints for agents, never evidence.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .text import matches, norm


@dataclass(frozen=True)
class Note:
    id: str
    title: str
    aliases: tuple[str, ...]
    type: str
    status: str
    created: str
    path: Path


class Vault:
    def __init__(self, root: Path, cache: Path):
        self.root = root
        self.cache = cache
        self._notes: dict[str, Note] | None = None

    def notes(self) -> dict[str, Note]:
        if self._notes is None:
            self._notes = {}
            for f in sorted((self.root / "notes").glob("*.md")):
                try:
                    note = _read_note(f)
                except OSError:
                    continue
                self._notes[note.id] = note
        return self._notes

    def __contains__(self, nid: str) -> bool:
        return nid in self.notes()

    def matching(self, terms: list[str], skip: set[str], limit: int = 12) -> list[Note]:
        """Notes whose title or aliases match a term, finished notes first."""
        out = [n for n in self.notes().values()
               if n.id not in skip and n.type not in ("daily", "person")
               and any(matches(t, norm(" ".join([n.title, *n.aliases]))) for t in terms)]
        rank = {"developed": 0, "wip": 1, "stub": 2}
        out.sort(key=lambda n: (rank.get(n.status, 3), n.title))
        return out[:limit]

    def developed_date(self, nid: str) -> dt.date | None:
        """When the note first reached `status: developed`, from git when it can."""
        note = self.notes().get(nid)
        if not note or note.status != "developed":
            return None
        cache_file = self.cache / "developed.json"
        try:
            cache = json.loads(cache_file.read_text())
        except (OSError, ValueError):
            cache = {}
        mtime = int(note.path.stat().st_mtime)
        hit = cache.get(nid)
        if hit and hit[0] == mtime:
            return dt.date.fromisoformat(hit[1])
        day = None
        if shutil.which("git") and (self.root / ".git").exists():
            out = subprocess.run(
                ["git", "-C", str(self.root), "log", "--reverse", "--format=%as",
                 "-S", "status: developed", "--", f"notes/{nid}.md"],
                capture_output=True, text=True).stdout.split()
            day = out[0] if out else None
        if not day:
            day = note.created if re.fullmatch(r"\d{4}-\d{2}-\d{2}", note.created) \
                else dt.date.fromtimestamp(mtime).isoformat()
        cache[nid] = [mtime, day]
        self.cache.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps(cache))
        return dt.date.fromisoformat(day)


def _read_note(f: Path) -> Note:
    fm, body = _frontmatter(f.read_text(errors="replace"))
    aliases = tuple(fm["aliases"]) if isinstance(fm.get("aliases"), list) else ()
    heading = next((m.group(1).strip() for m in re.finditer(r"^# (.+)$", body, re.M)), None)
    title = next((a for a in aliases if a and a != f.stem), None) or heading or f.stem
    return Note(f.stem, title, aliases, str(fm.get("type") or ""),
                str(fm.get("status") or ""), str(fm.get("created") or ""), f)


def _frontmatter(text: str) -> tuple[dict, str]:
    """A small YAML subset: `key: value`, `key: [a, b]` and `- item` lists."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end < 0:
        return {}, text
    fm: dict = {}
    key = None
    for line in text[3:end].splitlines():
        if re.match(r"^\s+-\s", line) and key:
            if isinstance(fm.setdefault(key, []), list):
                fm[key].append(line.split("-", 1)[1].strip().strip("\"'"))
            continue
        m = re.match(r"^([A-Za-z_]+):\s*(.*)$", line)
        if m:
            key, v = m.group(1), m.group(2).strip()
            if v.startswith("[") and v.endswith("]"):
                fm[key] = [x.strip().strip("\"'") for x in v[1:-1].split(",") if x.strip()]
            else:
                fm[key] = v.strip("\"'") if v else []
    return fm, text[end + 4:]
