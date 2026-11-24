"""
02 – Od fotky k číslu
=====================
Kalibrace -> prahování -> čištění masky -> (rozdělení) -> počet oblastí
-> plochy -> ověření přesnosti.
Používá jen Pillow, NumPy, SciPy a Matplotlib.

Tři příklady z přednášky (spouštěj ze složky demo/):

  1) Řecké mince: světlé objekty na tmavém pozadí, bez kalibrace
     python 02_pocitani_objektu.py

  2) Euromince: kalibrace podle mince 50 c uprostřed (objekt č. 6, průměr 24,25 mm)
     a kontrola proti oficiálním průměrům všech osmi mincí
     python 02_pocitani_objektu.py data/euro_mince.jpg --tmave-objekty --vyhlazeni --rozdelit --ref 6 --ref-mm 24.25 --kontrola 16.25,18.75,21.25,19.75,22.25,24.25,23.25,25.75

  3) Slepené mince: objekty se dotýkají, je potřeba je rozdělit
     python 02_pocitani_objektu.py data/slepene_mince.jpg --tmave-objekty --vyhlazeni --rozdelit --bez-zaplneni --min-plocha 800

Kalibrace (jedna z možností):
  --px 1180 --mm 100      délka měřítka v pixelech a v milimetrech
  --mm-na-px 0.085        rovnou velikost jednoho pixelu
  --ref 6 --ref-mm 24.25  objekt č. 6 má skutečný průměr 24,25 mm
Bez kalibrace vyjdou plochy jen v pixelech.

Úprava obrazu: vždy se odečte rozmazané pozadí (srovná osvětlení). Přepínač
--vyhlazeni navíc vyhladí šum; hodí se u velkých fotek s výrazným reliéfem
(euromince, slepené mince). U malé fotky řeckých mincí drobnosti uklidí čištění.
"""
import argparse
import csv
import os

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

os.makedirs("vystupy", exist_ok=True)   # složka pro výsledky

# ---------------------------------------------------------------- parametry
p = argparse.ArgumentParser()
p.add_argument("obrazek", nargs="?", default="data/recke_mince.png")
p.add_argument("--mm-na-px", type=float, help="kolik mm je jeden pixel")
p.add_argument("--px", type=float, help="délka měřítka v pixelech (na původní fotce)")
p.add_argument("--mm", type=float, help="délka měřítka v milimetrech")
p.add_argument("--ref", type=int, help="číslo objektu se známým průměrem (kalibrace)")
p.add_argument("--ref-mm", type=float, help="skutečný průměr objektu --ref v mm")
p.add_argument("--kontrola", help="skutečné průměry všech objektů v mm, oddělené čárkou")
p.add_argument("--prah", type=int, help="ruční práh 0-255 (jinak Otsu)")
p.add_argument("--tmave-objekty", action="store_true",
               help="objekty jsou tmavší než pozadí")
p.add_argument("--rozdelit", action="store_true",
               help="rozdělit objekty, které se dotýkají")
p.add_argument("--bez-zaplneni", action="store_true",
               help="nezaplňovat velké díry (mezery mezi slepenými objekty)")
p.add_argument("--vyhlazeni", action="store_true",
               help="před prahováním ještě vyhladí šum (velké fotky s výrazným reliéfem)")
p.add_argument("--min-plocha", type=int, default=100,
               help="menší oblasti (v px) se zahodí jako šum")
p.add_argument("--max-rozmer", type=int, default=1600,
               help="větší obrázek se před zpracováním zmenší na tuto délku")
p.add_argument("--bez-okna", action="store_true",
               help="jen uložit obrázky, neotvírat okno")
a = p.parse_args()

if a.mm_na_px:
    mm_na_px = a.mm_na_px
elif a.px and a.mm:
    mm_na_px = a.mm / a.px
else:
    mm_na_px = None


# ---------------------------------------------------------------- funkce
def otsu(obraz):
    """Otsuův práh: hledá jas, který nejlíp rozdělí histogram na dvě třídy."""
    hist = np.bincount(obraz.ravel(), minlength=256).astype(float)
    podil = hist / hist.sum()               # pravděpodobnost každého jasu
    vaha = np.cumsum(podil)                 # podíl pixelů pod prahem
    stred = np.cumsum(podil * np.arange(256))
    celkovy_stred = stred[-1]
    with np.errstate(divide="ignore", invalid="ignore"):
        rozptyl_mezi = (celkovy_stred * vaha - stred) ** 2 / (vaha * (1 - vaha))
    return int(np.nanargmax(rozptyl_mezi))  # práh s největším rozptylem


