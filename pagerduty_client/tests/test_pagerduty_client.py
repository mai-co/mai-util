from unittest.mock import MagicMock, patch

import pytest
import requests

from mai_util.pagerduty_client import PagerDutyAlertClient, PagerDutyClient


@patch("mai_util.pagerduty_client.secretmanager.SecretManagerServiceClient")
@patch("mai_util.pagerduty_client.requests.post")
def test_pagerduty_client_trigger_incident(mock_post, mock_secret_client_cls):
    # Arrange secret manager to return a fake routing key
    mock_secret_client = MagicMock()
    mock_secret_client.access_secret_version.return_value.payload.data.decode.return_value = (
        "test-routing-key-123"
    )
    mock_secret_client_cls.return_value = mock_secret_client

    # Arrange requests.post to return a successful response
    mock_response = MagicMock()
    mock_response.json.return_value = {"dedup_key": "test-incident-key"}
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    # Act: instantiate and use the client
    client = PagerDutyClient(
        gcp_project="test-project", routing_key_secret="TEST_ROUTING_KEY"
    )
    incident_key = client.trigger_incident(
        summary="Test validation failure",
        severity="error",
        source="test-source",
        custom_details={"error": "Test error message"},
        dedup_key="test-dedup-key",
    )

    # Assert: requests.post called with expected parameters
    assert incident_key == "test-incident-key"
    mock_post.assert_called_once()
    call_args = mock_post.call_args
    assert call_args[0][0] == "https://events.pagerduty.com/v2/enqueue"
    assert call_args[1]["headers"]["Content-Type"] == "application/json"

    payload = call_args[1]["json"]
    assert payload["routing_key"] == "test-routing-key-123"
    assert payload["event_action"] == "trigger"
    assert payload["dedup_key"] == "test-dedup-key"
    assert payload["payload"]["summary"] == "Test validation failure"
    assert payload["payload"]["severity"] == "error"
    assert payload["payload"]["source"] == "test-source"
    assert payload["payload"]["custom_details"]["error"] == "Test error message"


@patch("mai_util.pagerduty_client.secretmanager.SecretManagerServiceClient")
@patch("mai_util.pagerduty_client.requests.post")
def test_pagerduty_alert_client_trigger_incident(mock_post, mock_secret_client_cls):
    # Arrange secret manager to return a fake routing key
    mock_secret_client = MagicMock()
    mock_secret_client.access_secret_version.return_value.payload.data.decode.return_value = (
        "test-routing-key-123"
    )
    mock_secret_client_cls.return_value = mock_secret_client

    # Arrange requests.post to return a successful response
    mock_response = MagicMock()
    mock_response.json.return_value = {"dedup_key": "test-incident-key"}
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    # Act: instantiate and use the alert client
    client = PagerDutyAlertClient(gcp_project="test-project")
    incident_key = client.trigger_incident(
        summary="Test validation failure", severity="critical"
    )

    # Assert: uses the correct secret name
    assert incident_key == "test-incident-key"
    mock_secret_client.access_secret_version.assert_called_once()
    call_args = mock_secret_client.access_secret_version.call_args
    assert "PAGERDUTY_VALIDATION_ALERTS_ROUTING_KEY" in call_args[0][0]


@patch("mai_util.pagerduty_client.secretmanager.SecretManagerServiceClient")
@patch("mai_util.pagerduty_client.requests.post")
def test_pagerduty_client_resolve_incident(mock_post, mock_secret_client_cls):
    # Arrange secret manager to return a fake routing key
    mock_secret_client = MagicMock()
    mock_secret_client.access_secret_version.return_value.payload.data.decode.return_value = (
        "test-routing-key-123"
    )
    mock_secret_client_cls.return_value = mock_secret_client

    # Arrange requests.post to return a successful response
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    # Act: instantiate and resolve incident
    client = PagerDutyClient(gcp_project="test-project")
    result = client.resolve_incident("test-dedup-key", summary="Resolved")

    # Assert: requests.post called with expected parameters
    assert result is True
    mock_post.assert_called_once()
    call_args = mock_post.call_args
    payload = call_args[1]["json"]
    assert payload["routing_key"] == "test-routing-key-123"
    assert payload["event_action"] == "resolve"
    assert payload["dedup_key"] == "test-dedup-key"
    assert payload["payload"]["summary"] == "Resolved"


@patch(
    "mai_util.pagerduty_client.secretmanager.SecretManagerServiceClient",
    side_effect=Exception("boom"),
)
def test_pagerduty_client_init_failure_sets_routing_key_none(_):
    client = PagerDutyClient(gcp_project="test-project")
    assert client.routing_key is None
    # Calling methods should return None/False but not raise
    assert client.trigger_incident("test") is None
    assert client.resolve_incident("test") is False


@patch("mai_util.pagerduty_client.secretmanager.SecretManagerServiceClient")
@patch("mai_util.pagerduty_client.requests.post")
def test_pagerduty_client_trigger_incident_request_exception(
    mock_post, mock_secret_client_cls
):
    # Arrange secret manager to return a fake routing key
    mock_secret_client = MagicMock()
    mock_secret_client.access_secret_version.return_value.payload.data.decode.return_value = (
        "test-routing-key-123"
    )
    mock_secret_client_cls.return_value = mock_secret_client

    # Arrange requests.post to raise an exception
    mock_post.side_effect = requests.exceptions.RequestException("Network error")

    # Act: instantiate and use the client
    client = PagerDutyClient(gcp_project="test-project")
    incident_key = client.trigger_incident(summary="Test failure")

    # Assert: returns None on error
    assert incident_key is None
