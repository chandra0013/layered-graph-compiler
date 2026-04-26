from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from lgc import __version__
from lgc.artifacts import write_packet
from lgc.benchmark.run import run_benchmark
from lgc.benchmark.tokens import run_token_benchmark
from lgc.benchmark.multi_run import run_multi_benchmark
from lgc.export.html import HtmlGraphExporter
from lgc.pipeline import build_project, extract_project, inspect_project, query_project, scan_project
from lgc.query.render import MarkdownRenderer
from lgc.storage.paths import ArtifactPaths

app = typer.Typer(
    name="lgc",
    help="Layered Graph Compiler command line interface.",
    invoke_without_command=True,
    no_args_is_help=True,
)
console = Console()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option("--version", help="Show the installed LGC version.", is_eager=True),
    ] = False,
) -> None:
    if version:
        console.print(__version__)
        raise typer.Exit()


@app.command()
def scan(root: Annotated[str, typer.Argument(help="Project root to scan.")]) -> None:
    """Walk a project and write artifact_manifest.jsonl."""

    rows = scan_project(Path(root))
    console.print_json(data={"artifacts": len(rows), "output": "artifact_manifest.jsonl"})


@app.command()
def extract(root: Annotated[str, typer.Argument(help="Project root to extract.")]) -> None:
    """Extract L0 graph facts from supported files."""

    nodes, edges = extract_project(Path(root))
    console.print_json(data={"l0_nodes": len(nodes), "l0_edges": len(edges)})


@app.command()
def build(root: Annotated[str, typer.Argument(help="Project root to build.")]) -> None:
    """Build L0, L1, L2, and L3 deterministic graph artifacts."""

    console.print_json(data=build_project(Path(root)))


@app.command()
def query(
    root: Annotated[str, typer.Argument(help="Project root to query.")],
    question: Annotated[str, typer.Argument(help="Question to route into the graph.")],
    max_tokens: Annotated[int, typer.Option(help="Maximum evidence packet token budget.")] = 2048,
    output_format: Annotated[
        str,
        typer.Option("--format", help="Output format: json or markdown."),
    ] = "json",
) -> None:
    """Return an evidence packet JSON, not a generated answer."""

    root_path = Path(root).resolve()
    packet = query_project(root_path, question, max_tokens=max_tokens)
    write_packet(ArtifactPaths(root_path).evidence_packet, packet)
    if output_format == "json":
        console.print_json(data=packet.model_dump(mode="json"))
        return
    if output_format == "markdown":
        console.print(MarkdownRenderer().render(packet))
        return
    raise typer.BadParameter("--format must be json or markdown")


@app.command()
def inspect(root: Annotated[str, typer.Argument(help="Project root to inspect.")]) -> None:
    """Show counts for existing compiler artifacts."""

    console.print_json(data=inspect_project(Path(root)))


@app.command()
def visualize(root: Annotated[str, typer.Argument(help="Project root to visualize.")]) -> None:
    """Write lgc-out/graph.html for the compiled graph."""

    root_path = Path(root).resolve()
    if not ArtifactPaths(root_path).nodes_l3.exists():
        build_project(root_path)
    output = HtmlGraphExporter().export(root_path)
    console.print_json(data={"output": str(output)})


@app.command()
def benchmark(root: Annotated[str, typer.Argument(help="Project root to benchmark.")]) -> None:
    """Estimate token compression across graph layers."""

    root_path = Path(root).resolve()
    if not ArtifactPaths(root_path).nodes_l3.exists():
        build_project(root_path)
    metrics = run_token_benchmark(root_path)
    table = Table(title="Token Benchmark")
    table.add_column("metric")
    table.add_column("tokens")
    for key in [
        "raw_source_tokens",
        "l0_graph_tokens",
        "l1_tokens",
        "l2_tokens",
        "l3_tokens",
        "evidence_packet_tokens",
    ]:
        table.add_row(key, str(metrics[key]))
    console.print(table)
    console.print_json(data=metrics)


