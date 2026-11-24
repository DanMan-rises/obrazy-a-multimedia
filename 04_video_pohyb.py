"""
04 – Video: obraz v čase
========================
Video je řada obrázků. Pozadí = medián všech snímků v čase,
pohyb = to, co se od pozadí liší víc než práh. Dál už je to stejný postup:
práh -> maska -> čištění -> počet oblastí v každém snímku.

Spuštění:
    python 04_video_pohyb.py                 (chodci z data/chodci)
    python 04_video_pohyb.py data/snimky --fps 5

Vlastní video (statická kamera!) rozlož na snímky:
    ffmpeg -i video.mp4 -vf "fps=3,scale=384:-1" data/snimky/s_%03d.jpg
"""
import argparse
import sys
import glob
import os

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

# Windows při přesměrovaném výstupu nepíše UTF-8; ať háčky skript neshodí
if sys.stdout.encoding and sys.stdout.encoding.lower().replace("-", "") != "utf8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

os.makedirs("vystupy", exist_ok=True)   # složka pro výsledky

p = argparse.ArgumentParser()
p.add_argument("slozka", nargs="?", default="data/chodci")
p.add_argument("--fps", type=float, default=3, help="kolik snímků je za sekundu")
p.add_argument("--prah", type=int, default=30,
               help="o kolik úrovní jasu se pixel musí lišit od pozadí")
p.add_argument("--min-plocha", type=int, default=60,
               help="menší oblasti (v px) se nepočítají")
p.add_argument("--snimek", type=int, help="číslo snímku pro ukázku")
p.add_argument("--bez-okna", action="store_true",
               help="jen uložit obrázek, neotvírat okno")
a = p.parse_args()

# ---------------------------------------------------------------- 1) načtení
soubory = sorted(glob.glob(os.path.join(a.slozka, "*.jpg"))
                 + glob.glob(os.path.join(a.slozka, "*.png")))
video = np.stack([np.asarray(Image.open(s).convert("L"), dtype=float)
                  for s in soubory])
print(f"Načteno {len(soubory)} snímků ze složky {a.slozka}")
print("Tvar pole (snímky, výška, šířka):", video.shape)

# ---------------------------------------------------------------- 2) pozadí
# medián v čase: co je na daném místě většinu času, je pozadí
pozadi = np.median(video, axis=0)


# ---------------------------------------------------------------- 3) maska pohybu
def maska_pohybu(snimek):
    maska = np.abs(snimek - pozadi) > a.prah
    maska = ndi.binary_opening(maska, iterations=1)   # odstraní šum
    maska = ndi.binary_closing(maska, iterations=2)   # spojí části postavy
    stitky, pocet = ndi.label(maska)
    if pocet == 0:
        return np.zeros_like(maska), 0
    plochy = ndi.sum_labels(maska, stitky, range(1, pocet + 1))
    velke = np.flatnonzero(plochy >= a.min_plocha) + 1
    return np.isin(stitky, velke), len(velke)


pocty = [maska_pohybu(s)[1] for s in video]
cas = np.arange(len(pocty)) / a.fps
print(f"Počet pohybujících se objektů: nejméně {min(pocty)},"
      f" nejvíc {max(pocty)}, průměrně {np.mean(pocty):.1f}")

# ---------------------------------------------------------------- 4) obrázky
k = a.snimek if a.snimek is not None else int(len(video) * 0.88)
maska_k, pocet_k = maska_pohybu(video[k])
print(f"Ukázkový snímek č. {k} ({k / a.fps:.0f}. sekunda): objektů {pocet_k}")

fig, osy = plt.subplots(2, 2, figsize=(11, 7))
osy[0, 0].imshow(video[k], cmap="gray")
osy[0, 0].set_title(f"1. Snímek č. {k}")
osy[0, 1].imshow(pozadi, cmap="gray")
osy[0, 1].set_title("2. Pozadí: medián všech snímků v čase")
osy[1, 0].imshow(maska_k, cmap="gray")
osy[1, 0].set_title(f"3. Maska pohybu (objektů: {pocet_k})")
for o in (osy[0, 0], osy[0, 1], osy[1, 0]):
    o.axis("off")

osy[1, 1].step(cas, pocty, where="mid", color="#2a6f97")
osy[1, 1].axvline(k / a.fps, color="red", linewidth=1)
osy[1, 1].set_title("4. Počet objektů v čase")
osy[1, 1].set_xlabel("čas [s]")
osy[1, 1].set_ylabel("počet objektů")

plt.tight_layout()
plt.savefig("vystupy/04_video.png", dpi=150)
print("Uloženo: vystupy/04_video.png")
if not a.bez_okna:
    plt.show()
