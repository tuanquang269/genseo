import sys
from PIL import Image
pre, out = sys.argv[1], sys.argv[2]
im = Image.open(pre + "-desktop.png").convert("RGB"); w, h = im.size
for n, y in enumerate(range(0, h, 2000)):
    c = im.crop((0, y, w, min(h, y + 2000))); c = c.resize((c.width * 5 // 9, c.height * 5 // 9)); c.save(f"{out}-d{n}.jpg", quality=72)
im = Image.open(pre + "-mobile.png").convert("RGB"); w, h = im.size
k = 4; parts = [im.crop((0, i * h // k, w, (i + 1) * h // k)) for i in range(k)]
m = Image.new("RGB", (w * k + 10 * (k - 1), h // k), "white")
for i, p in enumerate(parts): m.paste(p, (i * (w + 10), 0))
m.save(f"{out}-m.jpg", quality=72); print("ok", h)
