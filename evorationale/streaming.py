"""Authenticated GitHub webhook -> versioned Kafka event; not used for retrospective replay."""
from __future__ import annotations
import hashlib
import hmac
import json
from typing import Any


def verify_github_webhook(body: bytes, signature_header: str, secret: str) -> dict[str, Any]:
    if not secret or not signature_header.startswith("sha256="):
        raise ValueError("Webhook HMAC secret/signature missing")
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature_header, "sha256=" + digest):
        raise ValueError("Invalid GitHub webhook HMAC")
    return json.loads(body)


def kafka_publish(producer: Any, topic: str, delivery_id: str, event_name: str,
                  body: bytes, signature: str, secret: str) -> None:
    value = verify_github_webhook(body, signature, secret)
    if not delivery_id or not event_name:
        raise ValueError("Event ID and event name required for deduplication")
    repo = (value.get("repository") or {}).get("full_name")
    if not repo:
        raise ValueError("Authenticated event has no repository")
    # Downstream storage must idempotently deduplicate by delivery_id.
    producer.send(topic, key=delivery_id.encode(), value=json.dumps({
        "delivery_id": delivery_id, "event_name": event_name,
        "repository": repo, "payload": value}, sort_keys=True).encode())
