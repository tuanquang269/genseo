#!/usr/bin/env python3
"""Write a LOCAL llms.txt draft. Does not upload and does not call Shopify.

  python3 scripts/llms_txt_draft.py [--from-product-refs] [--out path] [handle ...]

AgeAura copy in the draft can name only
https://wellnessnest.co/products/ageaura-pure-nmn-tmg-nad-complex.
Urolithin A and every other AgeAura handle are omitted. A bare "ageaura"
handle is rewritten to that SKU. Exit 1 when any requested handle was rejected
(the written draft still does not contain it).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import brand_rules as br

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    out = None
    if "--out" in argv:
        out = argv[argv.index("--out") + 1]
    handles = list(args)
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
