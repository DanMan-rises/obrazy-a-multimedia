"""
01 – Obraz je matice čísel
==========================
Ukázka k teorii: načtení obrázku, převod na matici, histogram.

Spuštění:
    python 01_obraz_zaklady.py data/euro_mince.jpg
(bez argumentu se použije data/recke_mince.png)
"""
import os
import sys

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

os.makedirs("vystupy", exist_ok=True)   # složka pro výsledky

cesta = sys.argv[1] if len(sys.argv) > 1 else "data/recke_mince.png"

# 1) Pillow načte soubor, NumPy z něj udělá matici
barevny = Image.open(cesta)
print("Soubor:      ", cesta)
print("Rozměr (px): ", barevny.size, " režim:", barevny.mode)

sedy = np.asarray(barevny.convert("L"))  # "L" = 8bit stupně šedi
print("Matice:      ", sedy.shape, sedy.dtype)
print("Min / max:   ", sedy.min(), "/", sedy.max())

# 2) Výřez 8x8 pixelů jako čísla – obraz opravdu JE tabulka čísel.
#    Výřez bereme tam, kde se jas mění nejvíc (hrana objektu).
gy, gx = np.gradient(sedy.astype(float))
r, s = np.unravel_index(np.argmax(np.hypot(gx, gy)), sedy.shape)
r = int(np.clip(r - 4, 0, sedy.shape[0] - 8))
s = int(np.clip(s - 4, 0, sedy.shape[1] - 8))
print(f"\nVýřez 8x8 pixelů na hraně objektu (řádek {r}, sloupec {s}):")
print(sedy[r:r + 8, s:s + 8])

# 3) Histogram: kolik pixelů má jaký jas
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))
ax1.imshow(sedy, cmap="gray", vmin=0, vmax=255)
ax1.set_title("Obraz ve stupních šedi")
ax1.axis("off")

ax2.hist(sedy.ravel(), bins=256, range=(0, 255), color="#444444")
ax2.set_title("Histogram jasu")
ax2.set_xlabel("jas (0 = černá, 255 = bílá)")
ax2.set_ylabel("počet pixelů")

plt.tight_layout()
plt.savefig("vystupy/01_histogram.png", dpi=150)
print("\nUloženo: vystupy/01_histogram.png")
plt.show()
