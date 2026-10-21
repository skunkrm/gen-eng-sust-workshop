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
- crea_documento: file scaricabile, nel formato esatto che l'utente chiede (pdf, docx o xlsx).

Se l'utente manda una foto, descrivi solo ciò che vedi davvero e segnala i dubbi.
Se un'informazione non è nei documenti o non la conosci, dillo esplicitamente."""
