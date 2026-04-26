# Sample Queries

LGC uses a built-in deterministic query classifier that interprets the intent behind your questions to route them to the correct graph layers (L0-L3). 

Here are some sample queries to test against any repository compiled with LGC.

## 1. Implementation Localization (L0/L1)
These queries map directly to specific file components or functions.
- `where is MarkdownRenderer defined`
- `which file contains ArtifactPaths`
- `find the ProvenanceGuard class`
- `where is estimate_tokens defined`

## 2. Architecture & Subsystems (L2/L3)
These queries require an understanding of how multiple components fit together and are routed to higher-level graph layers.
- `what validation guards exist in the system`
- `describe the L1 aggregation process`
- `explain how community detection works in L2 aggregation`
- `what Pydantic schemas define the domain model`

## 3. Flow Tracing
These queries traverse structural edges (calls, imports) across boundaries.
- `how does query routing work`
- `how are evidence packets built`
- `trace the full pipeline from scan to evidence packet`
- `how does the system enforce provenance from L0 to L3`

## Example Usage
To test one of these queries on the LGC repository itself, run:
```bash
lgc query . "how does query routing work" --format markdown
```
