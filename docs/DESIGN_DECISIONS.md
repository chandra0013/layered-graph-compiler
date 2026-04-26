# Design Decisions

This document outlines the core technical philosophies and design tradeoffs made while building the Layered Graph Compiler (LGC).

## Why Deterministic Retrieval?
In traditional Retrieval-Augmented Generation (RAG) systems, context is gathered through semantic similarity (embeddings) or generative agents (LLMs). While flexible, these approaches introduce unpredictability. LGC opts for a purely **deterministic retrieval pipeline** based on Abstract Syntax Tree (AST) extraction and graph traversal. 
- **Auditable & Debuggable**: If a node is missing from the output, it is 100% traceable back to the routing logic or graph structure, not a floating-point distance metric.
- **Zero Hallucination Grounding**: Because the system only uses extracted nodes and explicit structural edges (`CALLS`, `CONTAINS`, `IMPORTS`), the output context is guaranteed to represent the actual, literal state of the codebase.

## Why No Embeddings By Default?
Embeddings are powerful for synonym mapping, but they obscure architectural boundaries. In codebases, physical structure (files, directories, call graphs) matters more than semantic textual similarity. 
By avoiding embeddings, we:
1. Ensure the system remains extremely fast and entirely local without GPU or heavy dependency requirements.
2. Force the retrieval algorithm to understand the actual module structure rather than relying on "lucky" vector matches.

## Why Layered Graph Compression (L0 → L3)?
Feeding an entire repository into a prompt destroys the signal-to-noise ratio and incurs massive token costs. LGC solves this by building a pyramid of abstraction:
- **L0 (Raw AST)**: Exhaustive but massive.
- **L1 (File Level)**: Condenses L0 into file summaries.
- **L2 (Subsystems)**: Condenses L1 into connected components.
- **L3 (Overview)**: A global view of the project.
This layering allows high-level architectural queries to ingest L2/L3 nodes (providing a macro understanding) and trace down only the relevant branches to L0, preserving context while saving tens of thousands of tokens.

## Why Seed-Stage Noise Filtering Matters
During development, we discovered that simple keyword overlap scoring is heavily biased toward text-dense files, such as `test_*.py` files or verbose documentation paragraphs. These nodes artificially hoarded the top "seed" spots, starving the actual implementation nodes and crippling recall. By actively filtering generic labels, test code, and doc-fragments at the seed selection stage, LGC ensures the graph expansion starts from structurally meaningful components, dramatically improving final recall.

## Compression vs. Recall Tradeoff
LGC currently operates at an extreme compression ratio (~55.9x). This means we discard 98% of the codebase to build the evidence packet. 
- **The Tradeoff**: Aggressive pruning limits the depth of graph traversal. While this guarantees high precision and low token costs, it intentionally caps "Hard Recall" (e.g., answering multi-hop pipeline traces), as distant nodes are explicitly pruned to maintain the budget constraint.

## Current Limitations
1. **Keyword/Lexical Dependence**: Without embeddings, the initial multi-source BFS seeds rely on literal string matching (with stemming). Synonyms (e.g., "auth" vs "login") may fail to find optimal seeds.
2. **Hard Multi-Hop Recall**: Resolving deep architectural questions across 4+ subsystem boundaries struggles due to our strict graph expansion bounds.
3. **Single Language Extractor**: L0 extraction is currently optimized specifically for Python codebases using tree-sitter.
