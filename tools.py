"""Gli strumenti dell'agente: cosa può fare oltre a scrivere testo.

Ogni strumento ha due parti:
- la descrizione per il modello (TOOLS), che gli dice quando e come usarlo;
- la funzione Python che lo esegue davvero (execute_tool).
"""

import json

from generator import make_chart, make_document

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
}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calcola_emissioni",
            "description": (
                "Calcola le emissioni di gas serra moltiplicando ogni quantità per il suo fattore di emissione. "
                "Usalo SEMPRE per calcolare le emissioni, anche per una sola voce. "
                "Passa le voci singole come sono nei dati (una per sito e mese, per veicolo, per viaggio), "
                "senza sommarle: le somme le fa lo strumento. "
                "Per i viaggi passa la distanza di sola andata e indica andata_ritorno e persone: "
                "per i treni e gli aerei le emissioni sono per persona, per 'Auto propria' per veicolo."
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
                                "fattore": {"type": "string", "enum": list(FATTORI)},
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
                "In Excel ogni tabella diventa una tabella del foglio."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "formato": {"type": "string", "enum": ["pdf", "docx", "xlsx"]},
                    "nome_file": {"type": "string", "description": "Nome senza estensione, es. 'report_emissioni_2025'"},
                    "titolo": {"type": "string"},
                    "contenuto": {"type": "string"},
                    "includi_grafico": {"type": "boolean", "description": "Inserisce l'ultimo grafico creato (pdf e docx)"},
                },
                "required": ["formato", "nome_file", "titolo", "contenuto"],
            },
        },
    },
]


def calcola_emissioni(voci):
    righe, totali = [], {}
    for v in voci:
        if v["fattore"] not in FATTORI:
            raise ValueError(f"fattore '{v['fattore']}' sconosciuto. Fattori disponibili: {', '.join(FATTORI)}")
        valore, unita, fonte = FATTORI[v["fattore"]]
        quantita = float(v["quantita"])
        if v.get("andata_ritorno"):
            quantita *= 2
        if v["fattore"] != "Auto propria":
            quantita *= int(v.get("persone") or 1)
        t_co2e = quantita * valore / 1000
        totali[v["scope"]] = totali.get(v["scope"], 0) + t_co2e
        righe.append({
            "descrizione": v["descrizione"], "scope": v["scope"], "quantita_calcolata": round(quantita, 2),
            "fattore": f"{valore} {unita}", "fonte": fonte, "t_CO2e": round(t_co2e, 3),
        })
    return {
        "voci": righe,
        "totali_per_scope_t_CO2e": {k: round(v, 1) for k, v in sorted(totali.items())},
        "totale_t_CO2e": round(sum(totali.values()), 1),
        "numero_voci": len(righe),
    }


def execute_tool(name, args, stato):
    """Esegue uno strumento. Restituisce (risultato per il modello, evento per l'interfaccia o None).

    stato è un dizionario che dura per tutta la sessione (qui teniamo l'ultimo grafico).
    """
    try:
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
            grafico = stato.get("ultimo_grafico") if args.get("includi_grafico") else None
            dati, nome, mime = make_document(args["formato"], args["nome_file"], args["titolo"],
                                             args["contenuto"], grafico)
            evento = ("file", {"data": dati, "filename": nome, "mime": mime})
            return f"File {nome} creato e disponibile per il download.", evento

        return f"Strumento sconosciuto: {name}", None
    except Exception as errore:  # l'errore torna al modello, che può correggersi
        return f"Errore nell'esecuzione di {name}: {errore}", None
