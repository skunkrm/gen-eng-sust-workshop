"""Gli strumenti dell'agente: cosa può fare oltre a scrivere testo.

Ogni strumento ha due parti:
- la descrizione per il modello (TOOLS), che gli dice quando e come usarlo;
- la funzione Python che lo esegue davvero (execute_tool).
"""

import json
import re

import inventario
from generator import make_chart, make_document, make_dpp_pdf

# Fattori di emissione: stessi valori del foglio "Fattori_emissione" del file di test.
# Valori indicativi a scopo formativo: per un uso reale verificare l'ultima edizione delle fonti.
FATTORI = {
    "elettricita_rete": (0.213, "kg CO2/kWh", "ISPRA, Settore elettrico ed. 2026 (valore 2025), location-based"),
    "gas_naturale": (2.02633, "kg CO2e/Smc", "DESNZ/DEFRA GHG Conversion Factors 2026"),
    "gasolio": (2.58354, "kg CO2e/l", "DESNZ/DEFRA GHG Conversion Factors 2026"),
    "benzina": (2.075, "kg CO2e/l", "DESNZ/DEFRA GHG Conversion Factors 2026"),
    "R410A": (1924, "kg CO2e/kg", "IPCC AR5, GWP 100 anni"),
    "R32": (677, "kg CO2e/kg", "IPCC AR5, GWP 100 anni"),
    "Treno AV": (0.03092, "kg CO2e/pkm", "DESNZ/DEFRA 2026, National rail (proxy)"),
    "Aereo nazionale": (0.22928, "kg CO2e/pkm", "DESNZ/DEFRA 2026, con RF"),
    "Aereo corto raggio": (0.12786, "kg CO2e/pkm", "DESNZ/DEFRA 2026, con RF"),
    "Aereo lungo raggio": (0.15282, "kg CO2e/pkm", "DESNZ/DEFRA 2026, con RF"),
    "Auto propria": (0.17265, "kg CO2e/km", "DESNZ/DEFRA 2026, auto media diesel (per veicolo)"),
    # Dato secondario per l'acciaio, da usare SOLO quando manca il dato del fornitore
    "acciaio_media_mondiale": (1.92, "kg CO2/kg", "worldsteel, Sustainability Indicators 2025 (media mondiale 2024, dato secondario)"),
}

