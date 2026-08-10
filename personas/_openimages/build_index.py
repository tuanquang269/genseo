"""Build a key-free candidate index from Google's Open Images metadata + MIAP annotations.

Why this exists: Commons costs ~50 vision calls per accepted persona, because nothing in its
metadata says whether a photograph contains exactly one adult of a given apparent gender. Open
Images ships that as data. MIAP ("More Inclusive Annotations for People") boxes every person in
the CC BY corpus with a PERCEIVED gender presentation and age presentation, so the demographic
question that dominates our rejections can be asked for free, before a single model call.

Nothing here touches flickr.com. Flickr's robots.txt is `User-agent: * / Disallow: /`, so we
never crawl it: the metadata comes from Google's own storage bucket and the pixels come from
staticflickr.com, whose robots.txt carries no directives at all. No key, no account, no login.
"""
import csv, gzip, io, json, os, sys, urllib.request

BASE = "https://storage.googleapis.com/openimages"
MIAP = {
    "train": BASE + "/open_images_extended_miap/open_images_extended_miap_boxes_train.csv",
    "val":   BASE + "/open_images_extended_miap/open_images_extended_miap_boxes_val.csv",
    "test":  BASE + "/open_images_extended_miap/open_images_extended_miap_boxes_test.csv",
}
IMGS = {
    "train": BASE + "/2018_04/train/train-images-boxable-with-rotation.csv",
    "val":   BASE + "/2018_04/validation/validation-images-with-rotation.csv",
    "test":  BASE + "/2018_04/test/test-images-with-rotation.csv",
}

def fetch(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return path
    print("  downloading %s -> %s" % (url.rsplit('/',1)[-1], path))
    urllib.request.urlretrieve(url, path)
    return path

def miap_solo(path):
    """ImageID -> the single person box, for images with exactly one person box.

    Exactly one is the point: `person_count != 1` was the single commonest vision rejection on
    Commons. An image with two boxes is not a portrait we can anchor a persona on."""
    byimg = {}
    dupes = set()
    for r in csv.DictReader(open(path)):
        i = r["ImageID"]
        if i in byimg: dupes.add(i)
        byimg[i] = r
    return {i: r for i, r in byimg.items() if i not in dupes}

def main():
    out = {}
    for split in ("train", "val", "test"):
        mp = fetch(MIAP[split], "miap_%s.csv" % split)
        solo = miap_solo(mp)
        keep = {}
        for i, r in solo.items():
            if r["GenderPresentation"] == "Unknown": continue
            if r["IsGroupOf"] == "1" or r["IsDepictionOf"] == "1": continue
            area = (float(r["XMax"])-float(r["XMin"])) * (float(r["YMax"])-float(r["YMin"]))
            # Under a tenth of the frame the person is scenery, and a face crop off it will not
            # survive the resolution floor even when the file itself does.
            if area < 0.10: continue
            keep[i] = r
        print("%s: %d solo person boxes -> %d with a stated gender and enough frame"
              % (split, len(solo), len(keep)))
        ip = fetch(IMGS[split], "images_%s.csv" % split)
        n = 0
        for r in csv.DictReader(open(ip)):
            i = r["ImageID"]
            if i not in keep: continue
            b = keep[i]
            out[i] = {
                "image_id": i, "split": split,
                "url": r["OriginalURL"], "landing": r["OriginalLandingURL"],
                "licence": r["License"], "author": r["Author"],
                "author_url": r["AuthorProfileURL"], "title": r["Title"],
                "bytes": int(r["OriginalSize"] or 0),
                "gender": b["GenderPresentation"], "age": b["AgePresentation"],
                "box": [float(b["XMin"]), float(b["YMin"]), float(b["XMax"]), float(b["YMax"])],
                "occluded": b["IsOccluded"] == "1", "truncated": b["IsTruncated"] == "1",
            }
            n += 1
        print("     joined %d to image metadata" % n)
    bad = {v["licence"] for v in out.values()} - {"https://creativecommons.org/licenses/by/2.0/"}
    if bad:
        # The licence spine is not negotiable: no NC (we are a commercial store), no ND (a
        # generated image is a derivative), no SA (it would infect our own marketing output).
        print("REFUSING: non-CC-BY-2.0 licences present: %s" % bad); sys.exit(1)
    with gzip.open("candidates.json.gz", "wt") as f:
        json.dump(list(out.values()), f)
    print("wrote %d candidates, all CC BY 2.0" % len(out))

main()
