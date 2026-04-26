import json
from pathlib import Path

from lgc.benchmark.questions import evaluate_answer, load_questions
from lgc.domain.enums import Layer, TruthLabel
from lgc.domain.schemas import EvidencePacket, Node


def test_load_questions_from_json(tmp_path) -> None:
    path = tmp_path / "benchmark_questions.json"
    path.write_text(
        json.dumps([{"question": "where auth", "expected_nodes": ["auth.py"], "type": "implementation"}]),
        encoding="utf-8",
    )

    questions = load_questions(path)

    assert questions[0].question == "where auth"
    assert questions[0].expected_nodes == ["auth.py"]


def test_load_questions_with_difficulty(tmp_path) -> None:
    path = tmp_path / "benchmark_questions.json"
    path.write_text(
        json.dumps(
            [
                {
                    "question": "where auth",
                    "expected_nodes": ["auth.py"],
                    "type": "implementation",
                    "difficulty": "easy",
                },
                {
                    "question": "describe architecture",
                    "expected_layers": ["L3"],
                    "type": "overview",
                    "difficulty": "hard",
                },
            ]
        ),
        encoding="utf-8",
    )

    questions = load_questions(path)

    assert questions[0].difficulty == "easy"
    assert questions[1].difficulty == "hard"


def test_difficulty_defaults_to_medium(tmp_path) -> None:
    path = tmp_path / "benchmark_questions.json"
    path.write_text(
        json.dumps([{"question": "describe system", "type": "overview"}]),
        encoding="utf-8",
    )

    questions = load_questions(path)

    assert questions[0].difficulty == "medium"


def test_real_benchmark_questions_json_is_valid() -> None:
    """Validate that the actual benchmark_questions.json at the project root is well-formed."""
    project_root = Path(__file__).resolve().parent.parent
    path = project_root / "benchmark_questions.json"
    if not path.exists():
        return

    questions = load_questions(path)

    assert len(questions) >= 25
    valid_difficulties = {"easy", "medium", "hard"}
    for question in questions:
        assert question.question
        assert question.type
        assert question.difficulty in valid_difficulties, (
            f"Invalid difficulty '{question.difficulty}' for question: {question.question}"
        )


def test_evaluate_answer_computes_recall_and_precision() -> None:
    packet = EvidencePacket(
        query="where auth",
        nodes=[
            Node(
                id="node:auth.py:login_user",
                label="login_user",
                layer=Layer.L0,
                truth=TruthLabel.INFERRED,
                confidence=1.0,
                metadata={"path": "auth.py"},
            ),
            Node(
                id="node:other",
                label="other",
                layer=Layer.L1,
                truth=TruthLabel.INFERRED,
                confidence=1.0,
                support_node_ids=["x"],
            ),
        ],
    )

    metrics = evaluate_answer(packet, expected_nodes=["auth.py", "login_user"], expected_layers=["L0"])

    assert metrics["recall"] == 1.0
    assert 0 < metrics["precision"] <= 1.0
    assert metrics["matched_count"] == 3