# Chiave speciale: fattore dichiarato dal fornitore (EPD, certificato), con valore e fonte passati dal modello
DICHIARATO = "dichiarato_fornitore"

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calcola_inventario",
            "description": (
                "Calcola l'inventario GHG leggendo direttamente il file Excel dei consumi caricato dall'utente "
                "(fogli Consumi_energia, Flotta, Refrigeranti, Viaggi_lavoro). Il codice controlla la qualità dei dati, "
                "corregge le unità anomale dichiarandolo, applica i fattori del foglio Fattori_emissione e restituisce "
                "i totali per categoria, scope e sito. Usalo SEMPRE per i dati di consumo: non ricopiare i valori."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "stima_mancanti": {
                        "type": "boolean",
                        "description": "true per stimare i mesi mancanti con la media del sito; false (predefinito) per escluderli e segnalarli",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "crea_report_inventario",
            "description": (
                "Crea il report Excel dell'ultimo inventario calcolato con calcola_inventario: riepilogo con formule, "
                "dettaglio per riga, controlli di qualità e fattori. Usalo per l'Excel dell'inventario al posto di crea_documento. "
                "Se nei documenti c'è un bilancio, passa i valori dichiarati per avere il foglio di confronto."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "nome_file": {"type": "string", "description": "Nome senza estensione"},
                    "valori_dichiarati": {
                        "type": "object",
                        "description": "Valori dichiarati nel bilancio, es. {\"Scope 1\": 1106, \"Scope 2\": 2657}",
                        "additionalProperties": {"type": "number"},
                    },
                },
                "required": ["nome_file"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calcola_emissioni",
            "description": (
                "Calcola le emissioni di poche voci singole (per esempio i componenti di un prodotto). "
                "Per l'Excel dei consumi aziendali usa invece calcola_inventario. "
                "Passa le voci singole come sono nei dati (una per sito e mese, per veicolo, per viaggio), "
                "senza sommarle: le somme le fa lo strumento. "
                "Per i viaggi passa la distanza di sola andata e indica andata_ritorno e persone: "
                "per i treni e gli aerei le emissioni sono per persona, per 'Auto propria' per veicolo. "
                "Se un documento del fornitore dichiara un fattore (es. EPD), usa 'dichiarato_fornitore' con valore e fonte; "
                "usa 'acciaio_media_mondiale' solo se il dato del fornitore manca, e dillo all'utente."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "voci": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "descrizione": {"type": "string", "description": "Es. 'PC01 gen - energia elettrica'"},
                                "scope": {"type": "string", "enum": ["Scope 1", "Scope 2", "Scope 3"]},
                                "fattore": {"type": "string", "enum": [*FATTORI, DICHIARATO]},
                                "valore_fattore": {"type": "number", "description": "Solo con dichiarato_fornitore: kg CO2e per unità, come scritto nel documento"},
                                "unita_fattore": {"type": "string", "description": "Solo con dichiarato_fornitore: es. 'kg CO2e/kg'"},
                                "fonte_fattore": {"type": "string", "description": "Solo con dichiarato_fornitore: documento da cui è preso, es. 'EPD-AV-2024-031'"},
                                "quantita": {"type": "number", "description": "Quantità nell'unità del fattore (kWh, Smc, litri, kg, km)"},
                                "andata_ritorno": {"type": "boolean", "description": "Solo viaggi: true se andata e ritorno"},
                                "persone": {"type": "integer", "description": "Solo viaggi: numero di viaggiatori"},
                            },
                            "required": ["descrizione", "scope", "fattore", "quantita"],
                        },
                    }
                },
                "required": ["voci"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "crea_grafico",
            "description": "Crea un grafico a barre e lo mostra all'utente. Usalo per confronti tra valori.",
            "parameters": {
                "type": "object",
                "properties": {
                    "titolo": {"type": "string"},
                    "etichette": {"type": "array", "items": {"type": "string"}},
                    "valori": {"type": "array", "items": {"type": "number"}},
                    "unita": {"type": "string", "description": "Unità dei valori, es. 't CO2e'"},
                    "serie_confronto": {
                        "type": "array", "items": {"type": "number"},
                        "description": "Facoltativo: seconda serie da affiancare (es. valori dichiarati)",
                    },
                    "nomi_serie": {
                        "type": "array", "items": {"type": "string"},
                        "description": "Facoltativo: nomi delle due serie, es. ['Ricalcolato', 'Dichiarato']",
                    },
                },
                "required": ["titolo", "etichette", "valori", "unita"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "crea_documento",
            "description": (
                "Crea un file scaricabile. Usa esattamente il formato richiesto dall'utente. "
                "Contenuto in markdown semplice: '# ' e '## ' per i titoli, '- ' per gli elenchi, "
                "tabelle con righe separate da '|' (la prima riga è l'intestazione). "
                "In Excel ogni tabella diventa una tabella del foglio. "
                "Per il formato json il contenuto deve essere JSON valido (es. un Digital Product Passport)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "formato": {"type": "string", "enum": ["pdf", "docx", "xlsx", "json"]},
                    "nome_file": {"type": "string", "description": "Nome senza estensione, es. 'report_emissioni_2025'"},
                    "titolo": {"type": "string"},
                    "contenuto": {"type": "string"},
                    "includi_grafico": {"type": "boolean", "description": "Inserisce l'ultimo grafico creato (pdf e docx)"},
                    "includi_foto": {"type": "boolean",
                                     "description": "Inserisce le foto inviate dall'utente (pdf e docx): usalo nei verbali e report su una foto"},
                    "da_json_verificato": {
                        "type": "boolean",
                        "description": "Solo per il PDF del Digital Product Passport: true per generarlo dal JSON appena verificato, "
                                       "senza riscrivere il contenuto (lascia vuoto contenuto)",
                    },
                },
                "required": ["formato", "nome_file", "titolo"],
            },
        },
    },
]


