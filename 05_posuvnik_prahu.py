"""
05 – Práh naživo
================
Posuvníkem měníš práh a hned vidíš masku i počet oblastí.
Ukazuje, že práh je rozhodnutí: malá změna čísla, úplně jiný výsledek.
Prahuje se upravený obraz (srovnání osvětlení jako ve skriptu 02).
S přepínačem --bez-upravy se prahuje přímo fotka.

Ovládání: táhni modrý pruh myší (nebo klikni kamkoli na něj),
případně šipky na klávesnici: doleva/doprava o 1, dolů/nahoru o 10.
Okno musí být aktivní: jednou do něj klikni.

Spuštění:
    python 05_posuvnik_prahu.py
    python 05_posuvnik_prahu.py --bez-upravy
    python 05_posuvnik_prahu.py data/euro_mince.jpg --tmave-objekty --vyhlazeni
"""
import argparse
import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Slider
from PIL import Image
from scipy import ndimage as ndi

os.makedirs("vystupy", exist_ok=True)   # složka pro výsledky

# šipky doleva/doprava ovládají posuvník, ne historii zobrazení
for klic in ("keymap.back", "keymap.forward"):
    plt.rcParams[klic] = [k for k in plt.rcParams[klic] if k not in ("left", "right")]

p = argparse.ArgumentParser()
p.add_argument("obrazek", nargs="?", default="data/recke_mince.png")
p.add_argument("--tmave-objekty", action="store_true",
               help="objekty jsou tmavší než pozadí")
p.add_argument("--bez-upravy", action="store_true",
               help="prahuje přímo fotku, bez srovnání osvětlení")
p.add_argument("--vyhlazeni", action="store_true",
               help="před prahováním ještě vyhladí šum (jako ve skriptu 02)")
p.add_argument("--max-rozmer", type=int, default=800,
               help="větší obrázek se zmenší, aby posuvník reagoval plynule")
a = p.parse_args()

# ---------------------------------------------------------------- načtení
obrazek = Image.open(a.obrazek).convert("L")
if max(obrazek.size) > a.max_rozmer:
    pomer = a.max_rozmer / max(obrazek.size)
    obrazek = obrazek.resize((round(obrazek.width * pomer),
                              round(obrazek.height * pomer)), Image.LANCZOS)
sedy = np.asarray(obrazek)

# úprava obrazu stejně jako ve skriptu 02: fotka minus rozmazané pozadí
if not a.bez_upravy:
    velikost = max(sedy.shape)
    if a.vyhlazeni:
        vyhlazeny = ndi.gaussian_filter(sedy.astype(float), sigma=velikost / 200)
    else:
        vyhlazeny = sedy.astype(float)
    pozadi = ndi.gaussian_filter(sedy.astype(float), sigma=velikost / 10)
    rozdil = vyhlazeny - pozadi
    sedy = ((rozdil - rozdil.min()) / (rozdil.max() - rozdil.min()) * 255).astype(np.uint8)


def otsu(obraz):
    """Otsuův práh (stejná funkce jako ve skriptu 02)."""
    hist = np.bincount(obraz.ravel(), minlength=256).astype(float)
    podil = hist / hist.sum()
    vaha = np.cumsum(podil)
    stred = np.cumsum(podil * np.arange(256))
    with np.errstate(divide="ignore", invalid="ignore"):
        rozptyl = (stred[-1] * vaha - stred) ** 2 / (vaha * (1 - vaha))
    return int(np.nanargmax(rozptyl))


def spocitej(prah):
    """Vrátí masku a počet souvislých oblastí (bez jakéhokoli čištění)."""
    maska = sedy < prah if a.tmave_objekty else sedy > prah
    _, pocet = ndi.label(maska)
    return maska, pocet


# ---------------------------------------------------------------- okno
prah0 = otsu(sedy)
maska, pocet = spocitej(prah0)

fig = plt.figure(figsize=(13, 6.5))
ax_orig = fig.add_axes([0.03, 0.30, 0.30, 0.62])
ax_maska = fig.add_axes([0.36, 0.30, 0.30, 0.62])
ax_hist = fig.add_axes([0.71, 0.36, 0.27, 0.50])
ax_slider = fig.add_axes([0.12, 0.10, 0.76, 0.05])

ax_orig.imshow(sedy, cmap="gray", vmin=0, vmax=255)
ax_orig.set_title("Fotka bez úpravy" if a.bez_upravy else "Upravený obraz")
obr_maska = ax_maska.imshow(maska, cmap="gray", vmin=0, vmax=1)
for o in (ax_orig, ax_maska):
    o.axis("off")

ax_hist.hist(sedy.ravel(), bins=256, range=(0, 255), color="#444444")
ax_hist.axvline(prah0, color="#999999", linestyle="--", label=f"Otsu = {prah0}")
cara = ax_hist.axvline(prah0, color="red", label="tvůj práh")
ax_hist.set_title("Histogram jasu")
ax_hist.set_xlabel("jas")
ax_hist.legend(loc="upper right", fontsize=9)

posuvnik = Slider(ax_slider, "práh", 0, 255, valinit=prah0, valstep=1)


def popisek(prah, pocet):
    return f"Práh {int(prah)} -> oblastí: {pocet}"


titulek = ax_maska.set_title(popisek(prah0, pocet), fontsize=14)


def zmena(hodnota):
    maska, pocet = spocitej(hodnota)
    obr_maska.set_data(maska)
    cara.set_xdata([hodnota, hodnota])
    titulek.set_text(popisek(hodnota, pocet))
    fig.canvas.draw_idle()


posuvnik.on_changed(zmena)

# ovládání klávesnicí
KROKY = {"left": -1, "right": 1, "down": -10, "up": 10}


def klavesa(udalost):
    if udalost.key in KROKY:
        posuvnik.set_val(int(np.clip(posuvnik.val + KROKY[udalost.key], 0, 255)))


fig.canvas.mpl_connect("key_press_event", klavesa)
fig.text(0.5, 0.02, "Myší táhni modrý pruh, nebo šipky: ← → o 1, ↓ ↑ o 10",
         ha="center", fontsize=10, color="#555555")

plt.savefig("vystupy/05_posuvnik.png", dpi=120)
print(f"Otsu: {prah0}. Táhni posuvníkem myší, nebo použij šipky (← → o 1, ↓ ↑ o 10).")
print("Uloženo: vystupy/05_posuvnik.png (záloha pro prezentaci)")
plt.show()
