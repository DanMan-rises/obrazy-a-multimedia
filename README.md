# Obrazy a multimédia – demo skripty

Skripty k referátu *Obrazy a multimédia: jak z fotky udělat číslo* (zpracování dat,
PřF UJEP). Ukazují kalibraci, prahování, počet oblastí a jejich plochy na obrázcích
a stejný princip na zvuku a videu. Používají jen Pillow, NumPy, SciPy a Matplotlib.

## Stažení

Zelené tlačítko **Code → Download ZIP**, nebo:

```
git clone https://github.com/DanMan-rises/obrazy-a-multimedia.git
```

## Instalace

```
pip install pillow numpy scipy matplotlib
```

## Struktura

```
obrazy-a-multimedia/
  01_obraz_zaklady.py      obraz jako matice, histogram
  02_pocitani_objektu.py   kalibrace, prahování, rozdělení, počet, plochy, ověření
  03_zvuk_klepani.py       stejný princip na zvuku
  04_video_pohyb.py        stejný princip na videu
  05_posuvnik_prahu.py     práh naživo: posuvník, maska a počet oblastí
  06_euromince.py          euromince: přesnost, kalibrace jednou mincí a podle polohy
  fiji_makro.ijm           referenční makro pro Fiji (euromince)
  data/                    obrázky, zvuk a snímky videa (viz Zdroje níže)
  vystupy/                 sem se ukládají obrázky a CSV
```

Skripty spouštěj z hlavní složky repozitáře (kvůli cestám `data/` a `vystupy/`).

Skript 03 při otevření grafů klepání rovnou přehraje (vypneš přepínačem `--bez-zvuku`).
Posuvník (skript 05) ovládáš myší (táhni modrý pruh) nebo šipkami: ← → o 1, ↓ ↑ o 10.
Okno musí být aktivní, takže do něj nejdřív jednou klikni.

## Data

| Soubor | Co na něm je | K čemu |
| --- | --- | --- |
| `data/recke_mince.png` | 24 řeckých mincí, světlé na tmavém pozadí | prahování a čištění masky |
| `data/euro_mince.jpg` | sada 8 euromincí, tmavé na světlém pozadí | kalibrace a ověření přesnosti |
| `data/slepene_mince.jpg` | 24 stejných mincí, které se dotýkají | rozdělení (watershed) |
| `data/klepani.wav` | 5 s klepání na dveře, 8 zaklepání | zvuk: práh hlasitosti a úseky |
| `data/chodci/` | 239 snímků ze statické kamery, 3 za sekundu | video: pozadí a pohyb |

## Spuštění

```
python 01_obraz_zaklady.py
python 02_pocitani_objektu.py
python 05_posuvnik_prahu.py
python 05_posuvnik_prahu.py --bez-upravy
python 06_euromince.py
python 06_euromince.py --ref 8
python 02_pocitani_objektu.py data/slepene_mince.jpg --tmave-objekty --vyhlazeni --rozdelit --bez-zaplneni --min-plocha 800
python 03_zvuk_klepani.py
python 04_video_pohyb.py
```

Skript 06 najde euromince skriptem 02 a pak je kalibruje dvakrát: jednou mincí
(výchozí 50 c, s `--ref 8` na 2 €) a podle polohy, protože fotka není focená kolmo.
Vypíše chybu každé mince a uloží graf `vystupy/06_euromince.png`. Totéž bez
kalibrace podle polohy dá i samotný skript 02:
`python 02_pocitani_objektu.py data/euro_mince.jpg --tmave-objekty --vyhlazeni --rozdelit --ref 6 --ref-mm 24.25 --kontrola 16.25,18.75,21.25,19.75,22.25,24.25,23.25,25.75`

Skripty 03 a 04 bez argumentu použijí `data/klepani.wav` a `data/chodci/`.
U jiné nahrávky můžeš upravit práh: `python 03_zvuk_klepani.py data/vlastni_nahravka.wav --prah 0.3`
(podíl největší hlasitosti). U videa vybereš snímek přepínačem `--snimek 100`.

## Přepínače skriptu 02

