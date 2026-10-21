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

# Modelli a confronto: il primo è quello di partenza
MODELS = {
    "amazon.nova-lite-v1:0": "Economico, meno preciso",
    "anthropic.claude-sonnet-4-6": "Più costoso, più preciso",
}
MODEL = "amazon.nova-lite-v1:0"

MAX_TOKENS = 4096

# Il system prompt: il nostro mestiere, scritto in italiano
SYSTEM_PROMPT = """Sei un consulente senior di sostenibilità, esperto di CSRD, ESRS e GHG Protocol.
Rispondi in italiano, in modo sintetico, con tabelle quando confronti dati.
Quando ricevi dati numerici, prima di qualsiasi considerazione controlla la qualità dei dati
(unità incoerenti, valori anomali rispetto agli altri mesi, dati mancanti) e segnala cosa trovi.
Indica sempre fattori di emissione e fonti quando li usi.
Se un'informazione non è nei documenti o non la conosci, dillo esplicitamente."""
