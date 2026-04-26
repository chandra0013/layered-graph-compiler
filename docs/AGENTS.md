# AGENTS.md

You are building an open-source Layered Graph Compiler.

Goal:
Convert a messy project folder into a multi-layer knowledge graph that reduces repeated LLM token usage.

Do not build a generic RAG app.
Do not make hybrid vector retrieval the default.
Default architecture is compression-first layered graph compilation.

Core layers:
- L0: raw evidence graph
- L1: file/module graph
- L2: subsystem/community graph
- L3: tiny project overview graph

Rules:
- Every extracted fact must have provenance.
- Every generated summary must keep support_node_ids.
- Never create unsupported claims.
- If source support is missing, mark the relation AMBIGUOUS.
- Use Pydantic schemas for all data contracts.
- Write tests for every module before expanding features.

Commands:
- Run tests with: pytest
- Run lint with: ruff check .
