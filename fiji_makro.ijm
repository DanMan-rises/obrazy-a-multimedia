// Fiji / ImageJ makro: kalibrace -> prahování -> rozdělení -> počet a plochy
// Fotka: data/euro_mince.jpg (8 euromincí, tmavé mince na světlém pozadí).
// Otevři fotku a spusť přes Plugins > Macros > Run... (nebo v editoru Run).
//
// POZOR: makro je referenční a ve Fiji ho nikdo nespustil.
// Nejjistější je nahrát si vlastní přes Plugins > Macros > Record...
// při ručním průchodu demem. Hodnotu distance (průměr 50 c v pixelech)
// změř na své kopii fotky: úsečka přes minci 50 c a Analyze > Measure.

// 1) Kalibrace: mince 50 c (uprostřed dolní řady) má průměr 24,25 mm (ECB).
//    Je uprostřed fotky, takže zkreslení šikmým focením je u ní nejmenší.
run("Set Scale...", "distance=704 known=24.25 unit=mm");

// 2) Stupně šedi
run("8-bit");

// 3) Prahování: mince jsou TMAVŠÍ než pozadí, proto bez "dark"
setOption("BlackBackground", true);
setAutoThreshold("Otsu");
run("Convert to Mask");

// 4) Čištění a rozdělení mincí, které spojil stín
run("Fill Holes");
run("Watershed");

// 5) Co měřit a samotné měření (velikost v mm² po kalibraci)
run("Set Measurements...", "area centroid redirect=None decimal=2");
run("Analyze Particles...", "size=50-Infinity show=Outlines display exclude summarize");
