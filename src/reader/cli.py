"""reader: what Konstantin has shown they know, as recall probabilities.

The model lives in $READER_HOME (default ~/.local/share/reader):

  props.md     propositions, one checkable claim per line
  chains.md    chains: premises that together give a conclusion, by a step
  asks/        every question block asked: items, key, and their replies
  evidence.md  one line per answered item, the only learner data

The loop: look an idea up (`check`), ask what the lookup does not settle
(`ask`), and pass their reply on (`answer`, `grade`), which writes evidence at
once. Evidence comes only from questions asked and answered. A memory model,
FSRS-6 for now, turns each id's answers into R, the probability they recall it
today; an answer updates only the id it is about, and a wrong last answer
holds R at 0 until a right one. The labvault ($READER_VAULT,
default ~/labvault) is shown as hints, never counted and never written.

Run `reader -h` for the commands and `reader <command> -h` for each.
"""

import argparse
import datetime as dt
import difflib
import json
import math
import os
import random
import re
import shutil
import string
import subprocess
import sys
import unicodedata
from pathlib import Path

HOME = Path(os.environ.get("READER_HOME", Path.home() / ".local/share/reader"))
VAULT = Path(os.environ.get("READER_VAULT", Path.home() / "labvault"))
CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "reader"
SCOUT_MODEL = os.environ.get("READER_SCOUT_MODEL", "aqueduct/qwen-3.8-27b")

SEP = " · "
ID = r"[pc]_[0-9a-z]{3,8}"
QID = r"q_[0-9a-z]{4,16}"

# --------------------------------------------------------------------------
# The memory model: FSRS-6 with the py-fsrs 6.x default parameters.
# A pure function from an id's graded answers to (S, D, last day); R follows.

W = (0.212, 1.2931, 2.3065, 8.2956, 6.4133, 0.8334, 3.0194, 0.001, 1.8722,
     0.1666, 0.796, 1.4835, 0.0614, 0.2629, 1.6483, 0.6014, 1.8729, 0.5425,
     0.0912, 0.0658, 0.1542)
DECAY = -W[20]
FACTOR = 0.9 ** (1 / DECAY) - 1
GRADES = {"again": 1, "hard": 2, "good": 3, "easy": 4}  # `guess` carries no grade


def retrievability(s, t):
    return (1 + FACTOR * max(t, 0.0) / s) ** DECAY


def _init_d(g):
    return W[4] - math.exp(W[5] * (g - 1)) + 1


def _clamp_d(d):
    return min(10.0, max(1.0, d))


def _next_d(d, g):
    d2 = d + (10 - d) * (-W[6] * (g - 3)) / 9
    return _clamp_d(W[7] * _init_d(4) + (1 - W[7]) * d2)


def _next_s(s, d, g, t):
    if t < 1:  # same day
        inc = math.exp(W[17] * (g - 3 + W[18])) * s ** -W[19]
        if g >= 2:
            inc = max(inc, 1.0)
        return max(s * inc, 0.001)
    r = retrievability(s, t)
    if g == 1:
        long = W[11] * d ** -W[12] * ((s + 1) ** W[13] - 1) * math.exp((1 - r) * W[14])
        return max(min(long, s / math.exp(W[17] * W[18])), 0.001)
    hard = W[15] if g == 2 else 1
    easy = W[16] if g == 4 else 1
    return s * (1 + math.exp(W[8]) * (11 - d) * s ** -W[9]
                * (math.exp((1 - r) * W[10]) - 1) * hard * easy)


def replay(answers):
    """answers: [(day ordinal, seq, grade 1–4)]. Returns (S, D, last day) or None."""
    s = d = last = None
    for day, _seq, g in sorted(answers):
        if s is None:
            s, d, last = W[g - 1], _clamp_d(_init_d(g)), day
            continue
        s, d, last = _next_s(s, d, g, day - last), _next_d(d, g), day
    return None if s is None else (s, d, last)


# --------------------------------------------------------------------------
# Text

def norm(text):
    text = re.sub(r"\\([a-zA-Z]+)", r" \1 ", text)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def short(text, n=60):
    text = " ".join(text.split())
    return text if len(text) <= n else text[: n - 1] + "…"


def today():
    s = os.environ.get("READER_TODAY")
    return dt.date.fromisoformat(s) if s else dt.date.today()


def die(msg):
    print(f"reader: {msg}", file=sys.stderr)
    sys.exit(1)


# --------------------------------------------------------------------------
# Files

HEADERS = {
    "props.md": "# Propositions\n\n"
    "<!-- - p_id · name · statement · topics: a, b · vault: <id> · aliases: x, y -->\n\n",
    "chains.md": "# Chains\n\n"
    "<!-- - c_id · p_a ∧ p_b ⟹ p_c · step: <the reasoning step> -->\n\n",
    "evidence.md": "# Evidence\n\n"
    "<!-- One line per answered item, written by `reader answer` and `reader grade`:\n"
    "     - YYYY-MM-DD <id> pick|write|say <grade> [confidence] [mis|unseen] q_<ask>/<n> — <what they answered> -->\n\n",
}


def path(name):
    return HOME / name


def read_lines(name):
    p = path(name)
    return p.read_text().splitlines() if p.exists() else []


def ensure_home():
    HOME.mkdir(parents=True, exist_ok=True)
    (HOME / "asks").mkdir(exist_ok=True)
    for name, header in HEADERS.items():
        if not path(name).exists():
            path(name).write_text(header)


def append(name, lines):
    ensure_home()
    p = path(name)
    text = p.read_text() if p.exists() else ""
    with p.open("a") as f:
        if text and not text.endswith("\n"):
            f.write("\n")
        f.write("".join(line + "\n" for line in lines))


