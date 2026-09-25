#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RAGFlow 检索辅助脚本（通过 MCP evaluation-review → ragflow_retrieval）。

示例：
  python3 scripts/ragflow-retrieval.py --question "资产评估报告 正文 应当包括"
  python3 scripts/ragflow-retrieval.py -q "评估说明 资产评估说明 应当包括" \
      --documents bb8d1e804e7c11f18ee0afe6a78982c3 --keyword --threshold 0.1
  python3 scripts/ragflow-retrieval.py -q "折现率" --documents bc2bd3ea4e7c11f18ee0afe6a78982c3 --json
"""
import argparse, json, sys, urllib.request

URL = "http://10.1.1.230:9382/mcp"
HEADERS = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
DEFAULT_DATASET = "d6edbed44e7a11f18ee0afe6a78982c3"  # 评估法及准则


def rpc(method, params=None, rid=1):
    payload = {"jsonrpc": "2.0", "id": rid, "method": method}
    if params is not None:
        payload["params"] = params
    req = urllib.request.Request(URL, data=json.dumps(payload).encode(), headers=HEADERS, method="POST")
    with urllib.request.urlopen(req, timeout=180) as resp:
        raw = resp.read().decode("utf-8")
    if "\ndata:" in raw or raw.lstrip().startswith("event:"):
        data = [ln[5:].strip() for ln in raw.splitlines() if ln.startswith("data:")]
        raw = data[-1] if data else raw
    return json.loads(raw)


def retrieve(args):
    arguments = {
        "question": args.question,
        "page_size": args.page_size,
        "page": args.page,
        "similarity_threshold": args.threshold,
        "vector_similarity_weight": args.vector_weight,
        "keyword": args.keyword,
    }
    if args.dataset:
        arguments["dataset_ids"] = args.dataset
    if args.documents:
        arguments["document_ids"] = args.documents
    res = rpc("tools/call", {"name": "ragflow_retrieval", "arguments": arguments}, 2)
    text = "".join(c.get("text", "") for c in res.get("result", {}).get("content", []) if c.get("type") == "text")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw": text, "error": res.get("error")}


def main():
    ap = argparse.ArgumentParser(description="RAGFlow MCP retrieval helper")
    ap.add_argument("-q", "--question", required=True)
    ap.add_argument("--dataset", action="append", help="dataset_ids（可重复；默认准则数据集）")
    ap.add_argument("--documents", action="append", help="document_ids（可重复，用于锁定文档）")
    ap.add_argument("--page-size", type=int, default=10)
    ap.add_argument("--page", type=int, default=1)
    ap.add_argument("--threshold", type=float, default=0.2)
    ap.add_argument("--vector-weight", type=float, default=0.3)
    ap.add_argument("--keyword", action="store_true")
    ap.add_argument("--json", action="store_true", help="输出原始 JSON")
    ap.add_argument("--chars", type=int, default=600, help="每条片段打印字符数")
    args = ap.parse_args()
    if not args.dataset:
        args.dataset = [DEFAULT_DATASET]

    result = retrieve(args)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    for chunk in result.get("chunks", []):
        sim = chunk.get("similarity", 0)
        pos = chunk.get("positions") or []
        page = pos[0][0] if pos and isinstance(pos[0], list) else "?"
        print("=" * 78)
        print(f"{chunk.get('document_name')}  sim={sim:.3f}  page={page}")
        print((chunk.get("content") or "").strip()[: args.chars])
    print("=" * 78)
    print(f"命中 {len(result.get('chunks', []))} 条")


if __name__ == "__main__":
    sys.exit(main())
