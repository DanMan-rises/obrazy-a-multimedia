"""
03 – Zvuk: stejný princip v 1D
==============================
Zvuk je řada čísel (vzorků). Postup je stejný jako u obrazu:
hlasitost -> práh -> souvislé úseky nad prahem -> počet událostí a jejich délky.

Spuštění:
    python 03_zvuk_klepani.py                  klepání na dveře (data/klepani.wav),
                                               zvuk se při otevření grafů přehraje
    python 03_zvuk_klepani.py --bez-zvuku      totéž bez přehrání

Volitelně vlastní nahrávka: z telefonu (m4a, mp3) ji převeď na WAV
a případně uprav práh:
    ffmpeg -i nahravka.m4a -ac 1 data/vlastni_nahravka.wav
    python 03_zvuk_klepani.py data/vlastni_nahravka.wav --prah 0.3
"""
import argparse
import os
import shutil
import subprocess
import sys

import matplotlib.pyplot as plt
import numpy as np
from scipy import ndimage as ndi
from scipy import signal
from scipy.io import wavfile

os.makedirs("vystupy", exist_ok=True)   # složka pro výsledky

p = argparse.ArgumentParser()
p.add_argument("nahravka", nargs="?", default="data/klepani.wav")
p.add_argument("--prah", type=float, default=0.25,
               help="práh jako podíl největší hlasitosti (0 až 1)")
p.add_argument("--okno-ms", type=float, default=20,
               help="délka okna pro výpočet hlasitosti v milisekundách")
p.add_argument("--bez-zvuku", action="store_true",
               help="nepřehrávat zvuk při otevření grafů")
p.add_argument("--bez-okna", action="store_true",
               help="jen uložit obrázek, neotvírat okno (a nepřehrávat)")
a = p.parse_args()

# ---------------------------------------------------------------- 1) načtení
fs, zvuk = wavfile.read(a.nahravka)       # fs = vzorků za sekundu
zvuk = zvuk.astype(float)
if zvuk.ndim > 1:                          # stereo -> mono
    zvuk = zvuk.mean(axis=1)
zvuk /= np.abs(zvuk).max()                 # normalizace na -1..1
print(f"Soubor {a.nahravka}")
print(f"Vzorkovací frekvence: {fs} Hz, délka: {zvuk.size / fs:.2f} s,"
      f" vzorků: {zvuk.size}")

# ---------------------------------------------------------------- 2) hlasitost
# signál kmitá kolem nuly, proto ho rozdělíme na krátká okna
# a v každém spočítáme RMS (odmocninu z průměru druhých mocnin)
okno = int(a.okno_ms / 1000 * fs)
pocet_oken = zvuk.size // okno
ramce = zvuk[:pocet_oken * okno].reshape(pocet_oken, okno)
rms = np.sqrt((ramce ** 2).mean(axis=1))
cas_rms = (np.arange(pocet_oken) + 0.5) * okno / fs

# ---------------------------------------------------------------- 3) prahování
prah = a.prah * rms.max()
maska = rms > prah

# ---------------------------------------------------------------- 4) čištění masky
# krátké propady pod práh uvnitř jedné události spojíme (obdoba zaplnění děr)
maska = ndi.binary_closing(maska, iterations=2)

# ---------------------------------------------------------------- 5) označení úseků
stitky, pocet = ndi.label(maska)           # stejná funkce jako u obrazu
useky = ndi.find_objects(stitky)

print(f"\nPráh: {prah:.3f} ({a.prah:.0%} největší hlasitosti)"
      f"  ->  počet událostí: {pocet}")
print(f"{'#':>3} {'začátek [s]':>12} {'délka [ms]':>11}")
for i, (u,) in enumerate(useky, start=1):
    zac = u.start * okno / fs
    delka = (u.stop - u.start) * okno / fs * 1000
    print(f"{i:>3} {zac:>12.2f} {delka:>11.0f}")

# ---------------------------------------------------------------- 6) obrázky
fig, osy = plt.subplots(3, 1, figsize=(11, 8), sharex=True)
cas = np.arange(zvuk.size) / fs

osy[0].plot(cas, zvuk, color="#444444", linewidth=0.5)
osy[0].set_title("1. Signál: výchylka membrány mikrofonu v čase")
osy[0].set_ylabel("amplituda")

osy[1].plot(cas_rms, rms, color="#2a6f97")
osy[1].axhline(prah, color="red", label="práh")
osy[1].fill_between(cas_rms, 0, rms.max(), where=maska, color="#f4a261",
                    alpha=0.35, label="nad prahem")
osy[1].set_title(f"2. Hlasitost (RMS) a práh: počet událostí {pocet}")
osy[1].set_ylabel("RMS")
osy[1].legend(loc="upper right")

# spektrogram = obrázek (frekvence x čas), dá se zpracovat jako fotka
f, ts, S = signal.spectrogram(zvuk, fs, nperseg=1024, noverlap=768)
osy[2].pcolormesh(ts, f / 1000, 10 * np.log10(S + 1e-12), shading="auto",
                  cmap="magma")
osy[2].set_ylim(0, 10)
osy[2].set_title("3. Spektrogram: tentýž zvuk jako obraz")
osy[2].set_ylabel("frekvence [kHz]")
osy[2].set_xlabel("čas [s]")

plt.tight_layout()
plt.savefig("vystupy/03_zvuk.png", dpi=150)
print("\nUloženo: vystupy/03_zvuk.png")


def prehrat(cesta):
    """Spustí přehrávání WAV souboru na pozadí, aby se mezitím ukázaly grafy."""
    if sys.platform.startswith("win"):
        import winsound
        winsound.PlaySound(cesta, winsound.SND_FILENAME | winsound.SND_ASYNC)
        return True
    for prikaz in (["afplay"], ["aplay", "-q"], ["paplay"]):   # macOS, Linux
        if shutil.which(prikaz[0]):
            subprocess.Popen(prikaz + [cesta])
            return True
    return False


if not a.bez_okna:
    if not a.bez_zvuku:
        if prehrat(a.nahravka):
            print(f"Přehrávám {a.nahravka}")
        else:
            print("Přehrávač nenalezen: otevři soubor ručně dvojklikem.")
    plt.show()
