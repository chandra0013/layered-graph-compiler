# Benchmarking LGC

The Layered Graph Compiler (LGC) includes a comprehensive, deterministic benchmarking suite designed to measure retrieval performance and token compression without relying on embeddings or LLM evaluations.

## How the Benchmark Works

`lgc run-benchmark <repo-path>` performs the following steps:
1. **Build**: Scans the project, extracts the L0 graph, and builds the L1-L3 layers.
2. **Execute Queries**: Runs a predefined set of questions from `benchmark_questions.json` against the compiled graph.
3. **Evaluate**: Measures the exact number of tokens in the returned `evidence_packet` and checks if the expected nodes/layers are present.
4. **Compare Baselines**: Runs identical queries against multiple deterministic baselines to provide context.
5. **Consistency Check**: Runs the entire suite 3 times to ensure 1.0 determinism (identical node IDs returned every time).

## Metrics Explained

### Recall
**What it measures**: Did the system find what we were looking for?
Recall is the percentage of `expected_nodes` and `expected_layers` that were successfully included in the returned evidence packet. 
- *A recall of 1.0 means all expected facts were found.*

### Precision
**What it measures**: How much noise was included alongside the correct answers?
Precision is the ratio of relevant nodes to the total number of nodes returned. 
- *A precision of 0.30 means 30% of the returned nodes directly matched expected targets.* 
- In graph retrieval, perfect precision is rare (and often undesirable) because the system intentionally pulls in connected context (neighbors, parent files, subsystem summaries) that aren't explicitly requested but are crucial for understanding.

### Compression
**What it measures**: How much token context was saved compared to the raw repository?
Compression is `raw_repository_tokens / evidence_packet_tokens`.
- *A compression of 50x means the evidence packet is 50 times smaller than sending the whole codebase to an LLM.*

## Limitations

- **Keyword and Path Dependent**: LGC's multi-source BFS uses stemming and prefix-matching, but fundamentally relies on query terms existing in node labels, metadata, or paths. Queries using entirely different synonyms (e.g. "auth" when the code uses "login") may fail to find seed nodes.
- **Hard Recall is Lower**: While easy (entity lookup) and medium (subsystem flow) queries have strong recall, hard queries (multi-hop architecture overviews) have lower recall and precision. The system currently caps neighborhood expansion to avoid token explosions, which can cut off distant paths.
- **Deterministic Bounds**: Because we do not use embeddings (to maintain speed and explainability), semantic intent matching is restricted to the heuristic rules defined in the query classifier.
