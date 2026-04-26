import json
import urllib.error
import urllib.request

from lgc.models.base import ModelUnavailableError, SummaryModel


class OllamaSummaryModel(SummaryModel):
    def __init__(self, model: str, base_url: str, timeout_seconds: int = 30) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def summarize(self, prompt: str, max_tokens: int = 512) -> str:
        payload = json.dumps(
            {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": max_tokens},
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
        except (OSError, urllib.error.URLError, TimeoutError) as error:
            raise ModelUnavailableError(str(error)) from error

        return str(data.get("response", "")).strip()
