# LGC Architecture

The Layered Graph Compiler (LGC) is designed around a strictly deterministic, multi-layered graph extraction pipeline. 

## The L0 → L3 Graph Layers

LGC compiles a codebase into four distinct layers of abstraction:

1. **L0 (Raw Extraction)**: The foundational layer. An AST parser extracts functions, classes, methods, imports, and markdown documents directly from the source. Edges represent direct `CALLS`, `CONTAINS`, or `IMPORTS` relationships.
2. **L1 (File & Module Summaries)**: Groups L0 nodes by their physical file. This layer provides a file-level summary and aggregates symbol counts.
3. **L2 (Subsystems & Communities)**: Uses connected-component algorithms to group tightly coupled L1 files into logical subsystems or communities.
4. **L3 (Project Overview)**: A highly compacted, top-level graph representing the entire project structure, optimized for rapid context injection.

## Query Flow

When a user asks a question, LGC processes it without invoking external LLMs:

1. **Intent Classification**: The query is mapped to an intent (`IMPLEMENTATION_LOCALIZATION`, `ARCHITECTURE`, `FLOW_TRACING`, etc.) based on keyword patterns and phrase structures.
2. **Layer Routing**: Based on the intent, the system determines which graph layers (L0-L3) are relevant. Implementation queries route to L0/L1; architecture queries route to L2/L3.
3. **Seed Selection & Scoring**: Candidate nodes are scored against the query terms, layer priority, structural importance (e.g., cross-module bridges), and path matches.
4. **Graph Traversal & Expansion**: A multi-source Breadth-First Search (BFS) explores the neighborhood around the top seed nodes. For architecture/flow queries, it traverses down the `support_node_ids` chain to pull in grounded evidence.
5. **Noise Filtering**: Aggressive filters prune irrelevant `external_symbol` nodes, generic labels without term overlaps, and distant low-confidence nodes.
6. **Pruning & Evidence Packet**: The remaining subgraph is strictly pruned to fit within the `max_tokens` budget, yielding a deterministic `EvidencePacket`.

## Why Deterministic Matters

LGC relies on AST parsing and graph traversal rather than vector embeddings or LLM-based reasoning for retrieval. 

**Advantages:**
- **Zero Hallucinations**: Evidence packets only contain exact structural paths and code facts that exist in the codebase.
- **Measurable & Repeatable**: A query run 1,000 times will return the exact same nodes 1,000 times, allowing for rigorous benchmarking.
- **Speed & Efficiency**: Graph traversal is incredibly fast and runs entirely locally without GPU requirements or API costs.
