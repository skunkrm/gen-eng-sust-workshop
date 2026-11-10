"""Indicatori dell'analisi ambientale (ISO 14001) calcolati dal codice: legge l'Excel dei dati ambientali,
controlla i dati, calcola i KPI, li confronta con l'anno precedente e crea il report Excel con le formule.

Il modello non ricopia i valori e non fa conti: chiama questi strumenti, poi ragiona sui risultati
(congruenza con la vecchia analisi, significatività degli aspetti, obiettivi).
Il formato atteso è quello del file di esempio: fogli Produzione, Energia, Acqua, Rifiuti ed Emissioni_atmosfera,
con l'intestazione nella terza riga.
"""

from io import BytesIO
from statistics import mean, median

import openpyxl
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

VERDE = "1F4E5A"
FOGLI = ("Produzione", "Energia", "Acqua", "Rifiuti", "Emissioni_atmosfera")
SOGLIA_ANOMALIA = 50  # un valore oltre 50 volte la mediana del sito è trattato come errore di unità


def _n(x, dec=1):
    """Numero in formato italiano: 1.234,5."""
    testo = f"{x:,.{dec}f}"
    return testo.replace(",", "X").replace(".", ",").replace("X", ".")


# ---------------- lettura ----------------

def _righe(foglio):
    """Righe del foglio come dizionari, con le intestazioni della prima riga che ha almeno tre colonne piene."""
    righe = list(foglio.iter_rows(values_only=True))
    i_head = next(i for i, r in enumerate(righe) if sum(v is not None for v in r) >= 3)
    head = [str(h).strip() if h is not None else "" for h in righe[i_head]]
    return [dict(zip(head, r)) for r in righe[i_head + 1:] if any(v is not None for v in r)]


def _colonna(riga, *parole):
    """Valore della prima colonna il cui nome contiene tutte le parole indicate."""
    for k, v in riga.items():
        if all(p.lower() in k.lower() for p in parole):
            return v
    return None


def trova_file(files):
    """Tra i file Excel caricati, restituisce (nome, workbook) di quello con i fogli dei dati ambientali."""
    for nome, dati in files:
        try:
            wb = openpyxl.load_workbook(BytesIO(dati), data_only=True)
        except Exception:
            continue
        if all(f in wb.sheetnames for f in FOGLI):
            return nome, wb
    raise ValueError("Nessun file Excel con i fogli " + ", ".join(FOGLI) + " tra i documenti caricati.")


def _serie_mensili(righe, colonna, unita, stima_mancanti, controlli):
    """Controlla le serie mensili di ogni sito: corregge le unità anomale e gestisce i mesi mancanti.

    Restituisce le righe (sito, mese, valore o None, nota).
    """
    per_sito = {}
    for r in righe:
        per_sito.setdefault(_colonna(r, "codice sito"), []).append(r)
    out = []
    for sito, mesi in per_sito.items():
        valori = [_colonna(m, *colonna) for m in mesi]
        noti = [v for v in valori if isinstance(v, (int, float)) and v > 0]
        mediana = median(noti) if noti else 0
        validi = [v for v in noti if v < mediana * SOGLIA_ANOMALIA]
        for m, v in zip(mesi, valori):
            mese, nota = _colonna(m, "mese"), ""
            if v is None:
                if stima_mancanti and validi:
                    v = round(mean(validi))
                    nota = "stimato con la media degli altri mesi del sito"
                    controlli.append(f"{sito} {mese}, {unita}: dato mancante, stimato in {_n(v, 0)} {unita} (media degli altri mesi).")
                else:
                    nota = "mancante, escluso"
                    controlli.append(f"{sito} {mese}, {unita}: dato mancante, escluso dal calcolo (nessuna stima): "
                                     f"il totale del sito è sottostimato.")
            elif mediana and v > mediana * SOGLIA_ANOMALIA:
                corretto = v / 1000
                controlli.append(f"{sito} {mese}, {unita}: valore {_n(v, 0)}, circa {_n(v / mediana, 0)} volte la mediana del sito: "
                                 f"probabile inserimento in millesimi ({'Wh' if unita == 'kWh' else 'unità sbagliata'}). "
                                 f"Corretto in {_n(corretto, 0)} {unita}.")
                v, nota = corretto, "corretto: diviso per 1000 (unità errata)"
            out.append((sito, mese, v, nota))
    return out


