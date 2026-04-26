# Demo Steps

This guide demonstrates the complete workflow for compiling and querying a repository using the Layered Graph Compiler (LGC).

## 1. Setup
Ensure you are in the root directory of a Python project (you can use the LGC repository itself for this demo).

## 2. Compile the Graph
First, extract the AST and build the hierarchical graph layers (L0 through L3). This process is fully deterministic and entirely local.
```bash
lgc build .
```
*Artifacts will be written to the `lgc-out/` directory.*

## 3. Query the Graph
Route a question into the compiled graph to retrieve a grounded, highly compressed evidence packet. 
```bash
lgc query . "how does query routing work" --format markdown
```
*Unlike traditional LLM workflows, LGC does not hallucinate answers. The output is a deterministic rendering of the exact graph nodes retrieved.*

## 4. Visualize the Architecture
Generate an interactive HTML visualization of the L3 overview graph.
```bash
lgc visualize .
```
*Open `lgc-out/graph.html` in your web browser to explore.*

## 5. Benchmark the System
Evaluate LGC's compression, precision, and recall against an internal suite of 25 benchmark questions.
```bash
lgc run-benchmark .
```

## 6. Export the Benchmark Report
Format the raw JSON benchmark data into a human-readable Markdown report.
```bash
lgc export-benchmark .
```
*View the full results in `lgc-out/BENCHMARK_REPORT.md`.*
