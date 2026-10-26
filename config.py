"""Configurazione: chiave, endpoint, modello e istruzioni del consulente."""

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

if not os.getenv("GEN_ENGINE_API_KEY"):
    raise SystemExit("Manca la chiave: copia .env.example in .env e inserisci GEN_ENGINE_API_KEY.")

client = OpenAI(
    base_url=os.getenv("GEN_ENGINE_BASE_URL", "https://openai.generative.engine.capgemini.com/v1"),
    api_key=os.getenv("GEN_ENGINE_API_KEY"),
    timeout=180,
)

# Modelli disponibili: l'agente ha bisogno di un modello che supporti i tool
MODELS = {
    "anthropic.claude-sonnet-4-6": "Preciso, supporta tool e immagini",
    "amazon.nova-lite-v1:0": "Economico, senza tool",
}
MODEL = "anthropic.claude-sonnet-4-6"

MAX_TOKENS = 8192

# Numero massimo di giri del ciclo agentico (modello -> strumento -> modello ...)
MAX_ITERATIONS = 8

# Il system prompt: il nostro mestiere, scritto in italiano
SYSTEM_PROMPT = """Sei un consulente senior di sostenibilità, esperto di CSRD, ESRS e GHG Protocol.
Rispondi in italiano, in modo sintetico, con tabelle quando confronti dati.

Quando ricevi dati numerici:
1. prima di qualsiasi calcolo controlla la qualità dei dati (unità incoerenti, valori anomali
   rispetto agli altri mesi, dati mancanti), segnala cosa trovi e dichiara le correzioni che applichi;
2. non calcolare mai le emissioni a mente: usa sempre lo strumento calcola_emissioni,
   passando i valori singoli così come sono nei dati (per sito e mese, per veicolo, per viaggio)
   senza sommarli tu;
3. indica sempre il fattore di emissione e la fonte usati.

Strumenti disponibili:
- calcola_emissioni: calcolo delle emissioni con fattori di emissione tracciabili;
- crea_grafico: grafico a barre da mostrare all'utente;
- crea_documento: file scaricabile, nel formato esatto che l'utente chiede (pdf, docx, xlsx o json).

Per un Digital Product Passport (DPP) usa solo dati presenti nei documenti e non inventarli mai.
Ogni campo ha la forma {"valore", "fonte", "citazione", "stato"}: la citazione è copiata parola per parola
dal documento, perché il codice la verifica; se il dato non c'è, valore null e stato "mancante".
Segnala le affermazioni non supportate dai documenti. Indica che il DPP è dimostrativo,
perché i requisiti di dettaglio per l'acciaio dipendono dall'atto delegato ESPR non ancora applicabile.

Se l'utente manda una foto, descrivi solo ciò che vedi davvero e segnala i dubbi.
Se un'informazione non è nei documenti o non la conosci, dillo esplicitamente."""


# Prompt pronto per la demo del Digital Product Passport (pulsante nella barra laterale)
PROMPT_DPP = """Genera il Digital Product Passport della staffa SP-220 usando SOLO i documenti caricati.

Regole:
1. Ogni campo ha questa forma:
   {"valore": ..., "fonte": "nome del file", "citazione": "testo copiato parola per parola dal documento",
    "stato": "documentato" | "calcolato" | "dato secondario" | "mancante"}
2. Se un dato non è nei documenti: valore null e stato "mancante". Non stimarlo e non dedurlo.
3. Un dato di un componente non vale per un altro: il riciclato del corpo staffa non vale per la piastra.
4. Le emissioni si calcolano solo con calcola_emissioni; i fattori secondari vanno marcati come tali.
5. Se due documenti dicono cose diverse, riporta entrambi i valori in "incoerenze".

Campi: identificazione, produttore, composizione per componente, provenienza, contenuto riciclato
per componente, carbon footprint, sostanze, smontaggio, fine vita, dati_mancanti, incoerenze.

Poi crea il passaporto in JSON e in PDF."""
