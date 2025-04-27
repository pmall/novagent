import json
from pathlib import Path
from datetime import datetime, timezone


class DummyTraceLogger:
    def __call__(self, messages: list[dict], response: dict) -> None:
        pass


class JsonTraceLogger:
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


class OpenInferenceTraceLogger:
    def __init__(
        self,
        endpoint: str = "http://localhost:4318/v1/traces",
        headers: dict = None,
        project_name: str = "novagent",
    ):
        try:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                OTLPSpanExporter,
            )
            from opentelemetry.sdk.resources import Resource
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor
            from opentelemetry import trace
        except ImportError as e:
            raise ImportError(
                "OpenTelemetry packages are missing. Install them with:\n"
                "pip install opentelemetry-sdk opentelemetry-exporter-otlp"
            ) from e

        resource = Resource(attributes={"service.name": project_name})

        exporter = OTLPSpanExporter(endpoint=endpoint, headers=headers)

        provider = TracerProvider(resource=resource)
        span_processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(span_processor)
        trace.set_tracer_provider(provider)
        self.tracer = trace.get_tracer(project_name)

    def __call__(self, messages: list[dict], response: dict):
        with self.tracer.start_as_current_span("novagent.model_call") as span:
            span.set_attribute("messages", json.dumps(messages))
            span.set_attribute("response", json.dumps(response))
