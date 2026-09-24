# EvaluationReviewIssues

评估报告复核相关的知识库与检索工具配置。

## 项目内容

| 路径 | 说明 |
| --- | --- |
| `.vscode/mcp.json` | VS Code MCP 服务器配置（连接内网 RAGFlow 知识库） |
| `docs/datasets.md` | 可用数据集清单与检索说明 |

## MCP 服务器

项目通过 VS Code 的 MCP（Model Context Protocol）接入内网 RAGFlow 知识库，用于检索资产评估准则、法规与专家指引原文。

- **地址**：`http://10.1.1.230:9382/mcp`
- **服务端**：`ragflow-mcp-server` v1.19.0（HTTP Streamable，无鉴权）
- **协议版本**：`2025-06-18`
- **配置文件**：`.vscode/mcp.json`，服务器名 `evaluation-review`

启动方式：打开 `.vscode/mcp.json` 点击 CodeLens 的 **Start**，或执行命令面板 `MCP: List Servers` 选择 `evaluation-review`。

## 数据集

详见 [`docs/datasets.md`](docs/datasets.md)。

当前主要数据集：

| 名称 | Dataset ID | 内容 |
| --- | --- | --- |
| 评估法及准则 | `d6edbed44e7a11f18ee0afe6a78982c3` | 资产评估准则、执业准则与专家指引 |

## 快速验证

```bash
# 检查服务连通性
curl -sS -X POST http://10.1.1.230:9382/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"check","version":"1.0.0"}}}'
```