def zaplnit_male_diry(maska, max_dira):
    """Zaplní jen díry menší než max_dira pixelů (odlesky uvnitř objektů)."""
    diry = ndi.binary_fill_holes(maska) & ~maska
    oznacene, pocet = ndi.label(diry)
    if pocet == 0:
        return maska
    velikosti = ndi.sum_labels(diry, oznacene, range(1, pocet + 1))
    male = np.isin(oznacene, np.flatnonzero(velikosti < max_dira) + 1)
    return maska | male


def rozdelit(maska, min_polomer):
    """Rozdělí dotýkající se objekty podle mapy vzdáleností.

    Stejný princip jako Process > Binary > Watershed ve Fiji:
    1. mapa vzdáleností: každý pixel objektu dostane vzdálenost k pozadí,
    2. vrcholy mapy jsou středy objektů (nejdál od okraje),
    3. každý pixel připadne středu, jehož okraj je mu nejblíž.
    U dvou kruhů, které se dotýkají, vede hranice přesně bodem dotyku.
    """
    vzdalenost = ndi.distance_transform_edt(maska)
    okoli = 2 * min_polomer + 1
    vrcholy = (vzdalenost == ndi.maximum_filter(vzdalenost, size=okoli)) \
        & (vzdalenost >= min_polomer)
    skupiny, pocet = ndi.label(ndi.binary_dilation(vrcholy, iterations=2))
    stredy = ndi.maximum_position(vzdalenost, skupiny, range(1, pocet + 1))

    yy, xx = np.nonzero(maska)
    # vzdálenost pixelu od okraje kruhu kolem každého středu
    skore = np.stack([np.hypot(yy - cy, xx - cx) - vzdalenost[cy, cx]
                      for cy, cx in stredy])
    stitky = np.zeros(maska.shape, np.int32)
    stitky[yy, xx] = np.argmin(skore, axis=0) + 1
    return stitky, pocet


def poradi_cteni(stredy, polomer):
    """Seřadí objekty jako text: po řádcích shora dolů, v řádku zleva doprava."""
    podle_y = sorted(range(len(stredy)), key=lambda i: stredy[i][0])
    radky, aktualni, zacatek = [], [], None
    for i in podle_y:
        if zacatek is None or stredy[i][0] - zacatek > polomer:
            if aktualni:
                radky.append(aktualni)
            aktualni, zacatek = [], stredy[i][0]
        aktualni.append(i)
    radky.append(aktualni)
    return [i for radek in radky for i in sorted(radek, key=lambda i: stredy[i][1])]


# ---------------------------------------------------------------- 1) načtení
obrazek = Image.open(a.obrazek).convert("L")
print(f"Obrázek {a.obrazek}: {obrazek.width} x {obrazek.height} px")

# velkou fotku zmenšíme, jinak filtry běží zbytečně dlouho
if max(obrazek.size) > a.max_rozmer:
    pomer = a.max_rozmer / max(obrazek.size)
    obrazek = obrazek.resize((round(obrazek.width * pomer),
                              round(obrazek.height * pomer)), Image.LANCZOS)
    print(f"Zmenšeno na {obrazek.width} x {obrazek.height} px")
    if mm_na_px:
        mm_na_px /= pomer                  # méně pixelů = každý pokrývá víc mm
sedy = np.asarray(obrazek)

# ---------------------------------------------------------------- 2) naivní pokus
prah_naivni = a.prah if a.prah is not None else otsu(sedy)
maska_naivni = sedy < prah_naivni if a.tmave_objekty else sedy > prah_naivni
_, pocet_naivni = ndi.label(maska_naivni)
print(f"Naivně: práh {prah_naivni} -> oblastí: {pocet_naivni}")

