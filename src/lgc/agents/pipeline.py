import json
from pathlib import Path

from lgc.agents.base import ValidationContext, report_dict
from lgc.agents.compression_validator import CompressionValidator
from lgc.agents.ontology_agent import OntologyAgent
from lgc.agents.parser_agent import ParserAgent
from lgc.agents.provenance_validator import ProvenanceValidator
from lgc.domain.schemas import Edge, Node
from lgc.storage.paths import ArtifactPaths


def run_validations(
    root: Path,
    nodes_l0: list[Node],
    edges_l0: list[Edge],
    nodes_l1: list[Node],
    nodes_l2: list[Node],
    nodes_l3: list[Node],
) -> dict[str, object]:
    context = ValidationContext(
        nodes_l0=nodes_l0,
        edges_l0=edges_l0,
        nodes_l1=nodes_l1,
        nodes_l2=nodes_l2,
        nodes_l3=nodes_l3,
    )
    reports = [
        ParserAgent().validate(context),
        OntologyAgent().validate(context),
        ProvenanceValidator().validate(context),
        CompressionValidator().validate(context),
    ]
    payload = report_dict(reports)
    paths = ArtifactPaths(root)
    paths.ensure_out_dir()
    paths.validation_report.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload
