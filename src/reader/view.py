"""The model as a picture: one self-contained HTML page with a force-directed graph.

Propositions are nodes, coloured by R. A chain is drawn as a fork: its premises
join at a small knot, and one arrow leads on to the conclusion. A chain with
one premise is a plain arrow. Nothing here writes to the model.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from importlib import resources

from .model import Model
from .records import Answer


def graph(m: Model, ids: list[str] | None = None, focus: Iterable[str] = ()) -> dict:
    """Nodes and links for the props and chains in `ids` (everything if None).

    Chains whose ends are all shown are drawn too; a chain in `ids` brings its
    ends along. `focus` marks the ids that were looked up."""
    focus = set(focus)
    pids = set(m.props) if ids is None else {i for i in ids if i in m.props}
    cids = set(m.chains) if ids is None else {i for i in ids if i in m.chains}
    for cid in cids:
        c = m.chains[cid]
        pids.update((*c.premises, c.conclusion))
    cids |= {c.id for c in m.chains.values()
             if c.conclusion in pids and all(p in pids for p in c.premises)}
    pids &= set(m.props)

    nodes, links, chains = [], [], {}
    for pid in sorted(pids):
        p = m.props[pid]
        nodes.append({"id": pid, "name": p.name, "statement": p.statement,
                      "topics": list(p.topics), "vault": p.vault,
                      "focus": pid in focus, **_recall(m, pid)})
    for cid in sorted(cids):
        c = m.chains[cid]
        if c.conclusion not in pids or any(p not in pids for p in c.premises):
            continue
        chains[cid] = {"id": cid, "name": m.name(cid), "step": c.step,
                       "premises": list(c.premises), "conclusion": c.conclusion,
                       "focus": cid in focus, **_recall(m, cid)}
        if len(c.premises) == 1:
            links.append({"source": c.premises[0], "target": c.conclusion,
                          "chain": cid, "arrow": True})
            continue
        nodes.append({"id": cid, "knot": True, "chain": cid})
        links += [{"source": p, "target": cid, "chain": cid, "arrow": False}
                  for p in c.premises]
        links.append({"source": cid, "target": c.conclusion, "chain": cid, "arrow": True})
    return {"today": m.today.isoformat(), "nodes": nodes, "links": links, "chains": chains}


def html(data: dict, title: str = "reader") -> str:
    """The page, with the data and the graph library inlined (works offline)."""
    assets = resources.files("reader") / "assets"
    page = (assets / "graph.html").read_text()
    lib = (assets / "force-graph.min.js").read_text()
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return (page.replace("{{title}}", title)
                .replace("/*{{data}}*/", blob)
                .replace("/*{{force-graph}}*/", lib))


def _recall(m: Model, iid: str) -> dict:
    rc = m.recall(iid)
    last = rc.last
    return {"r": rc.r, "stability": rc.stability, "n": rc.n,
            "mis": bool(last and last.flag == "mis"),
            "answers": [_answer(a) for a in m.answers_for(iid)]}


def _answer(a: Answer) -> dict:
    return {"day": a.day.isoformat(), "kind": a.kind, "grade": a.grade, "conf": a.conf,
            "flag": a.flag, "note": a.note, "ask": f"{a.ask}/{a.n}"}
