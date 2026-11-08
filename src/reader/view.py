"""The model as a picture: one self-contained HTML page with a force-directed graph.

Ideas are nodes, coloured by R. An edge is an arrow from the idea needed or
used to the idea that needs or uses it: solid when it needs it, dashed when it
only uses it. The layout pulls what an idea rests on above it. Nothing here
writes to the model.

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


def around(m: Model, seeds: list[str], depth: int = 2) -> list[str]:
    """The seeds, what they rest on (`depth` steps along needs and uses), and what
    rests on them directly."""
    out, frontier = list(dict.fromkeys(seeds)), list(seeds)
    seen = set(out)
    for _ in range(depth):
        nxt = [j for i in frontier for j in (*m.needs.get(i, ()), *m.uses.get(i, ()))
               if j not in seen]
        seen.update(nxt)
        out += list(dict.fromkeys(nxt))
        frontier = nxt
    for i in seeds:
        for j in (*m.needed_by.get(i, ()), *m.used_by.get(i, ())):
            if j not in seen:
                seen.add(j)
                out.append(j)
    return out


def graph(m: Model, ids: list[str] | None = None, focus: Iterable[str] = ()) -> dict:
    """Nodes and links for the ideas in `ids` (everything if None); `focus` marks
    the ideas that were looked up. A link runs from the idea needed or used to the
    idea that needs or uses it, and says which marks it carries."""
    focus = set(focus)
    keep = set(m.ideas) if ids is None else {i for i in ids if i in m.ideas}
    nodes, links = [], []
    for iid in sorted(keep):
        i = m.ideas[iid]
        nodes.append({"id": iid, "name": i.name, "kind": i.kind, "area": i.area,
                      "statement": i.statement, "aliases": list(i.aliases), "vault": i.vault,
                      "focus": iid in focus, **_recall(m, iid)})
    for src in sorted(keep):
        for dst in dict.fromkeys((*m.needs.get(src, ()), *m.uses.get(src, ()))):
            if dst in keep:
                links.append({"source": dst, "target": src,
                              "needs": dst in m.needs.get(src, ()),
                              "uses": dst in m.uses.get(src, ())})
    return {"now": f"{m.now:%Y-%m-%d %H:%M}", "nodes": nodes, "links": links}


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
