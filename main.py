"""Step 0 - La prima chiamata: il nostro codice fa una domanda al Generative Engine."""

import os

from dotenv import load_dotenv
from openai import APIConnectionError, APIStatusError, OpenAI

# Legge la chiave dal file .env
load_dotenv()

client = OpenAI(
    base_url=os.getenv("GEN_ENGINE_BASE_URL", "https://openai.generative.engine.capgemini.com/v1"),
    api_key=os.getenv("GEN_ENGINE_API_KEY"),
    timeout=60,
)

MODEL = "amazon.nova-lite-v1:0"
DOMANDA = "Spiegami in due frasi cos'è la doppia materialità nella CSRD."

try:
    risposta = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": DOMANDA}],
        max_tokens=300,
    )
    print(risposta.choices[0].message.content)
    uso = risposta.usage
    if uso:
        print(f"\n[Token usati: {uso.prompt_tokens} in ingresso, {uso.completion_tokens} in uscita]")
except APIConnectionError as errore:
    print(f"Impossibile contattare il Generative Engine: {errore}")
except APIStatusError as errore:
    print(f"Errore {errore.status_code}: {errore.response.text}")
