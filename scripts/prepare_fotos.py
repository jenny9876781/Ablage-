"""HEIC-Uploads -> fotos/F-xxx.jpg  (gedreht, verkleinert, ohne EXIF/GPS, Personen beschnitten)."""
import os, glob
from PIL import Image, ImageOps
import pillow_heif
pillow_heif.register_heif_opener()

QUELLE = "/root/.claude/uploads/5c7acbc8-ee51-57d5-ad6a-f3ae7c3bda74"
ZIEL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fotos")

# Datenschutz: Fotos mit erkennbaren Personen werden beschnitten (Anteil, der oben wegfaellt)
BESCHNITT_OBEN = {95: 0.34, 99: 0.20, 111: 0.42, 28: 0.30}

os.makedirs(ZIEL, exist_ok=True)
dateien = glob.glob(os.path.join(QUELLE, "*.HEIC")) + glob.glob(os.path.join(QUELLE, "*.heic"))
eintraege = []
for f in dateien:
    im = Image.open(f)
    eintraege.append((str(im.getexif().get(306) or ""), os.path.basename(f), f))
eintraege.sort(key=lambda x: (x[0], x[1]))

for i, (dt, bn, f) in enumerate(eintraege, start=1):
    im = ImageOps.exif_transpose(Image.open(f)).convert("RGB")
    if i in BESCHNITT_OBEN:
        w, h = im.size
        im = im.crop((0, int(h * BESCHNITT_OBEN[i]), w, h))
    im.thumbnail((1400, 1400))
    im.save(os.path.join(ZIEL, f"F-{i:03d}.jpg"), quality=82, optimize=True)  # ohne EXIF -> kein GPS

gesamt = sum(os.path.getsize(os.path.join(ZIEL, x)) for x in os.listdir(ZIEL))
print(f"{len(eintraege)} Fotos -> {ZIEL}  ({gesamt//1024//1024} MB)")
print("beschnitten (Personen im Bild):", sorted(BESCHNITT_OBEN))
