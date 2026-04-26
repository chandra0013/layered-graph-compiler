# LGC Roadmap

The Layered Graph Compiler is currently in a robust, deterministic state. The graph extraction and retrieval pipeline operates with high compression and perfect consistency. 

However, there are clear limitations inherent to the current design that dictate our future direction.

## Current Limitations

- **Hard Recall is Low**: Multi-hop reasoning queries (e.g., tracing a pipeline end-to-end) often fail to retrieve the complete set of required nodes. The graph traversal currently uses conservative depth limits (depth 1 or 2) to maintain precision, which cuts off distant components.
- **Keyword-Bound Routing**: Because the system relies entirely on string matching, stemming, and prefixes, queries using domain synonyms (e.g., "authentication" vs "login") will fail if the exact terms don't appear in the graph node labels or metadata.
- **Single-Language Extraction**: Currently, AST extraction is deeply tied to Python.

## Future Plans

### 1. Better Graph Traversal
Instead of blind BFS, we plan to implement more intelligent traversal algorithms like PageRank-weighted walks or constrained shortest-path expansions. This will allow the system to follow deep architectural traces without blowing up the token budget, directly addressing the "hard recall" gap.

### 2. Multi-Repo Validation
The system currently performs exceptionally well on its own codebase. We must validate and tune the graph importance algorithms (e.g., cross-module hub scoring) across small, medium, and large external codebases to ensure generalized performance.

### 3. Optional Embeddings
While our core advantage is deterministic, explainable retrieval, we recognize that semantic mapping is necessary for synonym resolution. In the future, we may introduce an *optional* embedding layer specifically for resolving node aliases or query intent mapping. **This will not be the default.** The foundation of LGC will always remain deterministically verifiable graph compilation.
