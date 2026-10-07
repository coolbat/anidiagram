"""Relation-aware signal presentation layered over the frozen Edge Motion contract."""

from __future__ import annotations


def signal_semantic(kind: str | None) -> str:
    """Classify authored relation meaning without changing the frozen effect IDs.

    Unknown/absent semantics retain the explicitly selected visual recipe.
    """
    normalized = (kind or '').strip().lower().replace('_', '-').replace(' ', '-')
    if normalized in {'request', 'response', 'request-response', 'sync', 'synchronous', 'call', 'rpc', 'http', 'https'}:
        return 'sync'
    if normalized in {'async', 'async-message', 'asynchronous', 'queue', 'enqueue', 'dequeue', 'message', 'publish', 'subscribe', 'event', 'notify'}:
        return 'async'
    if normalized in {'stream', 'streaming', 'continuous', 'data-stream', 'sse', 'websocket'}:
        return 'stream'
    if normalized in {'failure', 'fail', 'error', 'reject', 'rejected', 'deny', 'denied', 'timeout'}:
        return 'failure'
    return 'default'