def parse_props(errors):
    props = {}
    for n, line in enumerate(read_lines("props.md"), 1):
        if not re.match(r"- p_", line):
            continue
        f = line[2:].split(SEP)
        if len(f) < 3 or not re.fullmatch(ID, f[0]):
            errors.append(f"props.md:{n}: want `- p_id · name · statement · key: value`")
            continue
        p = {"id": f[0], "name": f[1].strip(), "statement": f[2].strip(),
             "topics": [], "aliases": [], "vault": None, "line": line}
        for kv in f[3:]:
            k, _, v = kv.partition(":")
            k, v = k.strip(), v.strip()
            if k in ("topics", "aliases"):
                p[k] = [x.strip() for x in v.split(",") if x.strip()]
            elif k == "vault":
                p["vault"] = v or None
            else:
                errors.append(f"props.md:{n}: unknown field `{k}`")
        if p["id"] in props:
            errors.append(f"props.md:{n}: duplicate id {p['id']}")
        props[p["id"]] = p
    return props


def parse_chain_body(body, names=False):
    """`p_a ∧ p_b ⟹ p_c`; with names=True the parts may be proposition names."""
    part = r"\S+" if names else ID
    m = re.fullmatch(r"(.+?)\s*(?:⟹|=>)\s*(" + part + r")", body.strip())
    if not m:
        return None
    prem = [x for x in re.split(r"\s*(?:∧|\+|,|\s)\s*", m.group(1).strip()) if x]
    if not prem or not all(re.fullmatch(part, x) for x in prem):
        return None
    return prem, m.group(2)


def parse_chains(errors):
    chains = {}
    for n, line in enumerate(read_lines("chains.md"), 1):
        if not re.match(r"- c_", line):
            continue
        f = line[2:].split(SEP)
        parsed = parse_chain_body(f[1]) if len(f) >= 2 else None
        if not parsed or not re.fullmatch(ID, f[0]):
            errors.append(f"chains.md:{n}: want `- c_id · p_a ∧ p_b ⟹ p_c · step: …`")
            continue
        step = ""
        for kv in f[2:]:
            k, _, v = kv.partition(":")
            if k.strip() == "step":
                step = v.strip()
        chains[f[0]] = {"id": f[0], "premises": parsed[0], "conclusion": parsed[1],
                        "step": step, "line": line}
    return chains


EV_RE = re.compile(
    r"^- (?P<date>\d{4}-\d{2}-\d{2}) (?P<id>" + ID + r") (?P<kind>pick|write|say)"
    r" (?P<grade>again|hard|good|easy|guess)"
    r"(?: (?P<conf>[0-9]))?"
    r"(?: (?P<flag>mis|unseen))?"
    r" (?P<ask>" + QID + r")/(?P<n>\d+)"
    r"(?:\s+—\s*(?P<note>.*))?\s*$")


def ev_line(day, iid, kind, grade, ask, n, conf=None, flag=None, note=""):
    parts = [str(day), iid, kind, grade]
    if conf is not None:
        parts.append(str(conf))
    if flag:
        parts.append(flag)
    parts.append(f"{ask}/{n}")
    return "- " + " ".join(parts) + (f" — {' '.join(note.split())}" if note else "")


def parse_events(errors):
    events = []
    for n, line in enumerate(read_lines("evidence.md"), 1):
        if not line.startswith("- "):
            continue
        m = EV_RE.match(line)
        if not m:
            errors.append(f"evidence.md:{n}: want `- YYYY-MM-DD <id> <kind> <grade> [conf] "
                          f"[mis|unseen] q_<ask>/<n> — note`")
            continue
        if m["grade"] == "guess" and m["kind"] != "pick":
            errors.append(f"evidence.md:{n}: only a pick can be a guess")
            continue
        events.append({**m.groupdict(), "day": dt.date.fromisoformat(m["date"]),
                       "seq": n, "line": line})
    return events


# --------------------------------------------------------------------------
# The vault, read-only: hints, never evidence

def _frontmatter(text):
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end < 0:
        return {}, text
    fm, key = {}, None
    for line in text[3:end].splitlines():
        if re.match(r"^\s+-\s", line) and key:
            fm.setdefault(key, [])
            if isinstance(fm[key], list):
                fm[key].append(line.split("-", 1)[1].strip().strip("\"'"))
            continue
        m = re.match(r"^([A-Za-z_]+):\s*(.*)$", line)
        if m:
            key, v = m.group(1), m.group(2).strip()
            if v.startswith("[") and v.endswith("]"):
                fm[key] = [x.strip().strip("\"'") for x in v[1:-1].split(",") if x.strip()]
            elif v:
                fm[key] = v.strip("\"'")
            else:
                fm[key] = []
    return fm, text[end + 4:]


_VAULT = None


def vault():
    global _VAULT
    if _VAULT is not None:
        return _VAULT
    _VAULT = {}
    for f in sorted((VAULT / "notes").glob("*.md")):
        try:
            text = f.read_text(errors="replace")
        except OSError:
            continue
        fm, body = _frontmatter(text)
        aliases = fm.get("aliases") if isinstance(fm.get("aliases"), list) else []
        nid = f.stem
        title = next((a for a in aliases if a and a != nid), nid)
        _VAULT[nid] = {"id": nid, "title": title, "aliases": aliases,
                       "type": fm.get("type") or "", "status": fm.get("status") or "",
                       "created": fm.get("created") or "", "path": f}
    return _VAULT


def developed_date(nid):
    """When the note first reached status: developed (upkeep's ordering only)."""
    note = vault().get(nid)
    if not note or note["status"] != "developed":
        return None
    cache_file = CACHE / "developed.json"
    try:
        cache = json.loads(cache_file.read_text())
    except (OSError, ValueError):
        cache = {}
    mtime = int(note["path"].stat().st_mtime)
    hit = cache.get(nid)
    if hit and hit[0] == mtime:
        return dt.date.fromisoformat(hit[1])
    day = None
    if shutil.which("git") and (VAULT / ".git").exists():
        out = subprocess.run(
            ["git", "-C", str(VAULT), "log", "--reverse", "--format=%as",
             "-S", "status: developed", "--", f"notes/{nid}.md"],
            capture_output=True, text=True).stdout.split()
        if out:
            day = out[0]
    if not day:
        day = note["created"] if re.fullmatch(r"\d{4}-\d{2}-\d{2}", note["created"]) \
            else dt.date.fromtimestamp(mtime).isoformat()
    cache[nid] = [mtime, day]
    CACHE.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(cache))
    return dt.date.fromisoformat(day)


