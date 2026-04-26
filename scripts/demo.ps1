$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Layered Graph Compiler (LGC) Demo Script" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/5] Building the deterministic graph layers (L0-L3)..." -ForegroundColor Yellow
lgc build .
Write-Host "Done.`n" -ForegroundColor Green

Write-Host "[2/5] Querying the graph (no embeddings, no LLMs)..." -ForegroundColor Yellow
Write-Host "Query: 'how does query routing work'`n"
lgc query . "how does query routing work" --format markdown
Write-Host "Done.`n" -ForegroundColor Green

Write-Host "[3/5] Running internal benchmark suite..." -ForegroundColor Yellow
lgc run-benchmark .
Write-Host "Done.`n" -ForegroundColor Green

Write-Host "[4/5] Exporting benchmark results to Markdown..." -ForegroundColor Yellow
lgc export-benchmark .
Write-Host "Exported to lgc-out/BENCHMARK_REPORT.md`n" -ForegroundColor Green

Write-Host "[5/5] Generating interactive L3 architecture visualization..." -ForegroundColor Yellow
lgc visualize .
Write-Host "Visualization saved to lgc-out/graph.html`n" -ForegroundColor Green

Write-Host "Demo complete! Check the lgc-out/ directory for generated artifacts." -ForegroundColor Cyan
