"""Shared AgentCore Runtime contract server. Agent-specific core is injected via
AGENT_CORE_MODULE (a module exposing run_until_gate/resume)."""
from __future__ import annotations
import importlib, json, os
from http.server import BaseHTTPRequestHandler, HTTPServer

_core = importlib.import_module(os.getenv("AGENT_CORE_MODULE", "core"))


class H(BaseHTTPRequestHandler):
    def _s(self, c, b): self.send_response(c); self.send_header("Content-Type","application/json"); self.end_headers(); self.wfile.write(json.dumps(b).encode())
    def do_GET(self): self._s(200, {"status":"healthy"}) if self.path=="/ping" else self._s(404, {})
    def do_POST(self):
        if self.path != "/invocations": return self._s(404, {})
        n=int(self.headers.get("Content-Length",0)); p=json.loads(self.rfile.read(n) or b"{}")
        out=_core.run(p) if hasattr(_core,"run") else p
        self._s(200, out)


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", int(os.getenv("PORT","8080"))), H).serve_forever()