def _fascia(variazione):
    if variazione is None:
        return "non confrontabile"
    if variazione < 5:
        return "stabile o in calo (meno di +5%)"
    if variazione <= 15:
        return "aumento tra +5% e +15%"
    return "aumento oltre +15%"


def _fascia_limite(quota):
    if quota < 50:
        return "sotto il 50% del limite"
    if quota <= 80:
        return "tra il 50% e l'80% del limite"
    return "oltre l'80% del limite"


# ---------------- calcolo ----------------

def calcola(files, stima_mancanti=False, kpi_anno_precedente=None):
    nome_file, wb = trova_file(files)
    controlli = []

    produzione = [(_colonna(r, "codice sito"), _colonna(r, "produzione") or 0) for r in _righe(wb["Produzione"])]
    prod = sum(t for _, t in produzione)
    en_righe = _righe(wb["Energia"])
    rete = _serie_mensili(en_righe, ("elettrica", "rete"), "kWh", stima_mancanti, controlli)
    fv = _serie_mensili(en_righe, ("fotovoltaico",), "kWh", stima_mancanti, controlli)
    gas = _serie_mensili(en_righe, ("gas",), "Smc", stima_mancanti, controlli)
    acqua = _serie_mensili(_righe(wb["Acqua"]), ("prelievo",), "m3", stima_mancanti, controlli)
    energia = [(r[0], r[1], r[2], f[2], g[2], "; ".join(x for x in (r[3], f[3], g[3]) if x))
               for r, f, g in zip(rete, fv, gas)]

    rifiuti = []
    for r in _righe(wb["Rifiuti"]):
        rifiuti.append((_colonna(r, "codice sito"), str(_colonna(r, "eer")), _colonna(r, "descrizione"),
                        str(_colonna(r, "pericoloso") or ""), _colonna(r, "quantit") or 0, str(_colonna(r, "operazione") or "")))
    camini = []
    for r in _righe(wb["Emissioni_atmosfera"]):
        misurato, limite = _colonna(r, "misurata"), _colonna(r, "limite")
        camini.append((_colonna(r, "camino"), _colonna(r, "codice sito"), _colonna(r, "origine"), _colonna(r, "inquinante"),
                       misurato, limite, _colonna(r, "data")))

    def somma(righe, i=2):
        return sum(x[i] for x in righe if isinstance(x[i], (int, float)))

    el_mwh = (somma(energia) + somma(energia, 3)) / 1000
    gas_smc = somma(energia, 4)
    acqua_m3 = somma(acqua)
    rif_kg = sum(r[4] for r in rifiuti)
    per_kg = sum(r[4] for r in rifiuti if r[3].lower().startswith("s"))
    rec_kg = sum(r[4] for r in rifiuti if r[5].upper().startswith("R"))

    kpi = {  # nome dell'indicatore -> (valore, unità, decimali)
        "Produzione": (prod, "t", 0),
        "Energia elettrica totale (rete + fotovoltaico)": (el_mwh, "MWh", 0),
        "Energia elettrica specifica": (el_mwh / prod, "MWh/t", 3),
        "Gas naturale": (gas_smc, "Smc", 0),
        "Gas naturale specifico": (gas_smc / prod, "Smc/t", 1),
        "Prelievo idrico": (acqua_m3, "m3", 0),
        "Prelievo idrico specifico": (acqua_m3 / prod, "m3/t", 2),
        "Rifiuti prodotti": (rif_kg / 1000, "t", 1),
        "Rifiuti specifici": (rif_kg / prod, "kg/t", 1),
        "Rifiuti pericolosi": (per_kg / 1000, "t", 1),
        "Quota di rifiuti pericolosi": (per_kg / rif_kg * 100, "%", 1),
        "Quota di rifiuti avviati a recupero": (rec_kg / rif_kg * 100, "%", 1),
    }
    for c in camini:
        kpi[f"Camino {c[0]} - {str(c[3]).split(' (')[0]}"] = (c[4], f"mg/Nm3 (limite {_n(c[5], 0)})", 1)

    prec = kpi_anno_precedente or {}
    tabella = []
    for nome, (valore, unita, dec) in kpi.items():
        riga = {"indicatore": nome, "unita": unita, "valore": round(valore, dec)}
        if nome.startswith("Camino "):
            limite = next(c[5] for c in camini if nome == f"Camino {c[0]} - {str(c[3]).split(' (')[0]}")
            riga["quota_del_limite_%"] = round(valore / limite * 100, 1)
            riga["fascia_limite"] = _fascia_limite(valore / limite * 100)
        if nome in prec and isinstance(prec[nome], (int, float)):
            riga["anno_precedente"] = prec[nome]
            if unita == "%":
                riga["variazione_punti"] = round(valore - prec[nome], 1)
            elif prec[nome]:
                var = (valore / prec[nome] - 1) * 100
                riga["variazione_%"] = round(var, 1)
                if not nome.startswith("Camino "):
                    riga["fascia"] = _fascia(var)
        tabella.append(riga)
    sconosciuti = [k for k in prec if k not in kpi]

    return {
        "file": nome_file,
        "controlli_qualita": controlli,
        "indicatori": tabella,
        "indicatori_anno_precedente_non_riconosciuti": sconosciuti,
        "produzione_per_sito_t": dict(produzione),
        "camini": [{"camino": c[0], "sito": c[1], "origine": c[2], "inquinante": c[3], "misurato_mg_Nm3": c[4],
                    "limite_mg_Nm3": c[5], "quota_del_limite_%": round(c[4] / c[5] * 100, 1),
                    "fascia": _fascia_limite(c[4] / c[5] * 100), "data": c[6]} for c in camini],
        "rifiuti_per_codice": [{"sito": r[0], "eer": r[1], "descrizione": r[2], "pericoloso": r[3],
                                "kg": r[4], "operazione": r[5]} for r in rifiuti],
        "nota": "Le variazioni dei consumi si leggono sugli indicatori specifici (per tonnellata prodotta).",
        "_dettaglio": {"produzione": produzione, "energia": energia, "acqua": acqua, "rifiuti": rifiuti, "camini": camini,
                       "kpi": kpi, "prec": prec},
    }