# --------------------------------------------------------------------------
# The model

class Model:
    def __init__(self):
        self.errors = []
        self.props = parse_props(self.errors)
        self.chains = parse_chains(self.errors)
        self.events = parse_events(self.errors)
        self.into = {}  # conclusion -> chain ids
        for c in self.chains.values():
            self.into.setdefault(c["conclusion"], []).append(c["id"])
        self.now = today().toordinal()
        self._state = None

    def exists(self, iid):
        return iid in self.props or iid in self.chains

    def name(self, iid):
        if iid in self.props:
            return self.props[iid]["name"]
        c = self.chains.get(iid)
        if c:
            return " ∧ ".join(self.name(p) for p in c["premises"]) + " ⟹ " + self.name(c["conclusion"])
        return iid

    def state(self):
        """id -> R (None: no graded answer), S, n answers, the last answer."""
        if self._state is not None:
            return self._state
        by_id = {}
        for e in self.events:
            by_id.setdefault(e["id"], []).append(e)
        st = {}
        for iid in list(self.props) + list(self.chains):
            evs = sorted(by_id.get(iid, []), key=lambda e: (e["day"], e["seq"]))
            graded = [(e["day"].toordinal(), e["seq"], GRADES[e["grade"]])
                      for e in evs if e["grade"] in GRADES]
            fit = replay(graded)
            r = retrievability(fit[0], self.now - fit[2]) if fit else None
            if graded and max(graded)[2] == 1:
                # FSRS assumes the answer was relearned after a miss; seeing the
                # answer is not evidence, so a miss holds R at 0 until a right answer.
                r = 0.0
            st[iid] = {"n": len(evs), "last": evs[-1] if evs else None,
                       "S": fit[0] if fit else None, "R": r}
        self._state = st
        return st

    # -- selection

    def hay(self, p):
        return norm(" ".join([p["id"], p["name"], p["statement"], *p["aliases"], *p["topics"]]))

    def match(self, terms):
        hits = []
        for t in terms:
            if self.exists(t):
                hits.append(t)
                continue
            for p in self.props.values():
                if t.startswith("#"):
                    if t[1:] in p["topics"]:
                        hits.append(p["id"])
                elif norm(t) and all(tok in self.hay(p) for tok in norm(t).split()):
                    hits.append(p["id"])
        return list(dict.fromkeys(hits))

    def below(self, seeds, levels):
        """What the seeds rest on: chains into them and their premises, `levels` deep."""
        chains, props, frontier = [], [], [s for s in seeds if s in self.props]
        seen = set(seeds)
        for cid in (s for s in seeds if s in self.chains):  # a matched chain: its premises
            for p in self.chains[cid]["premises"]:
                if p not in seen:
                    seen.add(p)
                    props.append(p)
                    frontier.append(p)
        for _ in range(levels):
            nxt = []
            for pid in frontier:
                for cid in self.into.get(pid, []):
                    if cid not in chains and cid not in seeds:
                        chains.append(cid)
                    for p in self.chains[cid]["premises"]:
                        if p not in seen:
                            seen.add(p)
                            props.append(p)
                            nxt.append(p)
            frontier = nxt
        return chains, props

    def above(self, seeds):
        """What rests directly on the seeds."""
        chains, props = [], []
        for cid in (s for s in seeds if s in self.chains):  # a matched chain: its conclusion
            if self.chains[cid]["conclusion"] not in seeds:
                props.append(self.chains[cid]["conclusion"])
        for c in self.chains.values():
            if any(p in seeds for p in c["premises"]) and c["id"] not in seeds:
                chains.append(c["id"])
                if c["conclusion"] not in seeds and c["conclusion"] not in props:
                    props.append(c["conclusion"])
        return chains, props

    def vault_matches(self, terms, limit=12):
        pointed = {p["vault"] for p in self.props.values() if p["vault"]}
        out = []
        for n in vault().values():
            if n["id"] in pointed or n["type"] in ("daily", "person"):
                continue
            hay = norm(" ".join([n["title"], *n["aliases"]]))
            if any(norm(t) and all(tok in hay for tok in norm(t).split())
                   for t in terms if not t.startswith("#") and not self.exists(t)):
                out.append(n)
        rank = {"developed": 0, "wip": 1, "stub": 2}
        out.sort(key=lambda n: (rank.get(n["status"], 3), n["title"]))
        return out[:limit]


def split_terms(args):
    return [t.strip() for t in " ".join(args).split(",") if t.strip()]


def fmt_r(r):
    return "  –" if r is None else f"{r:.2f}".lstrip("0") if r < 1 else "  1"


def fmt_row(m, iid, indent="  ", width=28):
    """id, name, R, answers, last answer, and what else the agent needs."""
    s = m.state()[iid]
    p = m.props.get(iid)
    name = short(p["name"] if p else m.name(iid), width)
    last = s["last"]
    if last:
        when = f"{last['day'].strftime('%m-%d')} {last['grade']}"
    else:
        when = "no evidence"
    notes = []
    if last and last["flag"] == "mis":
        notes.append(f"! last answer: {short(last['note'] or 'misconception', 80)}")
    if last and last["flag"] == "unseen":
        notes.append("last answer: never met it")
    if p and p["vault"]:
        notes.append(f"vault {p['vault']}")
    if p:
        notes.append(short(p["statement"], 70))
    else:
        notes.append("step: " + short(m.chains[iid]["step"], 70))
    return (f"{indent}{iid:<8}{name:<{width + 1}}R {fmt_r(s['R']):>3}  n{s['n']:<2} {when:<12}  "
            + " · ".join(notes))


def warn_errors(m):
    if m.errors:
        print(f"({len(m.errors)} parse problem(s); `reader lint`)", file=sys.stderr)


# --------------------------------------------------------------------------
# Commands: look up

