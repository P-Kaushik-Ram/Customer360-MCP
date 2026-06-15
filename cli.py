#!/usr/bin/env python3
"""Customer360 CLI — MCP client for the local Dockerized MCP server."""

import sys
import json
import itertools
import requests

MCP_URL = "http://localhost:8000/mcp"
_ids = itertools.count(1)


def rpc(method, params=None):
    payload = {"jsonrpc": "2.0", "id": next(_ids), "method": method}
    if params is not None:
        payload["params"] = params
    r = requests.post(MCP_URL, json=payload, timeout=120)
    r.raise_for_status()
    return r.json()


def main():
    print("Customer360 CLI — MCP client")
    print(f"Connecting to {MCP_URL} ...")

    init = rpc("initialize")
    if "error" in init:
        print("Initialize failed:", init["error"])
        sys.exit(1)
    server_info = init["result"]["serverInfo"]
    print(f"Connected: {server_info['name']} v{server_info['version']}\n")

    tools = rpc("tools/list")["result"]["tools"]
    print("Available tools:")
    for t in tools:
        print(f"  - {t['name']}: {t['description']}")
    print()

    print("Ask a question (or 'quit' to exit)\n")
    while True:
        question = input("you> ").strip()
        if not question:
            continue
        if question.lower() in ("quit", "exit"):
            break

        resp = rpc("tools/call", {
            "name": "ask_customer360",
            "arguments": {"question": question},
        })

        if "error" in resp:
            print("error>", resp["error"])
            continue

        for item in resp["result"]["content"]:
            if item.get("type") == "text":
                print(f"\nbot> {item['text']}\n")


if __name__ == "__main__":
    main()