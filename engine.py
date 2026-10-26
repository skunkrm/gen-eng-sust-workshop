"""La logica della chat: manda conversazione e documenti al modello."""

from config import MAX_TOKENS, MODEL, SYSTEM_PROMPT, client


def build_messages(message, history, knowledge_base=""):
    """Prepara i messaggi da mandare al modello.

    Alcuni modelli del Generative Engine non accettano il ruolo "system",
    quindi le istruzioni (e i documenti) vanno come primo scambio utente/assistente.
    """
    istruzioni = SYSTEM_PROMPT
    if knowledge_base:
        istruzioni += (
            "\n\nL'utente ha caricato questi documenti. Usali per rispondere e cita il documento "
            "da cui prendi ogni informazione.\n\n" + knowledge_base
        )
    return [
        {"role": "user", "content": istruzioni},
        {"role": "assistant", "content": "Ho capito. Come posso aiutarti?"},
        *history,
        {"role": "user", "content": message},
    ]


def reply(message, history, knowledge_base="", model=MODEL):
    """Restituisce (testo della risposta, (token di input, token di output))."""
    risposta = client.chat.completions.create(
        model=model,
        messages=build_messages(message, history, knowledge_base),
        max_tokens=MAX_TOKENS,
    )
    testo = risposta.choices[0].message.content or ""
    uso = risposta.usage
    token = (uso.prompt_tokens, uso.completion_tokens) if uso else (0, 0)  # input e output: costano diversamente
    return testo, token
