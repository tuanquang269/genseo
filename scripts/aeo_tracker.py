#!/usr/bin/env python3
"""AI visibility entry point.

Mention and citation stay separate. template / validate / report / self-check
do not call an API. adapt calls one only when its key is already set.

The bare-query form is the old Gemini loop, kept for callers of run_aeo_scan:

  python3 scripts/aeo_tracker.py "best NMN supplement"

With GEMINI_API_KEY unset it writes a ticket whose mention and citation are
unknown. It does not invent a 1/5 score, and it does not call that result
an AI Overview. With the key set, the mention count is answer text only.
domain_cited stays unknown because this call does not return a source list.
"""
import os
import sys
import json
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ai_visibility

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def default_ticket_path():
    override = os.environ.get("AEO_TICKET_PATH")
    if override:
        return override
    return os.path.join(ROOT, "AEO_ACTION_TICKETS.md")


def simulate_llm_query(query, api_key):
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent?key=%s"
        % (ai_visibility.GEMINI_MODEL_DEFAULT, api_key)
    )
    payload = {
        "contents": [{"parts": [{"text": query}]}],
        "generationConfig": {"temperature": 0.7},
    }
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        res = urllib.request.urlopen(req)
        data = json.loads(res.read())
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as exc:
        print("API Error: %s" % exc)
        return None


def create_action_ticket(query, score, out_of, ticket_path=None, citation="unknown"):
    path = ticket_path or default_ticket_path()
    if score is None:
        content = (
            "# AEO tracker\n\n"
            "Query: `%s`\n\n"
            "GEMINI_API_KEY is unset. MOCK mode recorded no answer and no source list.\n\n"
            "- brand_mentioned: unknown\n"
            "- domain_cited: unknown\n"
            "- observed: false\n\n"
            "Enter the row with `python3 scripts/aeo_tracker.py template` after a real "
            "session, then `validate` and `report`.\n"
            % query
        )
    else:
        content = (
            "# AEO tracker\n\n"
            "Query: `%s`\n\n"
            "Gemini generateContent (%s) mention count: %s/%s answers that returned text.\n"
            "domain_cited: %s. This call returns answer text and does not return a source list.\n\n"
            "Record the row in data/ai_visibility/observations.json before changing a page.\n"
            "On-page citability checks live in scripts/geo_citability.py. "
            "Canonical product names live in the product guards.\n"
            % (query, ai_visibility.GEMINI_MODEL_DEFAULT, score, out_of, citation)
        )
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)
    print("Ticket saved to: " + path)


def _legacy_mention(answer, brand_name):
    if not isinstance(answer, str):
        return "unknown", ""
    needle = (brand_name or "").strip()
    if not needle:
        return "unknown", ""
    index = answer.lower().find(needle.lower())
    if index < 0:
        return "no", ""
    start = max(0, index - 60)
    end = min(len(answer), index + len(needle) + 60)
    return "yes", " ".join(answer[start:end].split())


def run_aeo_scan(query, brand_name="Your Brand", iterations=5, threshold=3,
                 ask=None, ticket_path=None, environ=None):
    """Legacy Gemini mention loop. Citation is unknown: the response is text."""
    env = os.environ if environ is None else environ
    api_key = env.get("GEMINI_API_KEY")
    if not api_key and ask is None:
        print("Error: GEMINI_API_KEY environment variable is not set.")
        print("Running in MOCK mode. Mention and citation stay unknown.")
        create_action_ticket(query, None, iterations, ticket_path=ticket_path)
        return

    ask = ask or (lambda text: simulate_llm_query(text, api_key))
    print("Simulating %s independent users asking AI: '%s'" % (iterations, query))
    print("Citation stays unknown. This call returns answer text, not a source list.")
    mentions = 0
    observed = 0
    missed = 0
    for index in range(iterations):
        print("User %s querying..." % (index + 1))
        answer = ask(query)
        mentioned, snippet = _legacy_mention(answer, brand_name)
        if mentioned == "unknown":
            missed += 1
            print(" -> Mention: unknown. Citation: unknown.")
            continue
        observed += 1
        if mentioned == "yes":
            mentions += 1
            print(" -> Mention: yes. Snippet: %s" % snippet)
        else:
            print(" -> Mention: no.")
        print(" -> Citation: unknown.")
    print("\nMention count: %s/%s observed answers (%s attempted)." % (mentions, observed, iterations))
    print("Citation: unknown.")
    if missed or observed != iterations:
        print("At least one attempt returned no answer text. No ticket.")
        return
    if mentions < threshold:
        print("Mention count is below the threshold. Citation is still unknown.")
        create_action_ticket(query, mentions, observed, ticket_path=ticket_path)
    else:
        print("Mention count is at the threshold. Citation is still unknown. No ticket.")


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print(ai_visibility.USAGE)
        return 0 if argv else 1
    if argv[0] not in ai_visibility.COMMANDS:
        run_aeo_scan(argv[0])
        return 0
    return ai_visibility.main(argv)


if __name__ == "__main__":
    sys.exit(main())
