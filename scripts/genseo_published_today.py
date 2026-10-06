#!/usr/bin/env python3
"""How many GenSeo articles are LIVE today (Asia/Saigon day), read from the PUBLIC site.

This is the cross-Mac source of truth (Kevin 2026-10-06: no automation may depend on one Mac).
The Mini and the MacBook keep separate ticket files, so neither can see the other's [DONE]
marks — but both publish to the same store, so the live atom feed is shared state that needs
no credentials, no Syncthing (vault sync is MacBook->Mini one-way) and no SSH.

Usage:
  genseo_published_today.py                 -> prints the count (int)
  genseo_published_today.py --json          -> {"date","count","entries":[{url,title,published_ict}]}
  genseo_published_today.py --peer-active MIN --local-log FILE
        -> exit 3 if a post published today in the last MIN minutes is NOT in FILE
           (i.e. the OTHER Mac is mid-batch right now), else exit 0. Prints the reason.
Fails CLOSED: if the feed cannot be read, prints -1 / exits 4 so callers do not publish blind.
"""
import argparse, datetime as dt, json, re, sys, urllib.request
from xml.etree import ElementTree as ET

FEED = "https://wellnessnest.co/blogs/news.atom"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")
ICT = dt.timezone(dt.timedelta(hours=7))
NS = {"a": "http://www.w3.org/2005/Atom"}


def entries():
    req = urllib.request.Request(FEED + "?_=" + str(int(dt.datetime.now().timestamp())),
                                 headers={"User-Agent": UA, "Cache-Control": "no-cache"})
    root = ET.fromstring(urllib.request.urlopen(req, timeout=30).read())
    out = []
    for e in root.findall("a:entry", NS):
        pub = e.findtext("a:published", default="", namespaces=NS)
        link = ""
        for l in e.findall("a:link", NS):
            if l.get("rel", "alternate") == "alternate":
                link = l.get("href", "")
        t = dt.datetime.fromisoformat(pub.replace("Z", "+00:00")).astimezone(ICT)
        out.append({"url": link.split("?")[0], "title": e.findtext("a:title", default="", namespaces=NS),
                    "published_ict": t})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--date", help="YYYY-MM-DD (ICT); default today ICT")
    ap.add_argument("--peer-active", type=int, metavar="MIN")
    ap.add_argument("--local-log")
    a = ap.parse_args()
    day = a.date or dt.datetime.now(ICT).date().isoformat()
    try:
        es = [e for e in entries() if e["published_ict"].date().isoformat() == day]
    except Exception as exc:  # noqa: BLE001
        print(-1 if not a.json else json.dumps({"date": day, "count": -1, "error": str(exc)}))
        sys.exit(4)
    if a.peer_active is not None:
        mine = set()
        if a.local_log:
            try:
                mine = {re.sub(r"[?#].*", "", l.split()[-1]) for l in open(a.local_log) if l.strip()}
            except FileNotFoundError:
                pass
        now = dt.datetime.now(ICT)
        foreign = [e for e in es if e["url"] not in mine
                   and (now - e["published_ict"]).total_seconds() < a.peer_active * 60]
        if foreign:
            f = max(foreign, key=lambda e: e["published_ict"])
            print(f"peer-active: {f['url']} went live {f['published_ict']:%H:%M} ICT and was not published by this Mac")
            sys.exit(3)
        print("peer-idle")
        sys.exit(0)
    if a.json:
        print(json.dumps({"date": day, "count": len(es), "entries": [
            {**e, "published_ict": e["published_ict"].isoformat()} for e in es]}, indent=1))
    else:
        print(len(es))


if __name__ == "__main__":
    main()