def pubblico(ris):
    """Il risultato da mandare al modello, senza il dettaglio riga per riga."""
    return {k: v for k, v in ris.items() if not k.startswith("_")}


# ---------------- report Excel ----------------

def _intestazione(ws, riga, valori):
    for c, v in enumerate(valori, 1):
        cella = ws.cell(row=riga, column=c, value=v)
        cella.font = Font(bold=True, color="FFFFFF")
        cella.fill = PatternFill("solid", fgColor=VERDE)


def _larghezze(ws, larg):
    for i, w in enumerate(larg, 1):
        ws.column_dimensions[get_column_letter(i)].width = w


def report_excel(ris, kpi_anno_precedente=None):
    d = ris["_dettaglio"]
    prec = kpi_anno_precedente or d["prec"]
    wb = openpyxl.Workbook()

    def foglio(nome, intest, righe, larg):
        ws = wb.create_sheet(nome)
        _intestazione(ws, 1, intest)
        for i, r in enumerate(righe, 2):
            for c, v in enumerate(r, 1):
                ws.cell(row=i, column=c, value=v)
        _larghezze(ws, larg)
        return len(righe) + 1

    n_pr = foglio("Produzione", ["Sito", "Produzione (t)"], d["produzione"], [10, 16])
    n_en = foglio("Energia", ["Sito", "Mese", "Elettricità da rete (kWh)", "Fotovoltaico (kWh)", "Gas naturale (Smc)", "Nota"],
                  d["energia"], [8, 8, 22, 18, 18, 46])
    n_ac = foglio("Acqua", ["Sito", "Mese", "Prelievo (m3)", "Nota"], d["acqua"], [8, 8, 14, 46])
    n_ri = foglio("Rifiuti", ["Sito", "EER", "Descrizione", "Pericoloso", "Quantità (kg)", "Operazione"],
                  d["rifiuti"], [8, 11, 56, 11, 14, 11])
    em = wb.create_sheet("Emissioni")
    _intestazione(em, 1, ["Camino", "Sito", "Origine", "Inquinante", "Misurato (mg/Nm3)", "Limite (mg/Nm3)", "Quota del limite", "Data"])
    for i, c in enumerate(d["camini"], 2):
        for j, v in enumerate(c[:6], 1):
            em.cell(row=i, column=j, value=v)
        em.cell(row=i, column=7, value=f"=E{i}/F{i}").number_format = "0.0%"
        em.cell(row=i, column=8, value=c[6])
    _larghezze(em, [8, 8, 44, 30, 16, 14, 14, 13])

    # Riepilogo: ogni KPI dell'anno è una formula sui fogli di dettaglio
    ws = wb.active
    ws.title = "Riepilogo KPI"
    ws["A1"] = "Indicatori ambientali - calcolati dal codice a partire da " + ris["file"]
    ws["A1"].font = Font(bold=True, size=13, color=VERDE)
    _intestazione(ws, 3, ["Indicatore", "Unità", "Anno in corso", "Anno precedente", "Variazione"])
    E, A, R = f"Energia!{{}}2:{{}}{n_en}", f"Acqua!C2:C{n_ac}", f"Rifiuti!{{}}2:{{}}{n_ri}"
    formule = {
        "Produzione": f"=SUM(Produzione!B2:B{n_pr})",
        "Energia elettrica totale (rete + fotovoltaico)": f"=(SUM({E.format('C', 'C')})+SUM({E.format('D', 'D')}))/1000",
        "Gas naturale": f"=SUM({E.format('E', 'E')})",
        "Prelievo idrico": f"=SUM({A})",
        "Rifiuti prodotti": f"=SUM({R.format('E', 'E')})/1000",
        "Rifiuti pericolosi": f'=SUMIF({R.format("D", "D")},"S*",{R.format("E", "E")})/1000',
        "Quota di rifiuti avviati a recupero": f'=SUMIF({R.format("F", "F")},"R*",{R.format("E", "E")})/SUM({R.format("E", "E")})*100',
    }
    riga_di = {}
    for i, (nome, (valore, unita, dec)) in enumerate(d["kpi"].items(), 4):
        riga_di[nome] = i
    rp = riga_di["Produzione"]
    formule.update({
        "Energia elettrica specifica": f"=C{riga_di['Energia elettrica totale (rete + fotovoltaico)']}/C{rp}",
        "Gas naturale specifico": f"=C{riga_di['Gas naturale']}/C{rp}",
        "Prelievo idrico specifico": f"=C{riga_di['Prelievo idrico']}/C{rp}",
        "Rifiuti specifici": f"=C{riga_di['Rifiuti prodotti']}*1000/C{rp}",
        "Quota di rifiuti pericolosi": f"=C{riga_di['Rifiuti pericolosi']}/C{riga_di['Rifiuti prodotti']}*100",
    })
    for k, c in enumerate(d["camini"], 2):
        formule[f"Camino {c[0]} - {str(c[3]).split(' (')[0]}"] = f"=Emissioni!E{k}"
    for nome, i in riga_di.items():
        valore, unita, dec = d["kpi"][nome]
        ws.cell(row=i, column=1, value=nome)
        ws.cell(row=i, column=2, value=unita)
        formato = "#,##0" if dec == 0 else "#,##0." + "0" * dec
        ws.cell(row=i, column=3, value=formule.get(nome, valore)).number_format = formato
        if nome in prec:
            ws.cell(row=i, column=4, value=prec[nome]).number_format = formato
            if unita == "%":
                ws.cell(row=i, column=5, value=f"=C{i}-D{i}").number_format = '+0.0" punti";-0.0" punti"'
            else:
                ws.cell(row=i, column=5, value=f'=IF(D{i}=0,"-",C{i}/D{i}-1)').number_format = "+0.0%;-0.0%"
    fine = 4 + len(riga_di) + 1
    ws.cell(row=fine, column=1, value="Controlli di qualità sui dati").font = Font(bold=True, color=VERDE)
    for k, testo in enumerate(ris["controlli_qualita"] or ["Nessuna anomalia rilevata."], fine + 1):
        ws.cell(row=k, column=1, value="• " + testo)
    nota = fine + len(ris["controlli_qualita"] or [1]) + 2
    ws.cell(row=nota, column=1, value=ris["nota"]).font = Font(italic=True)
    _larghezze(ws, [48, 22, 16, 16, 14])

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()