def cmd_init(a):
    ensure_home()
    if shutil.which("git") and not (HOME / ".git").exists():
        subprocess.run(["git", "init", "-q", str(HOME)], check=False)
    print(f"reader: model in {HOME}")


def cmd_check(a):
    m = Model()
    terms = split_terms(a.terms)
    if not terms:
        die("check needs ids or terms, e.g. `reader check p_k2x9, girsanov, #sde`")
    seeds = m.match(terms)
    limit = None if a.all else 30
    print(f"reader check · {', '.join(terms)} · {today()}"
          f" · R = recall probability today, – = no evidence")
    if seeds:
        print("matched")
        for iid in seeds[:limit]:
            print(fmt_row(m, iid))
        if limit and len(seeds) > limit:
            print(f"  … {len(seeds) - limit} more (--all)")
        bc, bp = m.below(seeds[:limit], a.depth)
        if bc or bp:
            print("rests on (chains, then premises)")
            for cid in bc:
                print(fmt_row(m, cid))
            for pid in bp:
                print(fmt_row(m, pid))
        ac, ap = m.above(seeds[:limit])
        if ac or ap:
            print("rests on it")
            for cid in ac:
                print(fmt_row(m, cid))
            for pid in ap:
                print(fmt_row(m, pid))
    vm = m.vault_matches(terms)
    if vm:
        print("vault notes with no proposition (hints, not evidence)")
        for n in vm:
            print(f"  {n['id']}  {short(n['title'], 50)}  ({n['status'] or n['type']})")
    if not seeds and not vm:
        print("nothing recorded; add the idea with `reader new prop`, then ask")
    warn_errors(m)


def cmd_find(a):
    m = Model()
    terms = split_terms(a.terms)
    toks = [tok for t in terms for tok in norm(t).split()]
    scored = []
    for p in m.props.values():
        hay, name = m.hay(p), norm(p["name"] + " " + " ".join(p["aliases"]))
        s = sum(tok in hay for tok in toks) + sum(tok in name for tok in toks)
        if s:
            scored.append((-s, p["id"]))
    for _, pid in sorted(scored)[: a.limit]:
        p = m.props[pid]
        print(f"{pid:<8}{short(p['name'], 28):<29}{short(p['statement'], 100)}")
    for c in m.chains.values():
        if any(pid in (c["conclusion"], *c["premises"]) for _, pid in sorted(scored)[:3]):
            print(f"{c['id']:<8}{short(m.name(c['id']), 120)}")
    vm = m.vault_matches(terms, limit=a.limit)
    for n in vm:
        print(f"vault {n['id']}  {short(n['title'], 50)}  ({n['status'] or n['type']})")
    if not scored and not vm:
        print("no match")


def load_ask(qid):
    p = path("asks") / f"{qid}.json"
    if not p.exists():
        die(f"no question block {qid}")
    return p, json.loads(p.read_text())


def cmd_show(a):
    m = Model()
    iid = a.id
    if iid in m.props:
        print(m.props[iid]["line"][2:])
    elif iid in m.chains:
        print(m.chains[iid]["line"][2:])
        print(f"  = {m.name(iid)}")
    else:
        die(f"no proposition or chain {iid}")
    asks = {}
    for e in m.events:
        if e["id"] != iid:
            continue
        if e["ask"] not in asks:
            p = path("asks") / f"{e['ask']}.json"
            asks[e["ask"]] = json.loads(p.read_text()) if p.exists() else None
        ask = asks[e["ask"]]
        it = ask["items"][int(e["n"]) - 1] if ask and int(e["n"]) <= len(ask["items"]) else None
        print(f"  {e['line'][2:]}")
        if it:
            print(f"      asked: {short(it['q'], 110)}")
    s = m.state()[iid]
    if s["R"] is not None:
        print(f"  R today {s['R']:.3f}, S {s['S']:.1f} days, {s['n']} answer(s)")
    else:
        print(f"  no graded answer yet ({s['n']} answer(s))")


def cmd_status(a):
    m = Model()
    st = m.state()
    with_ev = [iid for iid in st if st[iid]["n"]]
    print(f"reader · {today()} · {len(m.props)} propositions, {len(m.chains)} chains, "
          f"{len(m.events)} answers on {len(with_ev)} ids")
    topics = {}
    for p in m.props.values():
        for t in p["topics"] or ["(none)"]:
            topics.setdefault(t, []).append(p["id"])
    for t, ids in sorted(topics.items(), key=lambda kv: -len(kv[1]))[:15]:
        rs = [st[i]["R"] for i in ids if st[i]["R"] is not None]
        mean = f"mean R {sum(rs) / len(rs):.2f}" if rs else ""
        print(f"  #{t:<24}{len(ids):>3} props, {len(rs):>2} with evidence  {mean}")
    mis = [iid for iid in st if st[iid]["last"] and st[iid]["last"]["flag"] == "mis"]
    if mis:
        print("misconceptions shown in the last answer:")
        for iid in mis:
            print(f"  {iid}  {short(m.name(iid), 30)}  {short(st[iid]['last']['note'] or '', 80)}")
    if m.events:
        last = max(m.events, key=lambda e: (e["day"], e["seq"]))
        print(f"last answer: {last['day']} ({last['ask']})")
    warn_errors(m)


# --------------------------------------------------------------------------
# Commands: propositions and chains

def new_id(taken, prefix, k=4):
    while True:
        iid = prefix + "".join(random.choices(string.digits + string.ascii_lowercase, k=k))
        if iid not in taken:
            return iid


def cmd_new_prop(a):
    m = Model()
    for field in (a.name, a.statement, a.aliases or "", a.topics or ""):
        if SEP.strip() in field or "\n" in field:
            die("fields may not contain ` · ` or newlines")
    clash = [p for p in m.props.values() if norm(p["name"]) == norm(a.name)]
    if clash and not a.force:
        die(f"{clash[0]['id']} already has this name: {clash[0]['statement']} (--force to add anyway)")
    if a.vault and a.vault not in vault():
        die(f"no vault note {a.vault}")
    iid = new_id(set(m.props) | set(m.chains), "p_")
    line = f"- {iid}{SEP}{a.name}{SEP}{a.statement}"
    if a.topics:
        line += f"{SEP}topics: {a.topics}"
    if a.vault:
        line += f"{SEP}vault: {a.vault}"
    if a.aliases:
        line += f"{SEP}aliases: {a.aliases}"
    append("props.md", [line])
    print(iid)