# ---------------------------------------------------------------- 3) předzpracování
# odečtení silně rozmazaného pozadí srovná nerovnoměrné osvětlení,
# s přepínačem --vyhlazeni se navíc vyhladí šum
velikost = max(sedy.shape)
if a.vyhlazeni:
    vyhlazeny = ndi.gaussian_filter(sedy.astype(float), sigma=velikost / 200)
else:
    vyhlazeny = sedy.astype(float)
pozadi = ndi.gaussian_filter(sedy.astype(float), sigma=velikost / 10)
rozdil = vyhlazeny - pozadi
upraveny = ((rozdil - rozdil.min()) / (rozdil.max() - rozdil.min()) * 255)
upraveny = upraveny.astype(np.uint8)

# ---------------------------------------------------------------- 4) prahování
prah = a.prah if a.prah is not None else otsu(upraveny)
maska = upraveny < prah if a.tmave_objekty else upraveny > prah

# ---------------------------------------------------------------- 5) čištění masky
maska = ndi.binary_opening(maska, iterations=2)   # odstraní drobné tečky
if a.bez_zaplneni:
    # velké díry mohou být mezery mezi slepenými objekty: ty necháme
    maska = zaplnit_male_diry(maska, a.min_plocha / 50)
else:
    maska = ndi.binary_fill_holes(maska)          # zaplní díry v objektech

# ---------------------------------------------------------------- 6) označení oblastí
_, pocet_spojenych = ndi.label(maska)
if a.rozdelit:
    min_polomer = max(3, int(np.sqrt(a.min_plocha / np.pi)))
    stitky, pocet = rozdelit(maska, min_polomer)
else:
    stitky, pocet = ndi.label(maska)
indexy = np.arange(1, pocet + 1)
plochy_px = ndi.sum_labels(maska, stitky, index=indexy)

# zahodíme příliš malé oblasti
velke = plochy_px >= a.min_plocha
indexy, plochy_px = indexy[velke], plochy_px[velke]
stredy = ndi.center_of_mass(maska, stitky, indexy)

# očíslujeme objekty jako text: po řádcích, zleva doprava
polomer = np.sqrt(np.median(plochy_px) / np.pi)
poradi = poradi_cteni(stredy, polomer)
indexy, plochy_px = indexy[poradi], plochy_px[poradi]
stredy = [stredy[i] for i in poradi]
prevod = np.zeros(stitky.max() + 1, np.int32)
prevod[indexy] = np.arange(1, len(indexy) + 1)
stitky = prevod[stitky]                    # objekt č. 1, 2, 3 ... v pořadí čtení

if a.rozdelit:
    print(f"Po vyčištění: práh {prah} -> souvislých oblastí: {pocet_spojenych},"
          f" po rozdělení objektů: {len(indexy)}")
else:
    print(f"Po vyčištění: práh {prah} -> objektů: {len(indexy)}")

# ---------------------------------------------------------------- 7) kalibrace a měření
prumery_px = 2 * np.sqrt(plochy_px / np.pi)   # průměr kruhu se stejnou plochou

if a.ref and a.ref_mm:
    mm_na_px = a.ref_mm / prumery_px[a.ref - 1]
    print(f"Kalibrace podle objektu č. {a.ref}: {a.ref_mm} mm"
          f" = {prumery_px[a.ref - 1]:.1f} px")

if mm_na_px:
    plochy = plochy_px * mm_na_px ** 2      # plocha roste s druhou mocninou
    prumery = prumery_px * mm_na_px
    jednotka, jednotka_d = "mm²", "mm"
    print(f"Kalibrace: 1 px = {mm_na_px:.4f} mm")
else:
    plochy, prumery = plochy_px, prumery_px
    jednotka, jednotka_d = "px", "px"
    print("Bez kalibrace: plochy jsou v pixelech")

print(f"\n{'#':>3} {'plocha [' + jednotka + ']':>14} {'průměr [' + jednotka_d + ']':>12}")
for i, (pl, pr) in enumerate(zip(plochy, prumery), start=1):
    print(f"{i:>3} {pl:>14.1f} {pr:>12.2f}")
print(f"\nPočet: {len(plochy)}   průměrná plocha: {plochy.mean():.1f} {jednotka}"
      f"   celkem: {plochy.sum():.1f} {jednotka}")