def calcola_emissioni(voci):
    righe, totali = [], {}
    for v in voci:
        if v["fattore"] == DICHIARATO:
            if v.get("valore_fattore") is None or not v.get("fonte_fattore"):
                raise ValueError("con 'dichiarato_fornitore' servono valore_fattore e fonte_fattore")
            valore = float(v["valore_fattore"])
            unita = v.get("unita_fattore") or "kg CO2e/unità"
            fonte = f"Dichiarato dal fornitore: {v['fonte_fattore']}"
        elif v["fattore"] in FATTORI:
            valore, unita, fonte = FATTORI[v["fattore"]]
        else:
            raise ValueError(f"fattore '{v['fattore']}' sconosciuto. Fattori disponibili: {', '.join(FATTORI)}, {DICHIARATO}")
        quantita = float(v["quantita"])
        if v.get("andata_ritorno"):
            quantita *= 2
        if v["fattore"] in ("Treno AV", "Aereo nazionale", "Aereo corto raggio", "Aereo lungo raggio"):
            quantita *= int(v.get("persone") or 1)
        kg_co2e = quantita * valore
        t_co2e = kg_co2e / 1000
        totali[v["scope"]] = totali.get(v["scope"], 0) + t_co2e
        righe.append({
            "descrizione": v["descrizione"], "scope": v["scope"], "quantita_calcolata": round(quantita, 2),
            "fattore": f"{valore} {unita}", "fonte": fonte,
            "kg_CO2e": round(kg_co2e, 3), "t_CO2e": round(t_co2e, 3),
            "dato_secondario": v["fattore"] == "acciaio_media_mondiale",
        })
    return {
        "voci": righe,
        "totali_per_scope_t_CO2e": {k: round(v, 1) for k, v in sorted(totali.items())},
        "totali_per_scope_kg_CO2e": {k: round(v * 1000, 2) for k, v in sorted(totali.items())},
        "totale_t_CO2e": round(sum(totali.values()), 1),
        "totale_kg_CO2e": round(sum(totali.values()) * 1000, 2),
        "quota_da_dati_secondari": round(sum(r["kg_CO2e"] for r in righe if r["dato_secondario"])
                                         / max(sum(r["kg_CO2e"] for r in righe), 1e-9), 3),
        "numero_voci": len(righe),
    }


# ---------- verifica delle fonti: il codice controlla l'AI ----------

def _normalizza(testo):
    """Per confrontare citazioni e documenti ignoriamo il formato, non il contenuto:
    restano solo parole, numeri e il simbolo %, in minuscolo (punteggiatura, separatori | e virgolette ignorati)."""
    testo = str(testo).lower()
    testo = re.sub(r"(?<=\d)[.,](?=\d)", "", testo)    # 3,21 e 3.21 diventano 321
    testo = re.sub(r"[^\w%]+", " ", testo)              # restano solo parole, numeri e %
    return re.sub(r"\s+", " ", testo).strip()


def _campi_con_stato(nodo, percorso=""):
    """Trova nel JSON tutti i campi della forma {"valore", "stato", ...} con il loro percorso."""
    if isinstance(nodo, dict):
        if "stato" in nodo and "valore" in nodo:
            yield percorso or "radice", nodo
        for chiave, valore in nodo.items():
            yield from _campi_con_stato(valore, f"{percorso}.{chiave}" if percorso else chiave)
    elif isinstance(nodo, list):
        for i, valore in enumerate(nodo):
            yield from _campi_con_stato(valore, f"{percorso}[{i}]")


def verifica_fonti(oggetto, documenti):
    """Controlla che ogni campo "documentato" abbia una citazione presente davvero nei documenti
    e che i campi "mancante" non abbiano un valore. Restituisce un riepilogo."""
    testo_documenti = _normalizza(documenti)
    verificati, errori, mancanti = 0, [], 0
    for percorso, campo in _campi_con_stato(oggetto):
        stato = str(campo.get("stato", "")).lower().strip()
        if stato.startswith("documentato"):
            citazione = _normalizza(campo.get("citazione") or "")
            if len(citazione) < 3:
                errori.append(f"{percorso}: manca la citazione dal documento")
            elif citazione not in testo_documenti:
                errori.append(f"{percorso}: citazione non trovata nei documenti ('{campo.get('citazione')}')")
            else:
                verificati += 1
        elif stato.startswith("mancante"):
            mancanti += 1
            if campo.get("valore") not in (None, "", []):
                errori.append(f"{percorso}: è segnato come mancante ma ha un valore")
    return {"ok": not errori, "citazioni_verificate": verificati, "campi_mancanti": mancanti, "errori": errori}


