import json
from pathlib import Path
from datetime import datetime, timezone


class DummyLogger:
    def __call__(self, messages: list[dict], response: dict) -> None:
        pass


class JsonLineLogger:
    def __init__(
        self, path: str | Path, overwrite: bool = False, timezone=timezone.utc
    ):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if overwrite and self.path.exists():
            self.path.unlink()  # delete the existing log file

        self.timezone = timezone

    def __call__(self, messages: list[dict], response: dict):
        entry = {
            "timestamp": datetime.now(self.timezone).isoformat(),
            "messages": messages,
            "response": response,
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
