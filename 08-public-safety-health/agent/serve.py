# agent/serve.py — AgentCore Runtime contract (/invocations + /ping).
from __future__ import annotations
import json, os, sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
_REPO = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(_REPO/"platform_core"), str(_REPO), str(_REPO/"08-public-safety-health")]
from agent.core import run_until_gate, resume  # noqa: E402
class H(BaseHTTPRequestHandler):
    def _s(self,c,b): self.send_response(c); self.send_header("Content-Type","application/json"); self.end_headers(); self.wfile.write(json.dumps(b).encode())
    def do_GET(self): self._s(200,{"status":"healthy"}) if self.path=="/ping" else self._s(404,{})
    def do_POST(self):
        if self.path!="/invocations": return self._s(404,{})
        n=int(self.headers.get("Content-Length",0)); p=json.loads(self.rfile.read(n) or b"{}")
        s=run_until_gate(p)
        if p.get("human_approval"): s=resume(s, approval=p["human_approval"])
        s.pop("_paused_at_gate", None); self._s(200, s)
if __name__=="__main__":
    HTTPServer(("0.0.0.0", int(os.getenv("PORT","8080"))), H).serve_forever()