def cmd_new_chain(a):
    m = Model()
    parsed = parse_chain_body(" ".join(a.chain), names=True)
    if not parsed:
        die("want: reader new chain p_a p_b => p_c --step '…' (ids or names)")

    def resolve(x):
        if re.fullmatch(ID, x):
            return x
        hits = [p["id"] for p in m.props.values() if norm(p["name"]) == norm(x)]
        if len(hits) != 1:
            die(f"`{x}` names {len(hits)} propositions; use an id")
        return hits[0]

    premises, conclusion = [resolve(x) for x in parsed[0]], resolve(parsed[1])
    for pid in premises + [conclusion]:
        if pid not in m.props:
            die(f"no proposition {pid}")
    if conclusion in premises:
        die("a conclusion cannot be its own premise")
    key = (tuple(sorted(premises)), conclusion)
    for c in m.chains.values():
        if (tuple(sorted(c["premises"])), c["conclusion"]) == key:
            die(f"{c['id']} is already this chain")
    if not a.step or SEP.strip() in a.step:
        die("--step is required and may not contain ` · `")
    iid = new_id(set(m.props) | set(m.chains), "c_")
    append("chains.md", [f"- {iid}{SEP}{' ∧ '.join(premises)} ⟹ {conclusion}{SEP}step: {a.step}"])
    print(iid)


# --------------------------------------------------------------------------
# Commands: questions and answers, the only source of evidence

ITEM_RE = re.compile(r"^(\d+)\s+(pick|write|say)\s+(" + ID + r"):\s*(.*)$")


def parse_items(text):
    title, items, problems = "", [], []
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        if line.startswith("# ") and not items:
            title = line[2:].strip()
            continue
        m = ITEM_RE.match(line)
        if m:
            items.append({"n": int(m[1]), "kind": m[2], "id": m[3], "q": m[4],
                          "options": [], "why": "", "ref": ""})
            continue
        if not items:
            problems.append(f"before the first item: {line}")
            continue
        it, body = items[-1], line.strip()
        if body.startswith("* ") or body.startswith("- "):
            text_, _, mis = body[2:].partition(" :: ")
            it["options"].append({"text": text_.strip(), "correct": body[0] == "*",
                                  "mis": mis.strip()})
        elif body.startswith("? "):
            it["why"] = (it["why"] + " " + body[2:]).strip()
        elif body.startswith("= "):
            it["ref"] = (it["ref"] + " " + body[2:]).strip()
        else:
            it["q"] = (it["q"] + " " + body).strip()
    for k, it in enumerate(items, 1):
        if it["n"] != k:
            problems.append(f"items must be numbered 1, 2, 3, …; got {it['n']} at position {k}")
        if it["kind"] == "pick":
            if len(it["options"]) < 2 or sum(o["correct"] for o in it["options"]) != 1:
                problems.append(f"item {it['n']}: a pick needs ≥ 2 options, exactly one `* `")
        elif not it["ref"]:
            problems.append(f"item {it['n']}: a {it['kind']} needs a `= ` reference answer")
    return title, items, problems


def legend(items):
    """The reply forms this block uses, with its own item numbers."""
    first = {}
    for it in items:
        first.setdefault(it["kind"], it["n"])
    parts = []
    if "pick" in first:
        parts.append(f"`{first['pick']}b8` option b, 80% sure")
    if "write" in first:
        parts.append(f"`{first['write']}.` done writing")
    if "say" in first:
        parts.append(f"`{first['say']}: …` your answer")
    if "pick" in first or "write" in first:
        parts += ["`-` never met", "`?` seen it, can't produce it"]
        parts.append("`: …` after any answer for your thoughts")
    return " · ".join(parts)


def cmd_ask(a):
    m = Model()
    text = Path(a.file).read_text() if a.file else sys.stdin.read()
    title, items, problems = parse_items(text)
    if not items:
        problems.append("no items")
    for it in items:
        if not m.exists(it["id"]):
            problems.append(f"item {it['n']}: unknown id {it['id']} (add it with `reader new`)")
    if problems:
        die("question block not stored:\n  " + "\n  ".join(problems))
    for it in items:
        random.shuffle(it["options"])
        it["state"] = "open"
    ensure_home()
    taken = {p.stem for p in path("asks").glob("q_*.json")}
    qid = new_id(taken, "q_")
    ask = {"id": qid, "title": title, "asked": dt.datetime.now().isoformat(timespec="seconds"),
           "items": items}
    (path("asks") / f"{qid}.json").write_text(json.dumps(ask, indent=1, ensure_ascii=False))
    # Markdown: the agent shows this as it is, and chat UIs render it.
    print(f"**{title or 'Questions'}** · reply on one line\n")
    print(f"_{legend(items)}_")
    for it in items:
        hint = {"pick": "", "write": f" — _on your tablet; reply `{it['n']}.` when done_",
                "say": " — _one line_"}[it["kind"]]
        print(f"\n**{it['n']}** · {it['q']}{hint}")
        if it["options"]:
            print()
        for k, o in enumerate(it["options"]):
            print(f"- **{string.ascii_lowercase[k]})** {o['text']}")
    print(f"\n<!-- for the agent: block {qid}; pass the reply on with "
          f"`reader answer {qid} \"<reply>\"` -->")


