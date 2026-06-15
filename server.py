#!/usr/bin/env python3
"""
Customer360 MCP Server — local Docker version
- /mcp   : MCP JSON-RPC (for the CLI)
- /ask   : simple REST (for any web UI)
- /health: health check
"""

import os, json, traceback
import requests
import snowflake.connector
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SF_ACCOUNT   = os.environ.get("SF_ACCOUNT", "urkdocl-wj23271")
SF_USER      = os.environ.get("SF_USER", "KAUSHIK")
SF_PASSWORD  = os.environ.get("SF_PASSWORD", "#Kaushpass@123")
SF_ROLE      = os.environ.get("SF_ROLE", "ACCOUNTADMIN")
SF_WAREHOUSE = os.environ.get("SF_WAREHOUSE", "COMPUTE_WH")
SF_DATABASE  = os.environ.get("SF_DATABASE", "CUSTOMER_360")
SF_SCHEMA    = os.environ.get("SF_SCHEMA", "SILVER")
SF_HOST      = f"https://{SF_ACCOUNT}.snowflakecomputing.com"
SEMANTIC_MODEL_FILE = os.environ.get(
    "SEMANTIC_MODEL_FILE",
    "@CUSTOMER_360.BRONZE.CUSTOMER_STAGE/customer360_model.yaml",
)


def _connect():
    return snowflake.connector.connect(
        account=SF_ACCOUNT, user=SF_USER, password=SF_PASSWORD,
        role=SF_ROLE, warehouse=SF_WAREHOUSE,
        database=SF_DATABASE, schema=SF_SCHEMA, ocsp_fail_open=True,
    )


def _run_sql(conn, sql):
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchmany(20)
    if not rows:
        return "Query returned no results."
    cols = [d[0] for d in cur.description]
    lines = [" | ".join(cols), "-" * 60]
    for row in rows:
        lines.append(" | ".join(str(v) for v in row))
    return "\n".join(lines)


def query_cortex(question: str) -> str:
    if not question:
        return "No question provided."
    conn = None
    try:
        conn = _connect()
        token = conn.rest.token
        r = requests.post(
            f"{SF_HOST}/api/v2/cortex/analyst/message",
            headers={
                "Authorization": f'Snowflake Token="{token}"',
                "Content-Type": "application/json",
                "X-Snowflake-Authorization-Token-Type": "SESSION",
            },
            json={
                "messages": [{"role": "user", "content": [{"type": "text", "text": question}]}],
                "semantic_model_file": SEMANTIC_MODEL_FILE,
            },
            timeout=90,
        )
        result = r.json()
        parts = []
        msg = result.get("message")
        if isinstance(msg, dict):
            for item in msg.get("content", []):
                if not isinstance(item, dict):
                    continue
                t = item.get("type")
                if t == "text":
                    parts.append(item["text"])
                elif t == "sql":
                    parts.append(_run_sql(conn, item["statement"]))
                elif t == "suggestions":
                    parts.append("Could you clarify? Suggestions: " + "; ".join(item.get("suggestions", [])))
        elif "error" in result:
            parts.append(f"Cortex error: {result['error']}")
        else:
            parts.append(f"Raw: {json.dumps(result)[:500]}")
        return "\n\n".join(parts) if parts else "No answer."
    except Exception as e:
        return f"Error: {e}\n{traceback.format_exc()}"
    finally:
        if conn is not None:
            conn.close()


TOOL_DEF = {
    "name": "ask_customer360",
    "description": "Query Customer360 data using natural language. Answers about customers, revenue, contracts, churn risk, health, and cities.",
    "inputSchema": {
        "type": "object",
        "properties": {"question": {"type": "string", "description": "Natural language question"}},
        "required": ["question"],
    },
}


def handle_mcp(body: dict) -> dict:
    m = body.get("method", "")
    id_ = body.get("id")
    if m == "initialize":
        return {"jsonrpc": "2.0", "id": id_, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {"listChanged": False}}, "serverInfo": {"name": "customer360-mcp", "version": "1.0.0"}}}
    if m in ("notifications/initialized", "ping"):
        return {"jsonrpc": "2.0", "id": id_, "result": {}}
    if m == "tools/list":
        return {"jsonrpc": "2.0", "id": id_, "result": {"tools": [TOOL_DEF]}}
    if m == "tools/call":
        params = body.get("params", {})
        if params.get("name") == "ask_customer360":
            answer = query_cortex(params.get("arguments", {}).get("question", ""))
            return {"jsonrpc": "2.0", "id": id_, "result": {"content": [{"type": "text", "text": answer}], "isError": False}}
        return {"jsonrpc": "2.0", "id": id_, "error": {"code": -32601, "message": f"Unknown tool: {params.get('name')}"}}
    return {"jsonrpc": "2.0", "id": id_, "error": {"code": -32601, "message": f"Unknown method: {m}"}}


CORS = [
    ("Access-Control-Allow-Origin", "*"),
    ("Access-Control-Allow-Methods", "GET, POST, OPTIONS"),
    ("Access-Control-Allow-Headers", "Content-Type, Accept, mcp-session-id"),
]


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        for k, v in CORS:
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw)

    def do_OPTIONS(self):
        self.send_response(200)
        for k, v in CORS:
            self.send_header(k, v)
        self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            self._send_json(200, {"status": "ok", "service": "customer360-mcp"})
        else:
            self._send_json(404, {"error": "Not found"})

    def do_POST(self):
        try:
            body = self._read_body()
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON"})
            return
        if self.path == "/mcp":
            self._send_json(200, handle_mcp(body))
        elif self.path == "/ask":
            q = body.get("question", "").strip()
            if not q:
                self._send_json(400, {"error": "question is required"})
                return
            self._send_json(200, {"answer": query_cortex(q)})
        else:
            self._send_json(404, {"error": "Not found"})

    def log_message(self, fmt, *args):
        print(f"  {self.address_string()} - {fmt % args}")


if __name__ == "__main__":
    PORT = 8000
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"\n✅ Customer360 MCP Server started")
    print(f"   MCP  → http://0.0.0.0:{PORT}/mcp")
    print(f"   ASK  → http://0.0.0.0:{PORT}/ask")
    print(f"   HEALTH → http://0.0.0.0:{PORT}/health\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")