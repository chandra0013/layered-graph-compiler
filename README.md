# Layered Graph Compiler (LGC)

**A deterministic, compression-first graph retrieval system for codebases.**

## What Problem Does LGC Solve?
Modern code assistance relies on Retrieval-Augmented Generation (RAG). Traditional RAG systems blindly dump entire codebases into an LLM's context window or rely on opaque semantic vector embeddings that miss structural dependencies. 

LGC solves this by parsing your codebase into an Abstract Syntax Tree (AST) and building a deterministic, multi-layered graph (L0 to L3). When querying, it uses strict multi-source Breadth-First Search (BFS) and heuristic scoring to traverse physical code boundaries. 

**The result:** You get highly accurate, grounded context that is up to 55x smaller than the raw repository—saving massive token costs while maintaining zero hallucinations.

### Visual Proof

![LGC Architecture Visualization](docs/screenshot_graph.png)
*Interactive web graph generated via `lgc visualize .`*

![LGC Benchmark Metrics](docs/screenshot_benchmark.png)
*Deterministic multi-layer benchmark results outputting exactly 55.94x compression and perfect 1.0 consistency.*

## Architecture Summary
LGC compiles codebases into four distinct layers:
1. **L0 (Raw Extraction)**: Functions, classes, and imports parsed via tree-sitter.
2. **L1 (File Summaries)**: Aggregations of L0 nodes into single-file components.
3. **L2 (Communities)**: Tightly coupled files grouped via connected-component algorithms.
4. **L3 (Overview)**: A global, compact map of the entire project.

*For deeper technical specifics, read the [Architecture Guide](docs/ARCHITECTURE.md).*

## Installation
Ensure you have Python 3.14+ installed.

```bash
git clone https://github.com/your-username/layered-graph-compiler.git
cd layered-graph-compiler
pip install -e .
```

## Quickstart
Compile the graph and query the codebase locally:

```bash
# 1. Build the deterministic L0-L3 graph
lgc build .

# 2. Query the graph (outputs grounded markdown)
lgc query . "how does query routing work" --format markdown

# 3. Generate an interactive web visualization
lgc visualize .
```
All generated artifacts are safely stored in the `lgc-out/` directory.

## Benchmark Results
On the project-local 25-question benchmark, LGC achieved **55.94x compression, 0.698 recall, 0.507 precision, and 1.0 consistency without embeddings or LLM inference.**

| Metric | Result | Description |
|---|---|---|
| **Recall** | ~70% | Finds 70% of exact targeted files/functions. |
| **Precision** | ~51% | 51% of returned nodes are direct hits. |
| **Compression** | 55.9x | Context packets are 55x smaller than raw code. |
| **Consistency** | 1.0 | 100% deterministic outputs across identical runs. |

Run the benchmarks locally on your machine:
```bash
lgc run-benchmark .
lgc export-benchmark .
```

## Commands
| Command | Description |
|---|---|
| `lgc build <path>` | Builds the multi-layered graph artifacts. |
| `lgc query <path> "<query>"` | Routes a query and returns an evidence packet. |
| `lgc visualize <path>` | Creates an HTML visualization of the L3 graph. |
| `lgc run-benchmark <path>` | Runs the local benchmarking suite. |
| `lgc export-benchmark <path>`| Exports benchmarks to a Markdown report. |
| `lgc run-multi-benchmark` | Tests compression metrics across multiple repositories. |

## Examples & Documentation
- [Sample Queries](examples/sample_queries.md)
- [Demo Steps](examples/demo_steps.md)
- [Design Decisions](docs/DESIGN_DECISIONS.md)
- [Benchmarking Methodology](docs/BENCHMARKING.md)

## Limitations
LGC is a powerful, deterministic tool, but it is not a silver bullet.
- **Keyword Dependence**: Because LGC does not use embeddings, semantic synonyms (e.g., "auth" vs "login") may fail to find initial seed nodes if the strings do not overlap.
- **Deep Recall Cutoff**: To maintain high token compression, graph expansion is strictly bounded. Tracing pipelines across 4+ structural hops is often prematurely pruned.
- **Python Only**: The AST extraction layer is currently tailored to Python.

## Roadmap
See [ROADMAP.md](docs/ROADMAP.md) for future plans, including intelligent traversal algorithms and optional embedding layers for alias resolution.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