def parse_reply(reply, n_items):
    pat = re.compile(r"(?:(?<=[\s,;])|^)(\d{1,2})([a-h][0-9]?|[.=~x?\-])(?=[\s,;:]|$)")
    found, last = [], 0
    for mm in pat.finditer(reply):
        n = int(mm.group(1))
        if last < n <= n_items:
            found.append((n, mm.group(2), mm.start(), mm.end()))
            last = n
    entries = []
    for k, (n, tok, _start, end) in enumerate(found):
        stop = found[k + 1][2] if k + 1 < len(found) else len(reply)
        rest = reply[end:stop].strip().strip(",;").strip()
        entries.append((n, tok, rest[1:].strip() if rest.startswith(":") else rest))
    # `3: free text` for a say item
    for mm in re.finditer(r"(?:(?<=\s)|^)(\d{1,2}):\s*", reply):
        n = int(mm.group(1))
        if 0 < n <= n_items and all(e[0] != n for e in entries):
            stop = min([s for (_n, _t, s, _e) in found if s > mm.end()] + [len(reply)])
            entries.append((n, ":", reply[mm.end():stop].strip()))
    return sorted(entries)


def record(qid, n, line):
    """Write one answered item's evidence now, replacing an earlier line for it."""
    ensure_home()
    tag = f" {qid}/{n}"
    lines = read_lines("evidence.md")
    kept = [x for x in lines if not (x.startswith("- ") and (tag + " ") in (x + " "))]
    if len(kept) != len(lines):
        path("evidence.md").write_text("\n".join(kept) + "\n")
    append("evidence.md", [line])


def cmd_answer(a):
    m = Model()
    p, ask = load_ask(a.ask)
    qid, items = ask["id"], ask["items"]
    reply = " ".join(a.reply)
    entries = parse_reply(reply, len(items))
    if not entries:
        die("could not read the reply; entries look like `1b8 2. 3- 4?` or `5: …`")
    day, out, agent, logged = today(), [], [], 0
    for n, tok, thoughts in entries:
        it = items[n - 1]
        said = f" · “{short(thoughts, 80)}”" if thoughts else ""
        if it["state"] == "done" and not a.redo:
            out.append(f"- **{n}** already answered (--redo to answer again)")
            continue
        it.setdefault("replies", []).append({"at": dt.datetime.now().isoformat(timespec="seconds"),
                                             "token": tok, "thoughts": thoughts})
        right = next((o for o in it["options"] if o["correct"]), None)
        if tok == "-":
            record(qid, n, ev_line(day, it["id"], it["kind"], "again", qid, n, flag="unseen",
                                   note="never met it" + said))
            out.append(f"- **{n}** never met")
            it["state"], logged = "done", logged + 1
            continue
        if tok == "?":
            record(qid, n, ev_line(day, it["id"], it["kind"], "again", qid, n,
                                   note="seen it, could not produce it" + said))
            out.append(f"- **{n}** seen, not producible — it is: " + (it["ref"] or right["text"]))
            it["state"], logged = "done", logged + 1
            continue
        if it["kind"] == "pick":
            if not re.fullmatch(r"[a-h][0-9]?", tok):
                out.append(f"- **{n}** wants a letter and a confidence digit, e.g. `{n}b8`")
                continue
            k = ord(tok[0]) - ord("a")
            if k >= len(it["options"]):
                out.append(f"- **{n}** has no option {tok[0]}")
                continue
            conf = int(tok[1]) if len(tok) > 1 else 5
            chosen = it["options"][k]
            rl = string.ascii_lowercase[it["options"].index(right)]
            chance = 1 / len(it["options"])
            nc = "" if len(tok) > 1 else " (no confidence given, read as 5)"
            if chosen["correct"]:
                grade = "good" if conf >= 8 else "hard" if conf / 10 > chance else "guess"
                verdict = {"good": "✓ solid", "hard": "✓ fragile", "guess": "✓ but a guess"}[grade]
                record(qid, n, ev_line(day, it["id"], "pick", grade, qid, n, conf=conf,
                                       note=f"picked {short(chosen['text'], 50)}{said}"))
                out.append(f"- **{n}** {verdict} — {tok[0]} at {conf}0%{nc}"
                           + (f". {it['why']}" if it["why"] and grade != "good" else ""))
            else:
                mis = conf >= 8
                if mis:
                    belief = chosen["mis"] or short(chosen["text"], 50)
                    note = f"misconception: {belief}; right: {short(right['text'], 50)}{said}"
                else:
                    note = f"picked {short(chosen['text'], 50)}, right: {short(right['text'], 50)}{said}"
                record(qid, n, ev_line(day, it["id"], "pick", "again", qid, n, conf=conf,
                                       flag="mis" if mis else None, note=note))
                out.append(f"- **{n}** ✗ {'misconception' if mis else 'gap'} — {tok[0]} at {conf}0%{nc}. "
                           f"Right: **{rl})** {right['text']}"
                           + (f". _{chosen['mis']}_" if chosen["mis"] and mis else "")
                           + (f". {it['why']}" if it["why"] else ""))
            it["state"], logged = "done", logged + 1
        elif it["kind"] == "write":
            if tok == ".":
                it["state"] = "shown"
                out.append(f"- **{n}** compare with: {it['ref']}  \n"
                           f"  reply `{n}=` matches · `{n}~` small slip · `{n}x` wrong")
            elif tok in ("=", "~", "x"):
                grade = {"=": "good", "~": "hard", "x": "again"}[tok]
                note = {"=": "wrote it correctly", "~": "wrote it with a small slip",
                        "x": "could not write it"}[tok]
                record(qid, n, ev_line(day, it["id"], "write", grade, qid, n, note=note + said))
                out.append(f"- **{n}** {'✓' if tok != 'x' else '✗'} {note}")
                it["state"], logged = "done", logged + 1
            else:
                out.append(f"- **{n}** wants `{n}.` then `{n}=`, `{n}~` or `{n}x`")
        else:  # say
            if tok != ":" and not thoughts:
                out.append(f"- **{n}** wants `{n}: <answer>`")
                continue
            it["answer"] = thoughts
            it["state"] = "to-grade"
            out.append(f"- **{n}** you said: “{short(thoughts, 100)}”  \n  reference: {it['ref']}")
            agent.append(f"grade {n}: reader grade {qid} {n} good|hard|again [--mis 'believed → true']")
    p.write_text(json.dumps(ask, indent=1, ensure_ascii=False))
    print("\n".join(out))
    notes = agent + ([f"{logged} answer(s) recorded"] if logged else [])
    if notes:
        print("\n<!-- for the agent: " + "; ".join(notes) + " -->")


