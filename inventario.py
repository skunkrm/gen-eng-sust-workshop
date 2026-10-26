"""Inventario GHG calcolato dal codice: legge l'Excel dei consumi, controlla i dati, calcola e crea il report.

Il modello non ricopia i valori e non fa somme: chiama questi strumenti e ne commenta i risultati.
Il formato atteso è quello del file di esempio (fogli Consumi_energia, Flotta, Refrigeranti,
Viaggi_lavoro, Fattori_emissione, con l'intestazione nella terza riga).
"""

from io import BytesIO
from statistics import median

import openpyxl
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

VERDE = "1F4E5A"
FOGLI = ("Consumi_energia", "Flotta", "Refrigeranti", "Viaggi_lavoro")
FATTORI_PREDEFINITI = {  # usati solo se il file non ha il foglio Fattori_emissione
    "elettricita_rete": 0.213, "gas_naturale": 2.02633, "gasolio": 2.58354, "benzina": 2.075,
    "R410A": 1924, "R32": 677, "Treno AV": 0.03092, "Aereo nazionale": 0.22928,
    "Aereo corto raggio": 0.12786, "Aereo lungo raggio": 0.15282, "Auto propria": 0.17265,
}
SOGLIA_ANOMALIA = 50


def _n(x):
    """Numero in formato italiano: 281.450 e 1.234,5."""
    testo = f"{x:,.0f}" if float(x).is_integer() or abs(x) >= 100 else f"{x:,.1f}"
    return testo.replace(",", "X").replace(".", ",").replace("X", ".")  # un valore oltre 50 volte la mediana del sito è trattato come errore di unità


# ---------------- lettura ----------------

def _righe(foglio):
    """Righe del foglio come dizionari, con le intestazioni della prima riga che ha più colonne piene."""
    righe = [r for r in foglio.iter_rows(values_only=True)]
    i_head = next(i for i, r in enumerate(righe) if sum(v is not None for v in r) >= 3)
    head = [str(h).strip() if h is not None else "" for h in righe[i_head]]
    out = []
    for r in righe[i_head + 1:]:
        if any(v is not None for v in r):
            out.append(dict(zip(head, r)))
    return out


def _colonna(riga, *parole):
    """Valore della prima colonna il cui nome contiene tutte le parole indicate."""
    for k, v in riga.items():
        if all(p.lower() in k.lower() for p in parole):
            return v
    return None


def trova_file_consumi(files):
    """Tra i file Excel caricati, restituisce (nome, workbook) di quello con i fogli dei consumi."""
    for nome, dati in files:
        try:
            wb = openpyxl.load_workbook(BytesIO(dati), data_only=True)
        except Exception:
            continue
        if all(f in wb.sheetnames for f in FOGLI):
            return nome, wb
    raise ValueError("Nessun file Excel con i fogli Consumi_energia, Flotta, Refrigeranti e Viaggi_lavoro tra i documenti caricati.")


def _fattori(wb):
    if "Fattori_emissione" not in wb.sheetnames:
        return {k: (v, "valore predefinito dell'app") for k, v in FATTORI_PREDEFINITI.items()}
    out = {}
    for r in _righe(wb["Fattori_emissione"]):
        chiave, valore = _colonna(r, "chiave"), _colonna(r, "valore")
        if chiave and isinstance(valore, (int, float)):
            out[str(chiave)] = (float(valore), str(_colonna(r, "fonte") or ""))
    return out


# ---------------- calcolo ----------------

