"""Erzeugt das Bollenhut-Signet (nur Krempe + rote Bommeln) als SVG und PNG."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from design import ROT, SCHWARZ, ASSETS, FIRMA, hexrgb
from PIL import Image, ImageDraw, ImageFont

os.makedirs(ASSETS, exist_ok=True)

# Bommeln: (x, y, r) auf einer 120x78-Fläche, hintere Reihe zuerst
BOMMELN = [(36, 25, 12), (60, 19, 13), (84, 25, 12),
           (26, 38, 11), (49, 33, 12), (71, 33, 12), (94, 38, 11)]
ROT_DUNKEL = "8E0B20"          # feine Trennkontur, damit die Bommeln nicht verschmelzen
KREMPE = (60, 52, 55, 12)      # cx, cy, rx, ry

def svg(rot=ROT, schwarz=SCHWARZ):
    b = "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#{rot}" '
                f'stroke="#{ROT_DUNKEL}" stroke-width="1.6"/>' for x, y, r in BOMMELN)
    cx, cy, rx, ry = KREMPE
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 78" '
            f'width="120" height="78" role="img" aria-label="Bollenhut">'
            f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="#{schwarz}"/>{b}</svg>')

def png(pfad, breite=480, rot=ROT, schwarz=SCHWARZ, transparent=True):
    s = breite / 120
    img = Image.new("RGBA", (int(120 * s), int(78 * s)), (0, 0, 0, 0 if transparent else 255))
    d = ImageDraw.Draw(img)
    cx, cy, rx, ry = KREMPE
    d.ellipse([(cx - rx) * s, (cy - ry) * s, (cx + rx) * s, (cy + ry) * s], fill=hexrgb(schwarz))
    for x, y, r in BOMMELN:
        d.ellipse([(x - r) * s, (y - r) * s, (x + r) * s, (y + r) * s],
                  fill=hexrgb(rot), outline=hexrgb(ROT_DUNKEL), width=max(1, int(1.6 * s)))
    img.save(pfad)

def kopflogo(pfad, hoehe=150):
    """Signet + Wortmarke auf schwarzem Grund - Platzhalter bis die Logodatei vorliegt."""
    sig_h = int(hoehe * 0.52)
    sig = Image.new("RGBA", (int(sig_h / 78 * 120), sig_h), (0, 0, 0, 0))
    png("/tmp/_sig.png", breite=sig.width, transparent=True)
    sig = Image.open("/tmp/_sig.png").convert("RGBA")
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"):
        if os.path.exists(p):
            f = ImageFont.truetype(p, int(hoehe * 0.40)); break
    else:
        f = ImageFont.load_default()
    text = "KIKRIPP"
    tmp = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    tb = tmp.textbbox((0, 0), text, font=f)
    breite = max(sig.width, tb[2] - tb[0]) + 8
    img = Image.new("RGBA", (breite, hoehe), (0, 0, 0, 0))
    img.alpha_composite(sig, ((breite - sig.width) // 2, 0))
    ImageDraw.Draw(img).text(((breite - (tb[2] - tb[0])) // 2 - tb[0], sig.height + 4),
                             text, font=f, fill=(255, 255, 255, 255))
    img.save(pfad)

with open(os.path.join(ASSETS, "signet.svg"), "w", encoding="utf-8") as f:
    f.write(svg())
png(os.path.join(ASSETS, "signet.png"), 480)
png(os.path.join(ASSETS, "signet_klein.png"), 120)
kopflogo(os.path.join(ASSETS, "kopflogo.png"), 150)
print("erzeugt:", sorted(os.listdir(ASSETS)))
