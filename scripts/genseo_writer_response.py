#!/usr/bin/env python3
"""Classify a headless writer response as an Anthropic Message or not.

Claude Code talks to the Messages API. A 9router alias can still answer HTTP 200
with an OpenAI chat.completion (landing 2026-10-12 09:19, PATI-Alpha-Plan-Review).
The CLI then exits with "body is JSON but not a Message" and does not switch to
--fallback-model. This module is the check the runners use before one re-exec.

  python3 scripts/genseo_writer_response.py --log <file>
  python3 scripts/genseo_writer_response.py --body '<json>'

Exit 0 when that payload should re-exec on the fallback writer.
Exit 1 when it should not. Stdout stays empty.
"""
import json
import re
import sys

_CHAT_OBJECTS = ("chat.completion", "chat.completion.chunk")
_ANTHROPIC_ROLES = ("assistant", "user")
_STREAM_TYPES = (
    "message_start",
    "message_delta",
    "message_stop",
    "content_block_start",
    "content_block_delta",
    "content_block_stop",
    "ping",
)
_WRONG = ("openai_chat", "openai_response", "json_other")
_DIAGNOSTIC = re.compile(
    r"JSON but not a Message|json-not-message|not an Anthropic (?:Messages )?message",
    re.IGNORECASE,
)
_ATTEMPT = "=== writer attempt model="


class _NotJson(object):
    pass


_NOT_JSON = _NotJson()


def classify(value):
    """Return a short kind name for one decoded JSON value."""
    if isinstance(value, list):
        return "json_other"
    if not isinstance(value, dict):
        return "not_json"
    if _is_openai_chat(value):
        return "openai_chat"
    if _is_openai_response(value):
        return "openai_response"
    if _is_anthropic_message(value):
        return "anthropic_message"
    if _is_anthropic_error(value):
        return "anthropic_error"
    if value.get("type") in _STREAM_TYPES:
        return "anthropic_stream"
    return "json_other"


def body_needs_fallback(raw):
    """True when this HTTP body is JSON and is not an Anthropic message."""
    value = _loads(raw)
    if value is _NOT_JSON:
        return False
    return classify(value) in _WRONG


def log_needs_fallback(text):
    """True when the latest writer attempt should re-exec on the fallback."""
    body = _attempt_body(text).strip()
    if not body:
        return False
    value = _loads(body)
    if value is not _NOT_JSON:
        return classify(value) in _WRONG
    if _DIAGNOSTIC.search(body):
        return True
    for obj in _iter_objects(body):
        if classify(obj) in ("openai_chat", "openai_response"):
            return True
    return False


def _is_anthropic_message(value):
    if value.get("type") != "message":
        return False
    if value.get("role") not in _ANTHROPIC_ROLES:
        return False
    if not isinstance(value.get("content"), list):
        return False
    if value.get("object") in _CHAT_OBJECTS:
        return False
    return True


def _is_anthropic_error(value):
    return value.get("type") == "error" and isinstance(value.get("error"), dict)


def _is_openai_chat(value):
    if value.get("object") in _CHAT_OBJECTS:
        return True
    choices = value.get("choices")
    if not isinstance(choices, list) or not choices:
        return False
    if value.get("type") == "message" and isinstance(value.get("content"), list):
        return False
    first = choices[0]
    if not isinstance(first, dict):
        return False
    return "message" in first or "delta" in first


def _is_openai_response(value):
    if value.get("object") != "response":
        return False
    if value.get("type") == "message":
        return False
    return isinstance(value.get("output"), list)


def _attempt_body(text):
    if not text:
        return ""
    idx = text.rfind(_ATTEMPT)
    if idx < 0:
        return text
    rest = text[idx:]
    nl = rest.find("\n")
    if nl < 0:
        return ""
    return rest[nl + 1 :]


def _loads(raw):
    if raw is None:
        return _NOT_JSON
    text = raw.strip().lstrip("\ufeff")
    if not text:
        return _NOT_JSON
    try:
        return json.loads(text)
    except (ValueError, TypeError):
        return _NOT_JSON


def _iter_objects(text):
    decoder = json.JSONDecoder()
    index = 0
    length = len(text)
    while index < length:
        start = text.find("{", index)
        if start < 0:
            return
        try:
            value, end = decoder.raw_decode(text, start)
        except ValueError:
            index = start + 1
            continue
        if isinstance(value, dict):
            yield value
        index = end if end > start else start + 1


def main(argv):
    mode = None
    arg = None
    i = 1
    while i < len(argv):
        item = argv[i]
        if item in ("--log", "--body") and i + 1 < len(argv):
            mode = item
            arg = argv[i + 1]
            i += 2
            continue
        sys.stderr.write("usage: genseo_writer_response.py --log <file> | --body <json>\n")
        return 2
    if mode is None:
        sys.stderr.write("usage: genseo_writer_response.py --log <file> | --body <json>\n")
        return 2
    if mode == "--log":
        try:
            text = open(arg, "r", encoding="utf-8", errors="replace").read()
        except OSError as err:
            sys.stderr.write("writer-shape: cannot read log: %s\n" % err)
            return 1
        needs = log_needs_fallback(text)
    else:
        needs = body_needs_fallback(arg)
    return 0 if needs else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
