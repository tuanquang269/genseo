#!/usr/bin/env python3
"""Resolve GenSeo writer names to Claude Code model ids.

9router aliases such as PATI-Alpha-Plan-Review are not Anthropic model ids.
Claude Code logs [claude-code:unrecognized_model] for them. From v2.1.268 it
also confirms an id it does not accept locally the first time a session
switches to it. Landing 2026-10-15 hung on that switch: the SDK query used
PATI-Alpha-Plan-Review and the built-in Explore agent used PATI-Fable-5.
The names are gateway aliases, not a typo, and hosted-9router had already
been selected.

modelOverrides keys are Anthropic ids Claude Code accepts. Values are the
aliases the router still receives. The headless runner passes the key to
--model and merges this map into --settings. ANTHROPIC_API_KEY stays unset.

  python3 scripts/genseo_model_map.py claude-id -- <name>
  python3 scripts/genseo_model_map.py merge-settings --writer <a> --fallback <b>

claude-id prints one line, "OK <id>" or "ERR <message>". merge-settings
reads an optional settings JSON object on stdin and prints one JSON object.
A name that starts with claude- is passed through and is not rewritten.
"""
import json
import os
import sys

_MAP_NAME = "genseo_model_map.json"


def map_path():
    override = os.environ.get("GENSEO_MODEL_MAP_JSON")
    if override:
        return override
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), _MAP_NAME)


def refuse_message(name):
    shown = name if name else "(empty)"
    return (
        "unrecognized model: %s is not a Claude Code model id and has no "
        "modelOverrides entry in scripts/genseo_model_map.json. Refusing to "
        "start claude. Bare aliases hang on unrecognized_model (landing "
        "2026-10-15, Explore switched to the fallback). Add an entry "
        "{\"<claude-id>\": \"%s\"} or set the writer to a claude-* id. "
        "A local 9router /v1/models listing is not enough."
        % (shown, shown)
    )


def load_overrides(path):
    """Return (by_alias, error). by_alias maps a gateway alias to its Claude id."""
    try:
        raw = open(path, "r", encoding="utf-8").read()
    except OSError as err:
        return None, "model map unreadable: %s" % err
    try:
        data = json.loads(raw) if raw.strip() else None
    except ValueError:
        return None, "model map unreadable: scripts/genseo_model_map.json is not JSON"
    overrides = data.get("modelOverrides") if isinstance(data, dict) else None
    if not isinstance(overrides, dict) or not overrides:
        return None, "model map unreadable: modelOverrides is missing"
    by_alias = {}
    for key, value in overrides.items():
        if not isinstance(key, str) or not key.startswith("claude-"):
            return None, "model map unreadable: %r is not a claude- model id" % key
        if not isinstance(value, str) or not value or value.startswith("claude-"):
            return None, "model map unreadable: alias for %s is empty or already a claude id" % key
        if value in by_alias:
            return None, "model map unreadable: %s is mapped more than once" % value
        by_alias[value] = key
    return by_alias, None


def resolve_name(name, by_alias, load_error):
    if not isinstance(name, str) or not name:
        return None, refuse_message("")
    if name.startswith("claude-"):
        return name, None
    if load_error:
        return None, load_error
    mapped = by_alias.get(name) if isinstance(by_alias, dict) else None
    if mapped:
        return mapped, None
    return None, refuse_message(name)


def overrides_for(names, by_alias, load_error):
    """Return the modelOverrides object this run needs, or (None, error)."""
    selected = {}
    for name in names:
        if not isinstance(name, str) or not name or name.startswith("claude-"):
            resolved, err = resolve_name(name, by_alias, load_error)
            if err:
                return None, err
            continue
        resolved, err = resolve_name(name, by_alias, load_error)
        if err:
            return None, err
        selected[resolved] = name
    return selected, None


def merge_settings(existing_raw, names, by_alias, load_error):
    text = (existing_raw or "").strip()
    if text:
        try:
            existing = json.loads(text)
        except ValueError:
            return None, "model settings are not a JSON object"
        if not isinstance(existing, dict):
            return None, "model settings are not a JSON object"
    else:
        existing = {}
    selected, err = overrides_for(names, by_alias, load_error)
    if err:
        return None, err
    if not selected and not existing:
        return "", None
    merged = dict(existing)
    if selected:
        previous = merged.get("modelOverrides")
        if previous is None:
            previous = {}
        if not isinstance(previous, dict):
            return None, "model settings modelOverrides is not an object"
        combined = dict(previous)
        combined.update(selected)
        merged["modelOverrides"] = combined
    return json.dumps(merged, separators=(",", ":"), sort_keys=True), None


def _argv_value(argv, flag):
    if flag in argv:
        index = argv.index(flag)
        if index + 1 < len(argv):
            return argv[index + 1]
    return ""


def main(argv):
    if len(argv) >= 3 and argv[1] == "claude-id" and argv[2] == "--":
        name = argv[3] if len(argv) > 3 else ""
        by_alias, load_error = load_overrides(map_path())
        resolved, err = resolve_name(name, by_alias, load_error)
        if err:
            sys.stdout.write("ERR %s\n" % err)
            return 1
        sys.stdout.write("OK %s\n" % resolved)
        return 0
    if len(argv) >= 2 and argv[1] == "merge-settings":
        writer = _argv_value(argv, "--writer")
        fallback = _argv_value(argv, "--fallback")
        existing = sys.stdin.read()
        by_alias, load_error = load_overrides(map_path())
        merged, err = merge_settings(existing, (writer, fallback), by_alias, load_error)
        if err:
            sys.stderr.write("%s\n" % err)
            return 1
        if merged:
            sys.stdout.write(merged)
        return 0
    sys.stderr.write(
        "usage: genseo_model_map.py claude-id -- <name> | "
        "merge-settings --writer <a> --fallback <b>\n"
    )
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
