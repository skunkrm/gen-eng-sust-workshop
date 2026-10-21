"""La logica della chat: manda la conversazione al modello e restituisce la risposta."""

from config import MAX_TOKENS, MODEL, SYSTEM_PROMPT, client


def build_messages(message, history):
    """Prepara i messaggi da mandare al modello.

    Alcuni modelli del Generative Engine non accettano il ruolo "system",
    quindi le istruzioni vanno come primo scambio utente/assistente.
    """
    return [
        {"role": "user", "content": SYSTEM_PROMPT},
        {"role": "assistant", "content": "Ho capito. Come posso aiutarti?"},
        *history,
        {"role": "user", "content": message},
    ]


def reply(message, history):
    """Restituisce (testo della risposta, token usati)."""
    risposta = client.chat.completions.create(
        model=MODEL,
        messages=build_messages(message, history),
        max_tokens=MAX_TOKENS,
    )
    testo = risposta.choices[0].message.content or ""
    token = risposta.usage.total_tokens if risposta.usage else 0
    return testo, token