@app.command("run-benchmark")
def run_benchmark_command(
    root: Annotated[str, typer.Argument(help="Project root to benchmark.")],
    questions: Annotated[
        Path | None,
        typer.Option("--questions", help="Path to benchmark_questions.json."),
    ] = None,
    max_tokens: Annotated[int, typer.Option(help="Maximum evidence packet token budget.")] = 2048,
) -> None:
    """Run accuracy and compression benchmark questions."""

    root_path = Path(root).resolve()
    report = run_benchmark(root_path, questions, max_tokens=max_tokens)

    # Summary
    console.print()
    summary = Table(title="Benchmark Summary")
    summary.add_column("metric")
    summary.add_column("value")
    summary.add_row("questions", str(report["question_count"]))
    summary.add_row("raw_tokens", str(report["raw_tokens"]))
    summary.add_row("lgc_tokens", str(round(report["lgc_tokens"])))
    summary.add_row("compression", f'{report["compression"]}x')
    summary.add_row("recall", str(report["recall"]))
    summary.add_row("precision", str(report["precision"]))
    console.print(summary)

    # Per-difficulty breakdown
    by_diff = report.get("by_difficulty", {})
    if by_diff:
        console.print()
        diff_table = Table(title="Per-Difficulty Metrics")
        diff_table.add_column("difficulty")
        diff_table.add_column("count")
        diff_table.add_column("recall")
        diff_table.add_column("precision")
        diff_table.add_column("avg_tokens")
        diff_table.add_column("avg_compression")
        for level in ("easy", "medium", "hard"):
            entry = by_diff.get(level)
            if entry:
                diff_table.add_row(
                    level,
                    str(entry["count"]),
                    str(entry["recall"]),
                    str(entry["precision"]),
                    str(entry["avg_evidence_tokens"]),
                    f'{entry["avg_compression"]}x' if entry["avg_compression"] else "N/A",
                )
        console.print(diff_table)

    # Baselines
    baselines = report.get("baselines", {})
    if baselines:
        console.print()
        base_table = Table(title="Baseline Comparison")
        base_table.add_column("method")
        base_table.add_column("avg_tokens")
        base_table.add_column("compression")
        for name, entry in baselines.items():
            compression = entry.get("compression")
            base_table.add_row(
                name,
                str(entry["avg_tokens"]),
                f"{compression}x" if compression else "N/A",
            )
        # Add LGC row
        base_table.add_row(
            "[bold]LGC[/bold]",
            f'[bold]{round(report["lgc_tokens"])}[/bold]',
            f'[bold]{report["compression"]}x[/bold]',
        )
        console.print(base_table)

    # Consistency
    consistency = report.get("consistency", {})
    if consistency:
        console.print()
        console.print(
            f'Consistency: {consistency["identical_questions"]}/{consistency["total_questions"]} '
            f'identical across {consistency["runs"]} runs '
            f'(score: {consistency["consistency_score"]})'
        )

    console.print()
    console.print_json(
        data={
            "benchmark_report": str(ArtifactPaths(root_path).benchmark_report),
            "compression": report["compression"],
            "recall": report["recall"],
            "precision": report["precision"],
            "consistency_score": consistency.get("consistency_score"),
        }
    )



@app.command("run-multi-benchmark")
def run_multi_benchmark_command(
    repos: Annotated[list[str], typer.Argument(help="List of project roots to benchmark.")],
) -> None:
    """Run benchmark across multiple repositories."""
    result = run_multi_benchmark(repos)
    console.print_json(data=result)


@app.command("export-benchmark")
def export_benchmark_command(
    root: Annotated[str, typer.Argument(help="Project root to export benchmark for.")] = ".",
) -> None:
    """Export benchmark report to markdown."""
    from lgc.benchmark.export_md import export_benchmark_to_markdown
    root_path = Path(root).resolve()
    out_path = export_benchmark_to_markdown(root_path)
    console.print(f"Exported benchmark report to {out_path}")

if __name__ == "__main__":
    app()
