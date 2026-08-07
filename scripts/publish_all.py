#!/usr/bin/env python3
import glob, os, re, subprocess

ticket_file = "/Users/kevinkreative/genseo/image-regeneration-tickets.md"
with open(ticket_file, "r", encoding="utf-8") as f:
    text = f.read()

art_ids = re.findall(r"`(\d{12})`", text)
print(f"Publishing and verifying {len(art_ids)} articles...")

success_count = 0
failed_ids = []

for idx, art_id in enumerate(art_ids, 1):
    draft_path = f"/Users/kevinkreative/genseo/published_drafts/draft_{art_id}.md"
    print(f"\n[{idx}/{len(art_ids)}] Publishing article {art_id}...")

    pub_cmd = [
        "python3",
        os.path.expanduser("/Users/kevinkreative/genseo/scripts/shopify_publisher.py"),
        "update",
        draft_path,
        "104008483131",
        art_id
    ]
    res = subprocess.run(pub_cmd, capture_output=True, text=True)

    if "SUCCESS!" not in res.stdout:
        print(f"  ❌ Publish failed for {art_id}: {res.stderr or res.stdout[:200]}")
        failed_ids.append(art_id)
        continue

    print(f"  ✓ Published {art_id}. Verifying live gate...")

    ver_cmd = [
        "python3",
        "/Users/kevinkreative/genseo/scripts/verify_published.py",
        art_id,
        "104008483131"
    ]
    ver_res = subprocess.run(ver_cmd, capture_output=True, text=True)

    if "✓ Live article verified" in ver_res.stdout:
        print(f"  ✓ VERIFICATION PASSED for {art_id}")
        success_count += 1
    else:
        print(f"  ❌ Verification failed for {art_id}: {ver_res.stdout}")
        failed_ids.append(art_id)

print("\n========================================")
print(f"BATCH SUMMARY: {success_count}/{len(art_ids)} PASSED")
if failed_ids:
    print("Failed IDs:", failed_ids)
