import logging
from abc import ABC
from typing import Dict, Optional

import requests
from google.cloud import secretmanager

logger = logging.getLogger(__name__)

PAGERDUTY_EVENTS_API_URL = "https://events.pagerduty.com/v2/enqueue"


class PagerDutyClient(ABC):
    """
    Client for sending events to PagerDuty via Events API v2.

    This is a base class that should be subclassed to provide specific
    routing key secret names. The routing key is retrieved from Google
    Secret Manager.

    Example:
        class MyPagerDutyClient(PagerDutyClient):
            ROUTING_KEY_SECRET = "MY_ROUTING_KEY_SECRET"

        client = MyPagerDutyClient(gcp_project="my-project")
        client.trigger_incident(summary="Alert", severity="error")
    """

    # Override in child classes to the correct secret key.
    ROUTING_KEY_SECRET = "PAGERDUTY_ROUTING_KEY"

    def __init__(self, gcp_project: str, routing_key_secret: Optional[str] = None):
        """
        Initialize PagerDuty client.

        Args:
            gcp_project: Google Cloud Project ID where the secret is stored
            routing_key_secret: Optional override for the secret name.
                              If not provided, uses ROUTING_KEY_SECRET class attribute.
        """
        self.gcp_project = gcp_project
        secret_name = routing_key_secret or self.ROUTING_KEY_SECRET

        # Get routing key from Google Secret Manager
        try:
            client = secretmanager.SecretManagerServiceClient()
            secret_path = f"projects/{gcp_project}/secrets/{secret_name}/versions/latest"
            response = client.access_secret_version(name=secret_path)
            self.routing_key = response.payload.data.decode("UTF-8").strip()
        except Exception as e:
            logger.error(f"Failed to initialize PagerDuty client: {e}")
            self.routing_key = None

    def trigger_incident(
        self,
        summary: str,
        severity: str = "error",
        source: str = "mai-service",
        custom_details: Optional[Dict] = None,
        dedup_key: Optional[str] = None,
    ) -> Optional[str]:
        """
        Trigger a PagerDuty incident.

        Args:
            summary: A brief text summary of the event
            severity: Severity level (critical, error, warning, info). Default: "error"
            source: The unique location of the affected system. Default: "mai-service"
            custom_details: Additional details about the event as a dictionary
            dedup_key: Optional deduplication key to prevent duplicate incidents.
                      If provided and an incident with this key exists, it will be updated
                      instead of creating a new one.

        Returns:
            The dedup_key (incident key) if successful, None otherwise
        """
        if not self.routing_key:
            logger.error("PagerDuty routing key not available, cannot trigger incident")
            return None

        payload = {
            "routing_key": self.routing_key,
            "event_action": "trigger",
            "payload": {
                "summary": summary,
                "severity": severity,
                "source": source,
            },
        }

        if custom_details:
            payload["payload"]["custom_details"] = custom_details

        if dedup_key:
            payload["dedup_key"] = dedup_key

        try:
            response = requests.post(
                PAGERDUTY_EVENTS_API_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            response.raise_for_status()

            result = response.json()
            incident_key = result.get("dedup_key") or dedup_key
            logger.info(f"PagerDuty incident triggered successfully: {incident_key}")
            return incident_key
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to trigger PagerDuty incident: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            return None

    def resolve_incident(self, dedup_key: str, summary: Optional[str] = None) -> bool:
        """
        Resolve a PagerDuty incident.

        Args:
            dedup_key: The deduplication key of the incident to resolve
            summary: Optional summary message for the resolution

        Returns:
            True if successful, False otherwise
        """
        if not self.routing_key:
            logger.error("PagerDuty routing key not available, cannot resolve incident")
            return False

        payload = {
            "routing_key": self.routing_key,
            "event_action": "resolve",
            "dedup_key": dedup_key,
        }

        if summary:
            payload["payload"] = {"summary": summary}

        try:
            response = requests.post(
                PAGERDUTY_EVENTS_API_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            response.raise_for_status()
            logger.info(f"PagerDuty incident resolved successfully: {dedup_key}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to resolve PagerDuty incident: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            return False


class PagerDutyAlertClient(PagerDutyClient):
    """
    Pre-configured client for sending validation failure alerts to PagerDuty.

    This client is configured to use the PAGERDUTY_VALIDATION_ALERTS_ROUTING_KEY
    secret from Google Secret Manager.

    Example:
        client = PagerDutyAlertClient(gcp_project="mai-project-a26f")
        client.trigger_incident(
            summary="Validation failed",
            severity="critical",
            source="mai-spark-validation"
        )
    """

    ROUTING_KEY_SECRET = "PAGERDUTY_VALIDATION_ALERTS_ROUTING_KEY"
