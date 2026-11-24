"""
06 – Euromince: jsou čísla správně?
===================================
Na fotce osmi euromincí známe skutečné průměry (podle ECB), takže umíme
zkontrolovat, jak přesně měříme. Skript:

  1) najde mince stejným postupem jako skript 02 (zavolá ho, výsledek
     v pixelech si přečte z vystupy/02_plochy.csv),
  2) kalibruje JEDNOU mincí (výchozí 50 c) a spočítá chybu každé mince,
  3) kalibruje PODLE POLOHY: fotka není focená kolmo, takže počet pixelů
     na 1 mm klesá zleva doprava. Pro každou minci se měřítko odhadne
     z přímky proložené ostatními sedmi mincemi (mince sama sebe nekalibruje).

Spuštění:
    python 06_euromince.py            kalibrace na 50 c (mince č. 6)
    python 06_euromince.py --ref 8    kalibrace na 2 € v pravém dolním rohu

Mince jsou očíslované po řádcích zleva doprava: 1 c, 2 c, 5 c, 10 c,
20 c, 50 c, 1 €, 2 €. Skript je napsaný pro tuto fotku, protože zná
skutečné průměry jejích mincí.
"""
import argparse
import csv
import os
import subprocess
import sys

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

# Windows při přesměrovaném výstupu nepíše UTF-8; ať háčky skript neshodí
if sys.stdout.encoding and sys.stdout.encoding.lower().replace("-", "") != "utf8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FOTKA = "data/euro_mince.jpg"
NAZVY = ["1 c", "2 c", "5 c", "10 c", "20 c", "50 c", "1 €", "2 €"]
ECB = np.array([16.25, 18.75, 21.25, 19.75, 22.25, 24.25, 23.25, 25.75])  # průměry v mm
ORANZOVA, MODRA = "#BF3F1B", "#0F78A8"   # jedna mince / podle polohy

p = argparse.ArgumentParser()
p.add_argument("--ref", type=int, default=6, choices=range(1, 9),
               help="číslo kalibrační mince (1 až 8), výchozí 6 = 50 c")
p.add_argument("--bez-okna", action="store_true",
               help="jen uložit obrázek, neotvírat okno")
a = p.parse_args()
os.chdir(os.path.dirname(os.path.abspath(__file__)))   # cesty data/ a vystupy/ ke skriptu
os.makedirs("vystupy", exist_ok=True)
r = a.ref - 1

# ---------------------------------------------------------------- 1) mince najde skript 02
print("Hledám mince skriptem 02 ...")
# Windows při přesměrovaném výstupu nepíše UTF-8 a háčky by skript 02 shodily
prostredi = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
vysledek = subprocess.run([sys.executable, "02_pocitani_objektu.py", FOTKA, "--tmave-objekty",
                           "--vyhlazeni", "--rozdelit", "--bez-okna"],
                          env=prostredi, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                          text=True, encoding="utf-8", errors="replace")
if vysledek.returncode != 0:
    sys.exit("Skript 02 skončil chybou:\n" + vysledek.stderr)
with open("vystupy/02_plochy.csv", encoding="utf-8") as f:
    radky = list(csv.DictReader(f))
if len(radky) != len(ECB):
    sys.exit(f"Skript 02 našel {len(radky)} objektů místo {len(ECB)}.")

# skript 02 velkou fotku zmenšuje, přepočteme pixely zpět na původní fotku
fotka = Image.open(FOTKA).convert("RGB")
k = max(fotka.size) / min(max(fotka.size), 1600)
prumer_px = np.array([float(x["prumer_px"]) for x in radky]) * k
x = np.array([float(x["x_px"]) for x in radky]) * k
y = np.array([float(x["y_px"]) for x in radky]) * k
px_na_mm = prumer_px / ECB                  # skutečné měřítko v místě každé mince

# ---------------------------------------------------------------- 2) kalibrace jednou mincí
meritko = px_na_mm[r]
prumer_1 = prumer_px / meritko
chyba_1 = (prumer_1 - ECB) / ECB * 100

# ---------------------------------------------------------------- 3) kalibrace podle polohy
prumer_2 = np.zeros(len(ECB))
for i in range(len(ECB)):
    ostatni = np.arange(len(ECB)) != i
    sklon, posun = np.polyfit(x[ostatni], px_na_mm[ostatni], 1)   # přímka bez mince i
    prumer_2[i] = prumer_px[i] / (posun + sklon * x[i])
