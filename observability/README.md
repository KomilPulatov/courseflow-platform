# Observability stack

Configs consumed by the docker-compose services in [`docs/09-deployment.md`](../docs/09-deployment.md).
The backend ships traces, metrics, and logs over OTLP/gRPC to the OpenTelemetry
Collector, which fans out to Prometheus, Tempo, and Loki.

## Files

| File | Service | Purpose |
|---|---|---|
| `otel-collector-config.yaml` | otel-collector | OTLP receivers + Prom/Tempo/Loki exporters |
| `prometheus.yml` | prometheus | Scrape config — pulls metrics from the collector |
| `grafana/datasources/datasources.yml` | grafana | Auto-provision Prom + Tempo + Loki datasources |
| `grafana/dashboards/` | grafana | Drop dashboard JSONs here (provisioned by Grafana) |

## Running locally without the full stack

If `OTEL_EXPORTER_OTLP_ENDPOINT` is empty (the default in `.env.example`), the
backend installs a no-op TracerProvider — there is no requirement to run the
collector for local development or `pytest`. Set the env var to
`http://otel-collector:4317` once the compose stack is up to start exporting.