def cmd_grade(a):
    m = Model()
    p, ask = load_ask(a.ask)
    if not 0 < a.n <= len(ask["items"]):
        die(f"no item {a.n}")
    it = ask["items"][a.n - 1]
    if a.grade not in GRADES:
        die("grade is again, hard, good or easy")
    if it["state"] == "open":
        die(f"item {a.n} has no answer yet; pass their reply to `reader answer {ask['id']}`")
    if a.mis and a.grade != "again":
        die("a misconception is graded again")
    note = a.mis and f"misconception: {a.mis}" or a.note or short(it.get("answer", ""), 80) or "graded by the agent"
    record(ask["id"], a.n, ev_line(today(), it["id"], it["kind"], a.grade, ask["id"], a.n,
                                   flag="mis" if a.mis else None, note=note))
    it["state"] = "done"
    p.write_text(json.dumps(ask, indent=1, ensure_ascii=False))
    print(f"{a.n} graded {a.grade}, recorded")


# --------------------------------------------------------------------------
# Upkeep

def cmd_calib(a):
    m = Model()
    bins = {}
    for e in m.events:
        if e["kind"] == "pick" and e["conf"] is not None and e["flag"] != "unseen":
            bins.setdefault(int(e["conf"]), []).append(e["grade"] != "again")
    if not bins:
        print("no picks with confidence yet")
        return
    print("conf  n   right  (said)")
    for c in sorted(bins):
        xs = bins[c]
        print(f"  {c}  {len(xs):>3}  {sum(xs) / len(xs):>5.0%}  ({c}0%)")


def cmd_dupes(a):
    m = Model()
    ps = list(m.props.values())
    keys = [(norm(p["name"]), norm(p["statement"])) for p in ps]
    found = 0
    for i in range(len(ps)):
        for j in range(i + 1, len(ps)):
            r = max(difflib.SequenceMatcher(None, keys[i][0], keys[j][0]).ratio(),
                    difflib.SequenceMatcher(None, keys[i][1], keys[j][1]).ratio())
            if r >= a.threshold:
                found += 1
                print(f"{r:.2f}  {ps[i]['id']} {short(ps[i]['name'], 30)}  ~  "
                      f"{ps[j]['id']} {short(ps[j]['name'], 30)}")
    if not found:
        print("no likely duplicates")


def cmd_lint(a):
    m = Model()
    problems = list(m.errors)
    for c in m.chains.values():
        for pid in c["premises"] + [c["conclusion"]]:
            if pid not in m.props:
                problems.append(f"{c['id']}: unknown proposition {pid}")
    seen = set()
    for e in m.events:
        where = f"evidence.md:{e['seq']}"
        if not m.exists(e["id"]):
            problems.append(f"{where}: unknown id {e['id']}")
        key = (e["ask"], e["n"])
        if key in seen:
            problems.append(f"{where}: {e['ask']}/{e['n']} answered twice")
        seen.add(key)
        p = path("asks") / f"{e['ask']}.json"
        if not p.exists():
            problems.append(f"{where}: no question block {e['ask']}")
            continue
        items = json.loads(p.read_text())["items"]
        if int(e["n"]) > len(items) or items[int(e["n"]) - 1]["id"] != e["id"]:
            problems.append(f"{where}: {e['ask']}/{e['n']} does not ask about {e['id']}")
    if (VAULT / "notes").exists():
        for p in m.props.values():
            if p["vault"] and p["vault"] not in vault():
                problems.append(f"{p['id']}: no vault note {p['vault']}")
    for line in problems:
        print(line)
    if problems:
        sys.exit(1)
    print(f"ok · {len(m.props)} propositions, {len(m.chains)} chains, {len(m.events)} answers")


def cmd_upkeep(a):
    """Lint, back up, list duplicates, and draft propositions for new developed notes."""
    ensure_home()
    m = Model()
    report = [f"# reader upkeep · {today()}"]
    r = subprocess.run([sys.executable, __file__, "lint"], capture_output=True, text=True)
    report.append("lint: " + (r.stdout.strip().splitlines() or ["?"])[-1] if r.returncode == 0
                  else "lint problems:\n" + r.stdout.strip())
    if (HOME / ".git").exists():
        subprocess.run(["git", "-C", str(HOME), "add", "-A"], check=False)
        c = subprocess.run(["git", "-C", str(HOME), "commit", "-qm", f"upkeep {today()}"],
                           capture_output=True, text=True)
        report.append("backup: committed" if c.returncode == 0 else "backup: nothing new")
        remote = subprocess.run(["git", "-C", str(HOME), "remote"], capture_output=True, text=True).stdout
        if remote.strip():
            pu = subprocess.run(["git", "-C", str(HOME), "push", "-q"], capture_output=True, text=True)
            report.append("push: ok" if pu.returncode == 0 else f"push failed: {pu.stderr.strip()[-200:]}")
    d = subprocess.run([sys.executable, __file__, "dupes"], capture_output=True, text=True).stdout.strip()
    if d and d != "no likely duplicates":
        report.append("likely duplicates (merge by hand):\n" + d)
    handled = set(re.findall(r"^## ([0-9a-z]{6}) ", "\n".join(read_lines("proposals.md")), re.M))
    pointed = {p["vault"] for p in m.props.values() if p["vault"]}
    todo = []
    for n in vault().values():
        if n["status"] == "developed" and n["type"] == "note" and n["id"] not in pointed | handled:
            todo.append((developed_date(n["id"]) or dt.date.min, n))
    todo.sort(key=lambda x: x[0], reverse=True)
    batch = todo[: a.limit]
    if not batch:
        report.append("vault: no new developed notes")
    elif not a.scout:
        report.append(f"vault: {len(todo)} developed notes without propositions; newest:\n"
                      + "\n".join(f"  {n['id']}  {n['title']}  ({day})" for day, n in batch))
    else:
        out = []
        for day, n in batch:
            ans = subprocess.run(
                [sys.executable, __file__, "scout", "--timeout", str(a.timeout),
                 f"Read notes/{n['id']}.md and the notes it links to. Propose the propositions "
                 f"(and chains between them) that note {n['id']} states, at most 6."],
                capture_output=True, text=True)
            body = ans.stdout.strip() if ans.returncode == 0 else f"(scout failed: {ans.stderr.strip()[-200:]})"
            out += ["", f"## {n['id']} · {n['title']} · developed {day} · proposed {today()}", body]
        append("proposals.md", out)
        report.append(f"vault: drafted propositions for {len(batch)} of {len(todo)} notes "
                      f"into proposals.md: " + ", ".join(n["id"] for _, n in batch))
    print("\n\n".join(report))


