# PagerDuty Client Module

This module provides a PagerDuty client for sending events via Events API v2.

## Installation

Install from Artifact Registry:

```bash
pip install pagerduty-client --extra-index-url https://us-central1-python.pkg.dev/mai-project-a26f/mai-python-repo/simple/
```

## Usage

### Basic Usage

```python
from mai_util.pagerduty_client import PagerDutyClient

# Create a client with custom routing key secret
client = PagerDutyClient(
    gcp_project="mai-project-a26f",
    routing_key_secret="MY_ROUTING_KEY_SECRET"
)

# Trigger an incident
incident_key = client.trigger_incident(
    summary="Service is down",
    severity="critical",
    source="my-service",
    custom_details={"error": "Database connection failed"},
    dedup_key="unique-incident-id"
)

# Resolve an incident
client.resolve_incident(incident_key, summary="Issue resolved")
```

### Using Pre-configured Alert Client

```python
from mai_util.pagerduty_client import PagerDutyAlertClient

# Pre-configured for validation alerts
client = PagerDutyAlertClient(gcp_project="mai-project-a26f")

# Trigger validation failure incident
incident_key = client.trigger_incident(
    summary="Validation failed for clients: 844, 426",
    severity="critical",
    source="mai-spark-validation",
    custom_details={
        "channel": "DATA_IMPORT_CRITICAL",
        "client_ids": ["844", "426"],
        "validation_type": "blocking"
    }
)
```

### Custom Client Subclass

```python
from mai_util.pagerduty_client import PagerDutyClient

class MyCustomPagerDutyClient(PagerDutyClient):
    """Custom client for your specific use case."""

    ROUTING_KEY_SECRET = "MY_CUSTOM_ROUTING_KEY"

# Use it
client = MyCustomPagerDutyClient(gcp_project="mai-project-a26f")
client.trigger_incident(summary="Custom alert", severity="warning")
```

## Severity Levels

- `critical` - Highest priority, pages immediately
- `error` - High priority, pages based on policy
- `warning` - Medium priority, creates incident but doesn't page
- `info` - Low priority, informational only

## Requirements

- Python >=3.11,<3.13
- Google Cloud Secret Manager access
- PagerDuty service with Events API v2 integration

## Development

### Running Tests

```bash
uv run pytest
# or
pytest
```

### Building

```bash
./scripts/build.sh
```

### Publishing

```bash
./scripts/publish.sh [VERSION]
```
