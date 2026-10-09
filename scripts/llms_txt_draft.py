#!/usr/bin/env python3
"""Write a LOCAL llms.txt draft. Does not upload and does not call Shopify.

  python3 scripts/llms_txt_draft.py [--from-product-refs] [--out path] [handle ...]

AgeAura copy in the draft can name only
https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex.
Urolithin A and every other AgeAura handle are omitted. A bare "ageaura"
handle is rewritten to that SKU. Exit 1 when any requested handle was rejected
(the written draft still does not contain it).

FloraFresh, FusiForce, and shilajit-gummies formula sentences are written only
when they match the label source of truth (scripts/llms_formula.py). A handle
with no matching label sentence gets a URL and nothing invented.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import brand_rules as br

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(argv):
    out = None
    skip = set()
    i = 0
    while i < len(argv):
        if argv[i] == "--out":
            if i + 1 >= len(argv):
                print("FAIL CLOSED: --out needs a path", file=sys.stderr)
                return 1
            out = argv[i + 1]
            skip.update((i, i + 1))
            i += 2
            continue
        i += 1
    handles = [arg for i, arg in enumerate(argv) if i not in skip and not arg.startswith("--")]
    if "--from-product-refs" in argv:
        handles.extend(br.handles_from_product_refs(os.path.join(ROOT, "product_refs")))
    if not handles:
        handles = [br.AGEAURA_OK]
    text, rejected = br.llms_txt_draft(handles)
    if out:
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"wrote {out}")
    else:
        sys.stdout.write(text)
    if rejected:
        print("rejected (not written): " + ", ".join(rejected), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