SCOUT_PROMPT = """You are a read-only scout for an agent that models what one
reader (Konstantin, maths PhD student) knows. You work in their labvault, a
zettelkasten of markdown notes: notes/<id>.md, id = six base36 characters,
title = first entry of `aliases:`, `status:` stub/wip/developed, Pandoc fenced
divs such as :::{.theorem} for blocks, links [[id|label]]. Never create, edit or
move any file. Search with grep and find, read what you need, and answer
tersely. When asked for propositions, give one per line as

  reader new prop "<name>" "<statement, LaTeX in $…$, assumptions inside>" --topics <t> --vault <id>

with a kebab-case name, one checkable claim per line, taken from a note's own
definition or theorem block; then chains as

  reader new chain <name-a> <name-b> => <name-c> --step "<the reasoning step>"

using the names you proposed. Cite note ids. No preamble."""


def cmd_scout(a):
    if not shutil.which("pi"):
        die("pi is not installed")
    cmd = ["pi", "-p", "--no-session", "--no-skills", "--no-context-files",
           "--tools", "read,grep,find,ls", "--model", a.model,
           "--append-system-prompt", SCOUT_PROMPT, " ".join(a.task)]
    try:
        r = subprocess.run(cmd, cwd=VAULT, capture_output=True, text=True, timeout=a.timeout)
    except subprocess.TimeoutExpired:
        die(f"scout timed out after {a.timeout}s ({a.model})")
    if r.returncode:
        die(f"scout failed ({a.model}): {r.stderr.strip()[-500:]}")
    print(r.stdout.strip())


# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(prog="reader", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add(name, fn, help_):
        sp = sub.add_parser(name, help=help_, description=help_)
        sp.set_defaults(fn=fn)
        return sp

    add("init", cmd_init, "create the model folder and its git repo")
    sp = add("check", cmd_check, "look ideas up: each with what it rests on, what rests on it, "
             "and R per id (ids or terms, comma-separated; #topic)")
    sp.add_argument("terms", nargs="+")
    sp.add_argument("--depth", type=int, default=2, help="levels of premises (default 2)")
    sp.add_argument("--all", action="store_true", help="no limit on matches")
    sp = add("find", cmd_find, "existing propositions and vault notes for some terms")
    sp.add_argument("terms", nargs="+")
    sp.add_argument("--limit", type=int, default=8)
    sp = add("show", cmd_show, "one proposition or chain with every answer and its question")
    sp.add_argument("id")
    add("status", cmd_status, "the whole model in a few lines")

    sp = add("new", None, "add a proposition or a chain")
    nsub = sp.add_subparsers(dest="what", required=True)
    np_ = nsub.add_parser("prop", help="add a proposition; prints its id")
    np_.add_argument("name")
    np_.add_argument("statement")
    np_.add_argument("--topics")
    np_.add_argument("--vault")
    np_.add_argument("--aliases")
    np_.add_argument("--force", action="store_true")
    np_.set_defaults(fn=cmd_new_prop)
    nc = nsub.add_parser("chain", help="add a chain: p_a p_b => p_c --step '…'; prints its id")
    nc.add_argument("chain", nargs="+")
    nc.add_argument("--step", required=True)
    nc.set_defaults(fn=cmd_new_chain)

    sp = add("ask", cmd_ask, "store a question block (file or stdin), print it shuffled with its id")
    sp.add_argument("file", nargs="?")
    sp = add("answer", cmd_answer, "grade their one-line reply to a block and record it now")
    sp.add_argument("ask", help="the block id, q_…")
    sp.add_argument("reply", nargs="+")
    sp.add_argument("--redo", action="store_true", help="answer an item again, replacing its evidence")
    sp = add("grade", cmd_grade, "grade a say item (or regrade any answered item) and record it now")
    sp.add_argument("ask", help="the block id, q_…")
    sp.add_argument("n", type=int)
    sp.add_argument("grade")
    sp.add_argument("--mis", help="the misconception the answer shows: 'believed X → Y'")
    sp.add_argument("--note")

    add("calib", cmd_calib, "how often their confidence digits are right")
    sp = add("dupes", cmd_dupes, "likely duplicate propositions")
    sp.add_argument("--threshold", type=float, default=0.85)
    add("lint", cmd_lint, "check that every file parses and every id and answer resolves")
    sp = add("upkeep", cmd_upkeep, "daily: lint, back up, duplicates, draft seeds for new notes")
    sp.add_argument("--scout", action="store_true", help="draft propositions with the scout")
    sp.add_argument("--limit", type=int, default=5)
    sp.add_argument("--timeout", type=int, default=600)
    sp = add("scout", cmd_scout, "ask a cheap read-only model to search the vault")
    sp.add_argument("task", nargs="+")
    sp.add_argument("--model", default=SCOUT_MODEL)
    sp.add_argument("--timeout", type=int, default=900)

    a = ap.parse_args()
    if a.fn is None:
        ap.parse_args([a.cmd, "-h"])
    if a.cmd in ("answer", "grade") and not re.fullmatch(QID, a.ask):
        die(f"`{a.ask}` is not a block id; `reader ask` prints one (q_…)")
    a.fn(a)


if __name__ == "__main__":
    main()
