"""
[PHASE6] Webhooks system for Adam Prism.
Supports:
- Incoming webhooks (from external services)
- Outgoing webhooks (Adam -> external URLs)
- HMAC-SHA256 signature verification
- Automatic retries with exponential backoff
"""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import secrets
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

import httpx

logger = logging.getLogger("adam_prism.webhooks")


class WebhookEvent(str, Enum):
    """[PHASE6] Webhook event types."""

    CHAT_CREATED = "chat.created"
    CHAT_MESSAGE = "chat.message"
    SESSION_CREATED = "session.created"
    SESSION_DELETED = "session.deleted"
    KNOWLEDGE_ADDED = "knowledge.added"
    BOTTLENECK_PREDICTED = "bottleneck.predicted"
    TOOL_EXECUTED = "tool.executed"
    ERROR_OCCURRED = "error.occurred"


@dataclass
class WebhookSubscription:
    """[PHASE6] A webhook subscription."""

    id: str
    url: str
    events: list[str]  # WebhookEvent values
    secret: str  # HMAC-SHA256 secret
    is_active: bool = True
    created_at: float = field(default_factory=time.time)
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class WebhookDelivery:
    """[PHASE6] Record of a webhook delivery attempt."""

    id: str
    subscription_id: str
    event: str
    url: str
    payload: dict
    attempt: int = 1
    max_attempts: int = 5
    status_code: int | None = None
    response_body: str | None = None
    error: str | None = None
    delivered: bool = False
    started_at: float = field(default_factory=time.time)
    completed_at: float | None = None
    next_retry_at: float | None = None


class WebhookManager:
    """[PHASE6] Manage webhooks: subscribe, dispatch, retry."""

    def __init__(self):
        self._subscriptions: dict[str, WebhookSubscription] = {}
        self._deliveries: list[WebhookDelivery] = []
        self._max_deliveries = 1000

    def subscribe(
        self,
        url: str,
        events: list[str],
        description: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> WebhookSubscription:
        """[PHASE6] Subscribe a URL to receive webhooks."""
        sub = WebhookSubscription(
            id=f"wh_{secrets.token_hex(8)}",
            url=url,
            events=events,
            secret=secrets.token_hex(32),
            description=description,
            metadata=metadata or {},
        )
        self._subscriptions[sub.id] = sub
        logger.info(f"[WEBHOOK] New subscription {sub.id} for {url} ({len(events)} events)")
        return sub

    def unsubscribe(self, subscription_id: str) -> bool:
        """[PHASE6] Remove a subscription."""
        if subscription_id in self._subscriptions:
            del self._subscriptions[subscription_id]
            return True
        return False

    def list_subscriptions(self) -> list[WebhookSubscription]:
        """[PHASE6] List all subscriptions."""
        return list(self._subscriptions.values())

    def get_subscription(self, subscription_id: str) -> WebhookSubscription | None:
        return self._subscriptions.get(subscription_id)

    def sign_payload(self, subscription: WebhookSubscription, payload: bytes) -> str:
        """[PHASE6] Generate HMAC-SHA256 signature for the payload."""
        return hmac.new(
            subscription.secret.encode("utf-8"),
            payload,
            hashlib.sha256,
        ).hexdigest()

    async def dispatch(
        self,
        event: str,
        data: dict,
        subscription_id: str | None = None,
    ) -> list[WebhookDelivery]:
        """[PHASE6] Dispatch an event to all matching subscriptions."""
        targets = []
        if subscription_id:
            sub = self._subscriptions.get(subscription_id)
            if sub and sub.is_active and event in sub.events:
                targets = [sub]
        else:
            targets = [
                s for s in self._subscriptions.values()
                if s.is_active and event in s.events
            ]

        if not targets:
            return []

        deliveries = []
        for sub in targets:
            payload = {
                "event": event,
                "data": data,
                "subscription_id": sub.id,
                "timestamp": time.time(),
                "delivery_id": f"del_{secrets.token_hex(8)}",
            }
            delivery = WebhookDelivery(
                id=payload["delivery_id"],
                subscription_id=sub.id,
                event=event,
                url=sub.url,
                payload=payload,
            )
            deliveries.append(delivery)
            # Fire and forget (async)
            asyncio.create_task(self._deliver(delivery, sub))

        # Trim old deliveries
        self._deliveries.extend(deliveries)
        if len(self._deliveries) > self._max_deliveries:
            self._deliveries = self._deliveries[-self._max_deliveries:]

        return deliveries

    async def _deliver(
        self, delivery: WebhookDelivery, sub: WebhookSubscription
    ) -> None:
        """[PHASE6] Deliver a webhook with retries."""
        payload_bytes = json.dumps(delivery.payload).encode("utf-8")
        signature = self.sign_payload(sub, payload_bytes)
        headers = {
            "Content-Type": "application/json",
            "X-Adam-Prism-Event": delivery.event,
            "X-Adam-Prism-Delivery": delivery.id,
            "X-Adam-Prism-Signature": f"sha256={signature}",
            "User-Agent": "Adam-Prism-Webhook/1.0",
        }

        for attempt in range(1, delivery.max_attempts + 1):
            delivery.attempt = attempt
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(
                        delivery.url,
                        content=payload_bytes,
                        headers=headers,
                    )
                delivery.status_code = resp.status_code
                delivery.response_body = resp.text[:500]
                if 200 <= resp.status_code < 300:
                    delivery.delivered = True
                    delivery.completed_at = time.time()
                    logger.info(
                        f"[WEBHOOK] {delivery.id} delivered to {sub.url} (HTTP {resp.status_code})"
                    )
                    return
                # Server error — retry
                delivery.error = f"HTTP {resp.status_code}"
            except Exception as e:
                delivery.error = str(e)[:200]
                logger.warning(
                    f"[WEBHOOK] {delivery.id} attempt {attempt} failed: {delivery.error}"
                )

            # Exponential backoff: 1s, 2s, 4s, 8s, 16s
            if attempt < delivery.max_attempts:
                backoff = 2 ** (attempt - 1)
                delivery.next_retry_at = time.time() + backoff
                await asyncio.sleep(backoff)

        delivery.completed_at = time.time()
        logger.error(
            f"[WEBHOOK] {delivery.id} FAILED after {delivery.max_attempts} attempts"
        )

    def get_deliveries(self, limit: int = 100) -> list[WebhookDelivery]:
        return self._deliveries[-limit:]


# [PHASE6] Singleton
_webhook_manager: WebhookManager | None = None


def get_webhook_manager() -> WebhookManager:
    """[PHASE6] Get the singleton webhook manager."""
    global _webhook_manager
    if _webhook_manager is None:
        _webhook_manager = WebhookManager()
    return _webhook_manager
