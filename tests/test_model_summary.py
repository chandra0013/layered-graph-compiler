from lgc.config import load_config
from lgc.domain.enums import Layer, TruthLabel
from lgc.domain.schemas import Node
from lgc.models.base import ModelUnavailableError, SummaryModel
from lgc.summarize.local_summary import LocalSummaryService


class FakeSummaryModel(SummaryModel):
    def summarize(self, prompt: str, max_tokens: int = 512) -> str:
        return "fake supported summary"


class UnavailableSummaryModel(SummaryModel):
    def summarize(self, prompt: str, max_tokens: int = 512) -> str:
        raise ModelUnavailableError("offline")


def test_config_defaults_to_models_disabled(tmp_path) -> None:
    assert load_config(tmp_path).models.enabled is False


def test_fake_model_summary_attaches_when_enabled() -> None:
    node = _compressed_node(["n1"])

    enriched = LocalSummaryService(FakeSummaryModel(), enabled=True).enrich_nodes([node])

    assert enriched[0].metadata["summary_text"] == "fake supported summary"


def test_summary_not_attached_without_support_node_ids() -> None:
    node = _compressed_node([])

    enriched = LocalSummaryService(FakeSummaryModel(), enabled=True).enrich_nodes([node])

    assert "summary_text" not in enriched[0].metadata


def test_unavailable_model_does_not_crash() -> None:
    node = _compressed_node(["n1"])

    enriched = LocalSummaryService(UnavailableSummaryModel(), enabled=True).enrich_nodes([node])

    assert enriched == [node]


def _compressed_node(support_node_ids: list[str]) -> Node:
    return Node(
        id="l1:file",
        label="file_summary",
        layer=Layer.L1,
        truth=TruthLabel.INFERRED,
        confidence=1.0,
        support_node_ids=support_node_ids,
        metadata={"kind": "file_summary"},
    )