def calcola(files, stima_mancanti=False):
    nome_file, wb = trova_file_consumi(files)
    fattori = _fattori(wb)
    f = {k: v[0] for k, v in fattori.items()}
    controlli = []

    # Energia: serie mensili per sito, con controllo di qualità
    energia = _righe(wb["Consumi_energia"])
    serie = {}
    for r in energia:
        sito = _colonna(r, "codice sito")
        serie.setdefault(sito, []).append(r)

    righe_energia = []
    for sito, mesi in serie.items():
        for vettore, parole, unita in (("elettricita_rete", ("elettrica", "rete"), "kWh"),
                                       ("gas_naturale", ("gas",), "Smc")):
            valori = [_colonna(m, *parole) for m in mesi]
            noti = [v for v in valori if isinstance(v, (int, float)) and v > 0]
            mediana = median(noti) if noti else 0
            for m, v in zip(mesi, valori):
                mese = _colonna(m, "mese")
                nota = ""
                if v is None:
                    if stima_mancanti and noti:
                        stima = sum(x for x in noti if x < mediana * SOGLIA_ANOMALIA) / len(
                            [x for x in noti if x < mediana * SOGLIA_ANOMALIA])
                        v, nota = round(stima), "stimato con la media degli altri mesi del sito"
                        controlli.append(f"{sito} {mese}, {unita}: dato mancante, stimato in {_n(v)} {unita} (media degli altri mesi).")
                    else:
                        controlli.append(f"{sito} {mese}, {unita}: dato mancante, escluso dal calcolo (nessuna stima).")
                        righe_energia.append((sito, mese, vettore, None, None, "mancante, escluso"))
                        continue
                elif mediana and v > mediana * SOGLIA_ANOMALIA:
                    corretto = v / 1000
                    sbagliata = "Wh" if unita == "kWh" else f"millesimi di {unita}"
                    controlli.append(f"{sito} {mese}, {unita}: valore {_n(v)}, circa {_n(round(v / mediana))} volte la mediana "
                                     f"del sito: probabile inserimento in {sbagliata} invece che in {unita}. "
                                     f"Corretto in {_n(corretto)} {unita}.")
                    v, nota = corretto, "corretto: diviso per 1000 (unità errata)"
                if mediana == 0 and (v or 0) == 0:
                    continue
                righe_energia.append((sito, mese, vettore, v, v * f[vettore] / 1000, nota))

    # Flotta
    righe_flotta = []
    for r in _righe(wb["Flotta"]):
        alim = str(_colonna(r, "alimentazione") or "").lower()
        chiave = "gasolio" if "gasolio" in alim or "diesel" in alim else "benzina"
        litri = _colonna(r, "litri") or 0
        righe_flotta.append((_colonna(r, "sito"), _colonna(r, "targa"), chiave, litri, litri * f[chiave] / 1000))

    # Refrigeranti
    righe_refr = []
    for r in _righe(wb["Refrigeranti"]):
        gas = str(_colonna(r, "gas"))
        kg = _colonna(r, "quantit") or 0
        if gas not in f:
            controlli.append(f"Refrigerante {gas}: GWP non presente nei fattori, escluso.")
            continue
        righe_refr.append((_colonna(r, "sito"), _colonna(r, "impianto"), gas, kg, kg * f[gas] / 1000))

    # Trasferte
    righe_viaggi = []
    for r in _righe(wb["Viaggi_lavoro"]):
        mezzo = str(_colonna(r, "mezzo"))
        km = _colonna(r, "distanza") or 0
        ar = str(_colonna(r, "ritorno") or "").lower().startswith("s")
        persone = _colonna(r, "viaggiatori") or 1
        distanza = km * (2 if ar else 1)
        attivita = distanza if mezzo == "Auto propria" else distanza * persone
        if mezzo not in f:
            controlli.append(f"Trasferta {_colonna(r, 'tratta')}: mezzo {mezzo} senza fattore, esclusa.")
            continue
        righe_viaggi.append((_colonna(r, "data"), _colonna(r, "tratta"), mezzo, attivita, attivita * f[mezzo] / 1000))

    # Totali
    cat = {
        "Gas naturale": ("Scope 1", sum(r[4] for r in righe_energia if r[2] == "gas_naturale" and r[4])),
        "Flotta aziendale": ("Scope 1", sum(r[4] for r in righe_flotta)),
        "Refrigeranti (F-gas)": ("Scope 1", sum(r[4] for r in righe_refr)),
        "Elettricità da rete (location-based)": ("Scope 2", sum(r[4] for r in righe_energia if r[2] == "elettricita_rete" and r[4])),
        "Trasferte di lavoro (cat. 6)": ("Scope 3", sum(r[4] for r in righe_viaggi)),
    }
    scope = {}
    for s, v in cat.values():
        scope[s] = scope.get(s, 0) + v
    siti = {}
    for r in righe_energia:
        if r[4]:
            d = siti.setdefault(r[0], {"Scope 1": 0, "Scope 2": 0})
            d["Scope 1" if r[2] == "gas_naturale" else "Scope 2"] += r[4]
    for r in righe_flotta + righe_refr:
        siti.setdefault(r[0], {"Scope 1": 0, "Scope 2": 0})["Scope 1"] += r[4]
    totale = sum(scope.values())

    return {
        "file": nome_file,
        "controlli_qualita": controlli,
        "totali_per_categoria_t_CO2e": {k: {"scope": s, "t_CO2e": round(v, 1), "quota": round(v / totale, 3)} for k, (s, v) in cat.items()},
        "totali_per_scope_t_CO2e": {k: round(v, 1) for k, v in sorted(scope.items())},
        "totali_per_sito_t_CO2e": {k: {s: round(x, 1) for s, x in d.items()} | {"Totale": round(sum(d.values()), 1)}
                                   for k, d in siti.items()},
        "totale_t_CO2e": round(totale, 1),
        "totale_kg_CO2e": round(totale * 1000, 1),
        "numero_voci": len(righe_energia) + len(righe_flotta) + len(righe_refr) + len(righe_viaggi),
        "fattori_usati": {k: f"{v} ({fonte})" for k, (v, fonte) in fattori.items()},
        "nota": "Scope 3 limitato alla categoria 6 (trasferte): è l'unica presente nei dati.",
        "_dettaglio": {"energia": righe_energia, "flotta": righe_flotta, "refrigeranti": righe_refr, "viaggi": righe_viaggi},
    }


