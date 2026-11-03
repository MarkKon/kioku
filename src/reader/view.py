"""The model as a picture: one self-contained HTML page with a force-directed graph.

Propositions are nodes, coloured by R. A chain is drawn as a fork: its premises
join at a small knot, and one arrow leads on to the conclusion. A chain with
one premise is a plain arrow. The layout pulls premises above their conclusions,
so implications point down the page. Nothing here writes to the model.

`reader graph` serves the page on localhost, building it afresh on every
request, so the page's refresh button shows answers recorded since it opened.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
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
    return {"now": f"{m.now:%Y-%m-%d %H:%M}", "nodes": nodes, "links": links,
            "chains": chains}


def html(data: dict, title: str = "reader", live: bool = False) -> str:
    """The page, with the data and the graph library inlined (works offline).

    A live page is served by `serve` and shows a refresh button."""
    assets = resources.files("reader") / "assets"
    page = (assets / "graph.html").read_text()
    lib = (assets / "force-graph.min.js").read_text()
    blob = json.dumps({**data, "live": live}, ensure_ascii=False).replace("</", "<\\/")
    return (page.replace("{{title}}", title)
                .replace("/*{{data}}*/", blob)
                .replace("/*{{force-graph}}*/", lib))


def serve(page: Callable[[], str], port: int = 0,
          ready: Callable[[str], object] = print) -> None:
    """Serve `page()` on 127.0.0.1 until interrupted, calling it on every request."""

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.split("?")[0] != "/":
                self.send_error(404)
                return
            body = page().encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    with ThreadingHTTPServer(("127.0.0.1", port), Handler) as httpd:
        ready(f"http://127.0.0.1:{httpd.server_address[1]}/")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass


def _recall(m: Model, iid: str) -> dict:
    rc = m.recall(iid)
    last = rc.last
    return {"r": rc.r, "stability": rc.stability, "n": rc.n,
            "mis": bool(last and last.flag == "mis"),
            "answers": [_answer(a) for a in m.answers_for(iid)]}


def _answer(a: Answer) -> dict:
    return {"at": f"{a.at:%Y-%m-%d %H:%M}", "kind": a.kind, "grade": a.grade, "conf": a.conf,
            "flag": a.flag, "note": a.note, "ask": f"{a.ask}/{a.n}"}
