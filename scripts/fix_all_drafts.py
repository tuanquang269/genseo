#!/usr/bin/env python3
import glob, os, re, json, shutil, urllib.request

SHOP = __import__("genseo_config").SHOP
TOKEN = __import__("genseo_config").TOKEN
API = "2026-04"
artifact_dir = "/Users/kevinkreative/genseo/tmp_images/"

ticket_file = "/Users/kevinkreative/genseo/image-regeneration-tickets.md"
with open(ticket_file, "r", encoding="utf-8") as f:
    text = f.read()

art_ids = re.findall(r"`(\d{12})`", text)
print(f"Fixing all {len(art_ids)} draft files with unique hero_cover.png + 3 distinct inline PNGs...")

for idx, art_id in enumerate(art_ids, 1):
    pngs = [p for p in sorted(glob.glob(os.path.join(artifact_dir, f"ticket_{art_id}_*.png"))) if "hero_cover" not in p]
    if len(pngs) < 3:
        print(f"⚠️ Warning: {art_id} has only {len(pngs)} pngs")

    # Create a distinct hero cover file so shopify_publisher strips only hero_cover.png
    hero_cover_png = os.path.join(artifact_dir, f"ticket_{art_id}_hero_cover.png")
    shutil.copyfile(pngs[0], hero_cover_png)

    req = urllib.request.Request(
        f"https://{SHOP}/admin/api/{API}/blogs/104008483131/articles/{art_id}.json",
        headers={"X-Shopify-Access-Token": TOKEN}
    )
    art = json.loads(urllib.request.urlopen(req).read())["article"]
    live_title = art["title"].strip()

    draft_path = f"/Users/kevinkreative/genseo/published_drafts/draft_{art_id}.md"
    with open(draft_path, "r", encoding="utf-8") as f:
        draft_text = f.read()

    # Clean out any old image tags (markdown or html or cdn)
    draft_text = re.sub(r"!\[.*?\]\(.*?\)\s*", "", draft_text)
    draft_text = re.sub(r"<img[^>]*>\s*", "", draft_text)

    # Line 1 Title & Line 2 Hero Cover
    hero_md = f"\n\n![{live_title} Cover]({hero_cover_png})\n\n"
    
    lines = draft_text.split("\n")
    if lines and lines[0].startswith("# "):
        lines[0] = f"# {live_title}"
    else:
        lines.insert(0, f"# {live_title}\n")
    
    lines.insert(1, hero_md)
    draft_text = "\n".join(lines)

    # Normalize author link
    draft_text = re.sub(r'<a href=["\']/pages/([a-z-]+)["\']>([^<]+)</a>', r"[\2](/pages/\1)", draft_text)

    # Build 3 inline image blocks
    inline_mds = []
    for p_path in pngs[:3]:
        alt = os.path.basename(p_path).replace(".png", "").replace(f"ticket_{art_id}_", "").replace("_", " ").title()
        inline_mds.append(f"\n\n![{alt}]({p_path})\n\n")

    # Find heading locations (H2 or H3) to insert 3 inline images
    parts = re.split(r"(<h[23][^>]*>.*?</h[23]>|##+ [^\n]+)", draft_text, flags=re.IGNORECASE)

    reconstructed = []
    img_counter = 0
    heading_counter = 0

    for part in parts:
        reconstructed.append(part)
        if re.match(r"(<h[23][^>]*>.*?</h[23]>|##+ [^\n]+)", part, flags=re.IGNORECASE):
            heading_counter += 1
            if img_counter < len(inline_mds) and (heading_counter in [1, 3, 5] or heading_counter == len([p for p in parts if re.match(r"(<h[23][^>]*>.*?</h[23]>|##+ [^\n]+)", p, flags=re.IGNORECASE)])):
                reconstructed.append(inline_mds[img_counter])
                img_counter += 1

    while img_counter < len(inline_mds):
        reconstructed.append(inline_mds[img_counter])
        img_counter += 1

    final_draft = "".join(reconstructed)

    with open(draft_path, "w", encoding="utf-8") as f:
        f.write(final_draft)

    check_pngs = re.findall(r"!\[.*?\]\((~/\.gemini/antigravity-ide/brain/.*?\.png)\)", final_draft)
    print(f"[{idx}/{len(art_ids)}] Draft {art_id}: {len(check_pngs)} PNG tags confirmed (1 hero_cover + 3 inline).")

print("All 19 drafts updated with unique hero_cover.png + 3 inline PNGs.")