def execute_tool(name, args, stato):
    """Esegue uno strumento. Restituisce (risultato per il modello, evento per l'interfaccia o None).

    stato è un dizionario che dura per tutta la sessione (qui teniamo l'ultimo grafico).
    """
    try:
        if name == "calcola_inventario":
            inv = inventario.calcola(stato.get("file_excel", []), bool(args.get("stima_mancanti", False)))
            stato["inventario"] = inv
            risultato = inventario.pubblico(inv)
            return json.dumps(risultato, ensure_ascii=False), ("calc", risultato)

        if name == "crea_report_inventario":
            if "inventario" not in stato:
                return "Prima calcola l'inventario con calcola_inventario.", None
            dati = inventario.report_excel(stato["inventario"], args.get("valori_dichiarati"))
            nome = re.sub(r"[^\w\-]+", "_", args.get("nome_file") or "inventario_ghg").strip("_") + ".xlsx"
            mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            return f"File {nome} creato e disponibile per il download.", ("file", {"data": dati, "filename": nome, "mime": mime})

        if name == "calcola_emissioni":
            risultato = calcola_emissioni(args["voci"])
            evento = ("calc", risultato)
            return json.dumps(risultato, ensure_ascii=False), evento

        if name == "crea_grafico":
            png = make_chart(args["titolo"], args["etichette"], args["valori"], args["unita"],
                             args.get("serie_confronto"), args.get("nomi_serie"))
            stato["ultimo_grafico"] = png
            return "Grafico creato e mostrato all'utente.", ("chart", {"png": png, "titolo": args["titolo"]})

        if name == "crea_documento":
            if args.get("da_json_verificato") and args["formato"] == "pdf":
                if "ultimo_dpp" not in stato:
                    return "Nessun JSON verificato: crea prima il passaporto in formato json.", None
                grafico = stato.get("ultimo_grafico") if args.get("includi_grafico") else None
                dati, nome, mime = make_dpp_pdf(stato["ultimo_dpp"], args["nome_file"], args["titolo"], grafico)
                return f"File {nome} creato dal JSON verificato.", ("file", {"data": dati, "filename": nome, "mime": mime})
            if args["formato"] == "json" and stato.get("documenti"):
                testo = args.get("contenuto", "").strip().removeprefix("```json").removeprefix("```").removesuffix("```")
                esito = verifica_fonti(json.loads(testo), stato["documenti"])
                if not esito["ok"]:
                    elenco = "\n".join(f"- {e}" for e in esito["errori"][:15])
                    return (f"File NON creato: la verifica delle fonti ha trovato {len(esito['errori'])} problemi.\n"
                            f"{elenco}\nCorreggi: copia le citazioni parola per parola dai documenti, "
                            "oppure segna il campo come mancante con valore null. Poi riprova."), ("check", esito)
                stato["ultima_verifica"] = esito
                stato["ultimo_dpp"] = json.loads(testo)
                stato["esito_verifica_testo"] = (
                    f" Verifica delle fonti superata: {esito['citazioni_verificate']} citazioni trovate nei documenti, "
                    f"{esito['campi_mancanti']} campi dichiarati mancanti.")
            grafico = stato.get("ultimo_grafico") if args.get("includi_grafico") else None
            foto = stato.get("foto") if args.get("includi_foto") else None
            dati, nome, mime = make_document(args["formato"], args["nome_file"], args["titolo"],
                                             args.get("contenuto", ""), grafico, foto)
            evento = ("file", {"data": dati, "filename": nome, "mime": mime,
                               "verifica": stato.pop("ultima_verifica", None)})
            return f"File {nome} creato e disponibile per il download." + stato.pop("esito_verifica_testo", ""), evento

        return f"Strumento sconosciuto: {name}", None
    except Exception as errore:  # l'errore torna al modello, che può correggersi
        return f"Errore nell'esecuzione di {name}: {errore}", None
