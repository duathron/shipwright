"""Shared LLM-provider transport layer for Shipwright CLI tools (sift, barb).

Owns the *mechanism* only — "build request -> call SDK/HTTP -> return raw
text" for Anthropic, OpenAI, and a local Ollama server. Mirrors
``shipwright_kit.config``'s shape: shared mechanism, per-tool schema. The
per-tool bits (prompt content, response JSON-parse/validate/fence-strip,
template fallback, the ``SummarizerProtocol``/``ExplainerProtocol``, client
construction/import-guarding, and every try/except around these calls) stay
in each tool.

The SDK-backed providers (``anthropic_complete``, ``openai_complete``) take
an INJECTED ``client``: the caller constructs its own SDK client (with its
own install-hint/``ImportError`` handling in the tool's ``__init__``) and
passes it in. This module never imports ``anthropic``/``openai`` and never
constructs a client itself — the client is duck-typed, so import-lightness
here is structural (no SDK import exists to lazily defer), not merely lazy.

These are DUMB TRANSPORTS. They do NOT redact, sanitize, or scan ``system``/
``user`` text in any way — whatever the caller passes is sent to the provider
byte-for-byte. Redaction/injection-scanning is entirely the caller's
responsibility and must happen *before* calling into this module.

Exception-transparent by design: none of the three public functions contains
a ``try``/``except``. SDK, HTTP, and JSON/KeyError failures propagate to the
caller unchanged so each tool can keep its own existing error handling
(re-raise as ``RuntimeError``, swallow-and-fall-back-to-template, etc.) without
this module making that policy choice for them. The only exception raised
*by* this module itself is ``ValueError`` for an unrecognized ``extract``/
``system_mode`` literal — an input-validation guard, not error-swallowing.

No ``max_tokens``/``temperature`` default is baked in here (the config.py
lesson: no schema in the mechanism) — callers supply every value.
``temperature=None`` is a real sentinel: when a caller doesn't pass one, it is
OMITTED from the outbound request entirely rather than defaulted, so a
provider that never sent temperature today keeps not sending it.
"""

from __future__ import annotations

import json
import urllib.request
from typing import Any

__all__ = ["anthropic_complete", "ollama_generate", "openai_complete"]


# ---------------------------------------------------------------------------
# Anthropic
# ---------------------------------------------------------------------------


def anthropic_complete(
    *,
    client: Any,
    model: str,
    max_tokens: int,
    system: str,
    user: str,
    temperature: float | None = None,
    extract: str = "first_text_block",
) -> str:
    """Call the Anthropic Messages API on a caller-supplied client and return
    the extracted text.

    ``client`` is a pre-built Anthropic SDK client (e.g.
    ``anthropic.Anthropic(api_key=...)``) constructed and owned by the
    caller; this function only calls ``client.messages.create(...)`` and
    extracts text from the response. ``extract`` reconciles the two known
    current extraction behaviors:

    - ``"first_text_block"`` (sift's current behavior): scan
      ``message.content`` for the first block exposing a ``.text``
      attribute; if none is found, return ``""`` (defensive).
    - ``"index0"`` (barb's current behavior): ``message.content[0].text``
      unconditionally — raises ``IndexError``/``AttributeError`` uncaught on
      an empty or non-text first block. NOT "fixed" here; that crash-on-empty
      behavior is preserved on purpose (named follow-up F2 owns fixing it).

    Raises:
        ValueError: ``extract`` is not one of the two known modes.
        Exception: any exception raised by ``client.messages.create(...)``
            propagates unchanged — no try/except here.
    """
    kwargs: dict[str, Any] = {
        "model": model,
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    if temperature is not None:
        kwargs["temperature"] = temperature

    message = client.messages.create(**kwargs)

    if extract == "index0":
        return message.content[0].text
    if extract == "first_text_block":
        for block in message.content:
            if hasattr(block, "text"):
                return block.text
        return ""
    raise ValueError(f"unknown extract mode: {extract!r}")


# ---------------------------------------------------------------------------
# OpenAI
# ---------------------------------------------------------------------------


def openai_complete(
    *,
    client: Any,
    model: str,
    max_tokens: int,
    system: str,
    user: str,
    temperature: float | None = None,
) -> str:
    """Call the OpenAI Chat Completions API on a caller-supplied client and
    return the response text.

    ``client`` is a pre-built OpenAI SDK client (e.g.
    ``openai.OpenAI(api_key=...)``) constructed and owned by the caller; this
    function only calls ``client.chat.completions.create(...)`` and extracts
    text from the response (``response.choices[0].message.content or ""`` —
    a ``None`` content, e.g. a tool-call-only response, degrades to ``""``
    rather than raising, matching both sift and barb today).

    Raises:
        Exception: any exception raised by
            ``client.chat.completions.create(...)`` propagates unchanged —
            no try/except here.
    """
    kwargs: dict[str, Any] = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    if temperature is not None:
        kwargs["temperature"] = temperature

    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content or ""


# ---------------------------------------------------------------------------
# Ollama
# ---------------------------------------------------------------------------


def ollama_generate(
    *,
    base_url: str,
    model: str,
    system: str,
    user: str,
    timeout: float | None,
    system_mode: str,
) -> str:
    """POST to a local Ollama ``/api/generate`` endpoint and return the raw
    ``response`` field, unstripped.

    Literal move of the ``urllib.request`` POST + outer-JSON-envelope
    extraction (``json.loads(body)["response"]``). ``system_mode``
    reconciles the two known current payload shapes:

    - ``"fold"`` (sift's current behavior): no dedicated system field on
      ``/api/generate`` in all Ollama versions, so ``system`` is prepended
      into the prompt string as ``f"{system}\\n\\n{user}"``. Payload keys:
      ``{"model", "prompt", "stream"}``.
    - ``"field"`` (barb's current behavior): ``system`` sent as its own
      top-level payload key, ``prompt`` is ``user`` alone. Payload keys:
      ``{"model", "system", "prompt", "stream"}``.

    Note: barb's caller additionally does ``.strip()`` on the returned text
    today; that is NOT done here (sift's raw extraction never strips) — each
    tool's own call site is responsible for any such post-processing.

    Raises:
        ValueError: ``system_mode`` is not one of the two known modes.
        urllib.error.URLError, OSError: network/HTTP failure — propagates
            unchanged, no try/except here.
        json.JSONDecodeError: the outer HTTP body is not valid JSON —
            propagates unchanged.
        KeyError: the outer JSON envelope has no ``"response"`` key —
            propagates unchanged.
    """
    generate_url = f"{base_url.rstrip('/')}/api/generate"

    if system_mode == "fold":
        payload: dict[str, Any] = {"model": model, "prompt": f"{system}\n\n{user}", "stream": False}
    elif system_mode == "field":
        payload = {"model": model, "system": system, "prompt": user, "stream": False}
    else:
        raise ValueError(f"unknown system_mode: {system_mode!r}")

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        generate_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8")

    outer = json.loads(body)
    return outer["response"]
