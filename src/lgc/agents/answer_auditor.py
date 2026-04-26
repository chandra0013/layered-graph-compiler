from lgc.agents.base import ValidationReport


class AnswerAuditor:
    name = "answer_auditor"

    def validate(self, answer: str, evidence_node_ids: list[str]) -> ValidationReport:
        errors: list[str] = []
        sentences = [sentence.strip() for sentence in answer.split(".") if sentence.strip()]
        for sentence in sentences:
            if not any(node_id in sentence for node_id in evidence_node_ids):
                errors.append(f"Ungrounded sentence: {sentence}")
        return ValidationReport(
            name=self.name,
            passed=not errors,
            errors=errors,
            metrics={"sentence_count": len(sentences)},
        )