# ---------------------------------------------------------------- 8) ověření přesnosti
skutecne = None
if a.kontrola:
    skutecne = np.array([float(x) for x in a.kontrola.split(",")])
    if len(skutecne) != len(prumery):
        print(f"\nKontrola: zadáno {len(skutecne)} průměrů,"
              f" ale nalezeno {len(prumery)} objektů. Kontrolu přeskakuji.")
        skutecne = None
    else:
        chyby = (prumery - skutecne) / skutecne * 100
        print(f"\nOvěření přesnosti (průměry v {jednotka_d}):")
        print(f"{'#':>3} {'skutečný':>9} {'změřený':>9} {'chyba':>8}")
        for i, (sk, zm, ch) in enumerate(zip(skutecne, prumery, chyby), start=1):
            znacka = "   <- kalibrace" if i == a.ref else ""
            print(f"{i:>3} {sk:>9.2f} {zm:>9.2f} {ch:>+7.1f} %{znacka}")
        print(f"Průměrná absolutní chyba: {np.abs(chyby).mean():.1f} %"
              f"   největší: {np.abs(chyby).max():.1f} %")

with open("vystupy/02_plochy.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    hlavicka = ["objekt", f"plocha_{'mm2' if mm_na_px else 'px'}",
                f"prumer_{jednotka_d}", "x_px", "y_px"]
    if skutecne is not None:
        hlavicka += ["skutecny_prumer_mm", "chyba_procent"]
    w.writerow(hlavicka)
    for i in range(len(plochy)):
        radek = [i + 1, round(float(plochy[i]), 2), round(float(prumery[i]), 3),
                 round(float(stredy[i][1]), 1), round(float(stredy[i][0]), 1)]
        if skutecne is not None:
            radek += [skutecne[i], round(float(chyby[i]), 2)]
        w.writerow(radek)

# ---------------------------------------------------------------- 9) obrázky
fig, osy = plt.subplots(2, 3, figsize=(14, 8))

osy[0, 0].imshow(sedy, cmap="gray")
osy[0, 0].set_title("1. Originál (stupně šedi)")

osy[0, 1].hist(sedy.ravel(), bins=256, range=(0, 255), color="#444444")
osy[0, 1].axvline(prah_naivni, color="red")
osy[0, 1].set_title(f"2. Histogram a práh = {prah_naivni}")

osy[0, 2].imshow(maska_naivni, cmap="gray")
osy[0, 2].set_title(f"3. Naivní maska (oblastí: {pocet_naivni})")

osy[1, 0].imshow(maska, cmap="gray")
osy[1, 0].set_title(f"4. Maska po vyčištění (oblastí: {pocet_spojenych})")

barvy = np.ma.masked_equal(stitky, 0)
osy[1, 1].imshow(sedy, cmap="gray")
osy[1, 1].imshow(barvy % 20, cmap="tab20", alpha=0.6, interpolation="nearest",
                 vmin=0, vmax=19)
for i, (y, x) in enumerate(stredy, start=1):
    osy[1, 1].text(x, y, str(i), color="white", ha="center", va="center",
                   fontsize=8, fontweight="bold")
osy[1, 1].set_title(f"5. Označené objekty (počet: {len(indexy)})")

if skutecne is not None:
    cisla = np.arange(1, len(chyby) + 1)
    osy[1, 2].bar(cisla, chyby, color="#2a6f97")
    osy[1, 2].axhline(0, color="#444444", linewidth=1)
    osy[1, 2].set_xticks(cisla)
    osy[1, 2].set_title("6. Chyba změřeného průměru")
    osy[1, 2].set_xlabel("objekt")
    osy[1, 2].set_ylabel("chyba [%]")
else:
    osy[1, 2].hist(plochy, bins=12, color="#2a6f97", edgecolor="white")
    osy[1, 2].set_title("6. Rozložení ploch")
    osy[1, 2].set_xlabel(f"plocha [{jednotka}]")
    osy[1, 2].set_ylabel("počet objektů")

for o in (osy[0, 0], osy[0, 2], osy[1, 0], osy[1, 1]):
    o.axis("off")
plt.tight_layout()
plt.savefig("vystupy/02_postup.png", dpi=150)
print("Uloženo: vystupy/02_postup.png, vystupy/02_plochy.csv")
if not a.bez_okna:
    plt.show()