# ---------------- report Excel ----------------

def _intestazione(ws, riga, valori):
    for c, v in enumerate(valori, 1):
        cella = ws.cell(row=riga, column=c, value=v)
        cella.font = Font(bold=True, color="FFFFFF")
        cella.fill = PatternFill("solid", fgColor=VERDE)


def _larghezze(ws, larg):
    for i, w in enumerate(larg, 1):
        ws.column_dimensions[get_column_letter(i)].width = w


def report_excel(inv, valori_dichiarati=None):
    d = inv["_dettaglio"]
    wb = openpyxl.Workbook()

    # Dettagli prima, così il riepilogo può sommarli con formule
    def foglio(nome, intest, righe, col_t, larg):
        ws = wb.create_sheet(nome)
        _intestazione(ws, 1, intest)
        for i, r in enumerate(righe, 2):
            for c, v in enumerate(r, 1):
                ws.cell(row=i, column=c, value=v)
            ws.cell(row=i, column=col_t).number_format = "#,##0.000"
        _larghezze(ws, larg)
        return ws, len(righe) + 1

    en, n_en = foglio("Energia", ["Sito", "Mese", "Vettore", "Quantità (kWh o Smc)", "t CO2e", "Nota"],
                      d["energia"], 5, [8, 8, 18, 20, 12, 44])
    fl, n_fl = foglio("Flotta", ["Sito", "Targa", "Carburante", "Litri", "t CO2e"], d["flotta"], 5, [8, 12, 12, 10, 12])
    rf, n_rf = foglio("Refrigeranti", ["Sito", "Impianto", "Gas", "kg ricaricati", "t CO2e"], d["refrigeranti"], 5, [8, 36, 8, 14, 12])
    vg, n_vg = foglio("Trasferte", ["Data", "Tratta", "Mezzo", "pkm o km veicolo", "t CO2e"], d["viaggi"], 5, [12, 28, 20, 18, 12])

    ws = wb.active
    ws.title = "Riepilogo"
    wb.move_sheet("Riepilogo", offset=-4)
    ws["A1"] = "Inventario GHG - calcolato dal codice a partire da " + inv["file"]
    ws["A1"].font = Font(bold=True, size=13, color=VERDE)
    _intestazione(ws, 3, ["Categoria", "Scope", "t CO2e"])
    formule = [
        ("Gas naturale", "Scope 1", f'=SUMIF(Energia!C2:C{n_en},"gas_naturale",Energia!E2:E{n_en})'),
        ("Flotta aziendale", "Scope 1", f"=SUM(Flotta!E2:E{n_fl})"),
        ("Refrigeranti (F-gas)", "Scope 1", f"=SUM(Refrigeranti!E2:E{n_rf})"),
        ("Elettricità da rete (location-based)", "Scope 2", f'=SUMIF(Energia!C2:C{n_en},"elettricita_rete",Energia!E2:E{n_en})'),
        ("Trasferte di lavoro (cat. 6)", "Scope 3", f"=SUM(Trasferte!E2:E{n_vg})"),
    ]
    for i, (c, s, fx) in enumerate(formule, 4):
        ws.cell(row=i, column=1, value=c)
        ws.cell(row=i, column=2, value=s)
        ws.cell(row=i, column=3, value=fx).number_format = "#,##0.0"
    r = 4 + len(formule) + 1
    _intestazione(ws, r, ["Scope", "", "t CO2e"])
    for j, s in enumerate(("Scope 1", "Scope 2", "Scope 3"), r + 1):
        ws.cell(row=j, column=1, value=s)
        ws.cell(row=j, column=3, value=f'=SUMIF(B4:B{3 + len(formule)},"{s}",C4:C{3 + len(formule)})').number_format = "#,##0.0"
    tot = r + 4
    ws.cell(row=tot, column=1, value="Totale").font = Font(bold=True)
    ws.cell(row=tot, column=3, value=f"=SUM(C{r + 1}:C{r + 3})").number_format = "#,##0.0"
    ws.cell(row=tot, column=3).font = Font(bold=True)

    if valori_dichiarati:
        c0 = tot + 2
        _intestazione(ws, c0, ["Confronto con il bilancio", "Dichiarato (t CO2e)", "Ricalcolato (t CO2e)", "Differenza"])
        for k, (s, v) in enumerate(valori_dichiarati.items(), c0 + 1):
            ws.cell(row=k, column=1, value=s)
            ws.cell(row=k, column=2, value=v).number_format = "#,##0.0"
            riga_scope = {"Scope 1": r + 1, "Scope 2": r + 2, "Scope 3": r + 3}.get(s)
            if riga_scope:
                ws.cell(row=k, column=3, value=f"=C{riga_scope}").number_format = "#,##0.0"
                ws.cell(row=k, column=4, value=f"=IF(B{k}=0,\"-\",C{k}/B{k}-1)").number_format = "0.0%"
        tot = c0 + len(valori_dichiarati) + 1

    c1 = tot + 2
    ws.cell(row=c1, column=1, value="Controlli di qualità sui dati").font = Font(bold=True, color=VERDE)
    for k, testo in enumerate(inv["controlli_qualita"] or ["Nessuna anomalia rilevata."], c1 + 1):
        ws.cell(row=k, column=1, value="• " + testo)
    c2 = c1 + len(inv["controlli_qualita"] or [1]) + 2
    ws.cell(row=c2, column=1, value="Fattori di emissione usati").font = Font(bold=True, color=VERDE)
    for k, (chiave, testo) in enumerate(inv["fattori_usati"].items(), c2 + 1):
        ws.cell(row=k, column=1, value=chiave)
        ws.cell(row=k, column=2, value=testo)
    ws.cell(row=c2 + len(inv["fattori_usati"]) + 2, column=1, value=inv["nota"]).font = Font(italic=True)
    _larghezze(ws, [40, 22, 20, 14])

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


def pubblico(inv):
    """Il risultato da mandare al modello, senza il dettaglio riga per riga."""
    return {k: v for k, v in inv.items() if not k.startswith("_")}