| Přepínač | Co dělá |
| --- | --- |
| `--tmave-objekty` | objekty jsou tmavší než pozadí |
| `--vyhlazeni` | před prahováním vyhladí šum (Gaussian blur); hodí se u velkých fotek s výrazným reliéfem |
| `--prah 120` | ruční práh místo Otsuovy metody |
| `--rozdelit` | rozdělí objekty, které se dotýkají (princip jako Watershed ve Fiji) |
| `--bez-zaplneni` | nezaplní velké díry; nutné, když mezi slepenými objekty zbydou mezery |
| `--min-plocha 800` | oblasti menší než tolik pixelů zahodí; při `--rozdelit` určuje i nejmenší čekaný poloměr |
| `--ref 6 --ref-mm 24.25` | kalibrace: objekt č. 6 (50 c uprostřed) má skutečný průměr 24,25 mm |
| `--px 1180 --mm 100` | kalibrace měřítkem: 100 mm odpovídá 1 180 px původní fotky |
| `--kontrola 16.25,...` | skutečné průměry všech objektů v pořadí čísel; vypíše chybu měření |
| `--max-rozmer 1600` | větší fotku zmenší na tuto delší stranu a kalibraci přepočítá |
| `--bez-okna` | jen uloží obrázky do `vystupy/` |

Objekty jsou očíslované jako text: po řádcích shora dolů, v řádku zleva
doprava. Na fotce euromincí tedy 1 = 1 cent, 6 = 50 centů, 8 = 2 eura.

Kalibruje se na 50 c uprostřed: fotka není focená kolmo, takže mince na krajích
mají jiné měřítko. S kalibrací na 2 € v rohu (`--ref 8 --ref-mm 25.75`) vyjde
chyba až 16 %, s kalibrací na 50 c asi 8 %.

## Na jaké obrázky skript 02 funguje

Dobře funguje, když se objekty od pozadí liší jasem (světlé na tmavém, nebo tmavé
na světlém s `--tmave-objekty`), jsou zhruba stejně velké a moc se nepřekrývají.
Nerovnoměrné osvětlení srovná sám, šum a reliéf uklidí čištění nebo `--vyhlazeni`,
dotýkající se kulaté objekty rozdělí `--rozdelit`.

Nefunguje, když se objekt od pozadí liší jen barvou a ne jasem (skript pracuje
ve stupních šedi), když je pozadí členité nebo stejně světlé jako objekty, když se
objekty hodně překrývají, nebo když jsou to tenké a protáhlé tvary (rozdělení
předpokládá zhruba kulaté objekty). Na milimetry převádí jen při kalibraci
a správně jen u fotky focené kolmo. U jiné fotky je skoro vždy potřeba vyzkoušet
přepínače a podívat se na masku v okně.

## Oficiální průměry euromincí (ECB)

| Mince | 1 c | 2 c | 5 c | 10 c | 20 c | 50 c | 1 € | 2 € |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Průměr [mm] | 16,25 | 18,75 | 21,25 | 19,75 | 22,25 | 24,25 | 23,25 | 25,75 |

Zdroj: https://www.ecb.europa.eu/euro/coins/common/html/index.en.html

## Příprava vlastního zvuku a videa (ffmpeg)

```
ffmpeg -i nahravka.m4a -ac 1 data/vlastni_nahravka.wav
ffmpeg -i video.mp4 -vf "fps=3,scale=384:-1" data/snimky/s_%03d.jpg
```

Pak `python 03_zvuk_klepani.py data/vlastni_nahravka.wav` a `python 04_video_pohyb.py data/snimky`.

Video musí být natočené statickou kamerou, jinak odečtení pozadí nefunguje.

## Zdroje dat

- `recke_mince.png`: testovací snímek `coins` z knihovny scikit-image
  (řecké mince z Pompejí, sbírka Brooklyn Museum, bez známých
  autorských omezení).
- `euro_mince.jpg`: repozitář janstaffa/euros na GitHubu, licence Apache-2.0,
  https://github.com/janstaffa/euros
- `slepene_mince.jpg`: obrázek `water_coins.jpg` z návodu OpenCV
  „Image Segmentation with Watershed Algorithm“, repozitář opencv/opencv,
  licence Apache-2.0,
  https://github.com/opencv/opencv/blob/4.x/doc/py_tutorials/py_imgproc/py_watershed/images/water_coins.jpg
- `klepani.wav`: soubor `4-261068-A-30.wav` z datasetu ESC-50
  (K. J. Piczak, nahrávky z Freesound), licence CC BY-NC,
  https://github.com/karolpiczak/ESC-50
- `chodci/`: ukázkové video `vtest.avi` z repozitáře opencv/opencv,
  rozložené na snímky příkazem
  `ffmpeg -i vtest.avi -vf "fps=3,scale=384:-1" -q:v 3 chodci/s_%03d.jpg`,
  https://github.com/opencv/opencv/blob/4.x/samples/data/vtest.avi
