#!/usr/bin/env python3
"""Formula sentences for a local llms.txt draft.

A sentence is included only when it matches that product's label source of truth.
Anything else is omitted. This module does not upload and does not call Shopify.

  FloraFresh — scripts/florafresh_rules.py (Supplement Facts: SNZ-1969, 15B CFU).
  FusiForce — product_refs/fusiforce-creatine-gummies.label.json ("90" + "Gummies").
    The front-of-pouch OCR does not state a serving count or a ginseng milligram,
    so the sentence does not state one.
  Shilajit gummies — optional tokens "60 GUMMIES" and "60-DAY SUPPLY".
    A 30-serving panel is not that label.
"""
import json
import os
import re

import ageaura_rules
import florafresh_rules as ff

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FUSI = "fusiforce-creatine-gummies"
SHIL = "premium-himalayan-shilajit-gummies"

FUSI_LINE = "FusiForce Creatine Monohydrate Gummies, 90 gummies (pack label)."
SHIL_LINE = "Premium Himalayan Shilajit Gummies, 60 gummies, 60-day supply (pack label)."
FLORA_LINE = "FloraFresh: " + ff.FORMULA_LINE

_EXTRA_NUMBER = re.compile(
    r"\b\d+\s+servings?\b|\b\d+(?:,\d{3})*(?:\.\d+)?\s*mg\b",
    re.I,
)


def label_spec(handle, root=None):
    root = ROOT if root is None else root
    path = os.path.join(root, "product_refs", handle + ".label.json")
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _blob(spec):
    parts = [str(part) for part in (spec.get("required") or []) + (spec.get("optional") or [])]
    return " ".join(parts)


def matches_label(handle, sentence, root=None):
    """True only when `sentence` is supported by that product's label source of truth."""
    sentence = sentence or ""
    if re.search(r"urolithin", sentence, re.I):
        return False
    if handle == ff.HANDLE:
        if ff.STRAIN not in sentence or ff.CFU not in sentence:
            return False
        return ff.violations(sentence) == []
    spec = label_spec(handle, root)
    if not spec:
        return False
    blob = _blob(spec)
    if handle == FUSI:
        if "90" not in [str(item) for item in (spec.get("required") or [])]:
            return False
        if not re.search(r"\bgummies?\b", blob, re.I):
            return False
        if not re.search(r"\b90\b", sentence) or not re.search(r"gummies", sentence, re.I):
            return False
        if re.search(r"\b84\b", sentence):
            return False
        if re.search(r"\b(?:25|50)\s*mg\b", sentence, re.I):
            return False
        for match in _EXTRA_NUMBER.finditer(sentence):
            if match.group(0).lower() not in blob.lower():
                return False
        return True
    if handle == SHIL:
        if "60 GUMMIES" not in blob or "60-DAY SUPPLY" not in blob:
            return False
        if not re.search(r"\b60\b", sentence) or not re.search(r"60-day", sentence, re.I):
            return False
        if re.search(r"\b30\s+servings?\b", sentence, re.I):
            return False
        if re.search(r"\b84\b", sentence):
            return False
        return True
    return False


def formula_line(handle, root=None):
    """The one sentence a local draft may state, or None when the label does not support one."""
    if ageaura_rules.classify_handle(handle) == "deny":
        return None
    if handle == ff.HANDLE:
        line = FLORA_LINE
    elif handle == FUSI:
        line = FUSI_LINE
    elif handle == SHIL:
        line = SHIL_LINE
    else:
        return None
    if not matches_label(handle, line, root):
        return None
    return line