chyba_2 = (prumer_2 - ECB) / ECB * 100
sklon, posun = np.polyfit(x, px_na_mm, 1)                         # přímka ze všech, pro graf

# ---------------------------------------------------------------- výpis
print(f"\nJedna mince: {NAZVY[r]} má {ECB[r]} mm = {prumer_px[r]:.0f} px,"
      f" tedy {meritko:.2f} px na 1 mm")
print(f"Podle polohy: px na 1 mm ≈ {posun:.1f} {sklon * 1000:+.2f} × (x / 1000 px)\n")
print(f"{'#':>2} {'mince':>5} {'ECB [mm]':>9} {'jedna mince':>12} {'chyba':>7}"
      f" {'podle polohy':>13} {'chyba':>7}")
for i in range(len(ECB)):
    c1 = "kalibr." if i == r else f"{chyba_1[i]:+.1f} %"
    print(f"{i + 1:>2} {NAZVY[i]:>5} {ECB[i]:>9.2f} {prumer_1[i]:>12.2f} {c1:>7}"
          f" {prumer_2[i]:>13.2f} {chyba_2[i]:>+6.1f} %")
for nazev, ch in ((f"Jedna mince ({NAZVY[r]})", chyba_1), ("Podle polohy", chyba_2)):
    j = int(np.abs(ch).argmax())
    print(f"{nazev:>18}: průměrná chyba {np.abs(ch).mean():.1f} %,"
          f" největší {abs(ch[j]):.1f} % ({NAZVY[j]})")

# ---------------------------------------------------------------- obrázek
fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(17, 5.4),
                                    gridspec_kw={"width_ratios": [1.15, 1, 1]})
ax1.imshow(fotka)
for i in range(len(ECB)):
    ax1.text(x[i], y[i], str(i + 1), ha="center", va="center", fontsize=15,
             fontweight="bold", color="white",
             bbox=dict(boxstyle="circle", fc=ORANZOVA if i == r else "#16202B", ec="none"))
ax1.set_title(f"Mince 1–8, oranžově kalibrační ({NAZVY[r]})")
ax1.axis("off")

for i in range(len(ECB)):
    ax2.plot([x[i], x[i]], [meritko, px_na_mm[i]], color=ORANZOVA, lw=2, alpha=0.7)
ax2.axhline(meritko, color=ORANZOVA, lw=2, ls="--", label=f"jedna mince ({NAZVY[r]})")
xx = np.array([0, fotka.width])
ax2.plot(xx, posun + sklon * xx, color=MODRA, lw=2, label="podle polohy (přímka)")
ax2.scatter(x, px_na_mm, s=60, color="#16202B", zorder=3)
POPISKY = {"1 c": (8, 4), "2 c": (8, 6), "5 c": (-30, -18), "10 c": (8, 4),
           "20 c": (-40, -16), "50 c": (6, -18), "1 €": (8, 4), "2 €": (8, 4)}
for i in range(len(ECB)):
    ax2.annotate(NAZVY[i], (x[i], px_na_mm[i]), xytext=POPISKY.get(NAZVY[i], (7, 5)),
                 textcoords="offset points")
ax2.set_xlim(0, fotka.width)
ax2.set_xlabel("poloha mince na fotce zleva [px]")
ax2.set_ylabel("pixelů na 1 mm")
ax2.set_title("Měřítko se mění s polohou")
ax2.legend(loc="upper right", frameon=False)
ax2.grid(alpha=0.3)

pozice = np.arange(len(ECB))
ax3.bar(pozice - 0.2, chyba_1, width=0.38, color=ORANZOVA, label=f"jedna mince ({NAZVY[r]})")
ax3.bar(pozice + 0.2, chyba_2, width=0.38, color=MODRA, label="podle polohy")
ax3.axhline(0, color="#16202B", lw=1)
ax3.set_xticks(pozice, NAZVY)
ax3.set_ylabel("chyba průměru [%]")
ax3.set_title(f"Největší chyba: {np.abs(chyba_1).max():.1f} % → {np.abs(chyba_2).max():.1f} %")
ax3.legend(loc="lower left", frameon=False)
ax3.grid(axis="y", alpha=0.3)

fig.tight_layout()
fig.savefig("vystupy/06_euromince.png", dpi=110)
print("\nUloženo: vystupy/06_euromince.png")
if not a.bez_okna:
    plt.show()
