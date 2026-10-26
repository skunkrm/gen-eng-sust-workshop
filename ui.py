"""Interfaccia del Sustainability Copilot: tutto l'aspetto grafico sta qui, la logica resta in app.py.

Tre stili, scelti con la variabile ESG_STILE nel file .env (predefinito "carta"):
- carta: sfondo bianco, pochi elementi, massima leggibilita'; nell'intestazione una linea delle emissioni
  che scorre e diventa ambra quando l'agente lavora;
- aurora: come carta, con una luce pastello animata nell'intestazione;
- ardesia: scuro e animato, con un campo di particelle che accelera quando l'agente lavora.

In tutti gli stili:
- intestazione con il nome dell'agente e una frase che si scrive da sola (FRASI, diverse per ogni step);
- pannello "Tempi e costi" a destra, richiudibile in una pillola: cronometro della richiesta e della sessione,
  costo calcolato con i prezzi del modello scelto (PREZZI in config.py), token di input e output,
  barra del budget mensile di 4 $;
- sotto ogni risposta le misure: tempo, token, costo e modello;
- bordo luminoso attorno al pannello dell'agente mentre lavora;
- pulsanti per il tema chiaro o scuro (predefinito chiaro, la scelta resta salvata nel browser)
  e per il tutto schermo.

Niente librerie esterne: CSS e JavaScript puro, inseriti con st.html. Il tema di base di Streamlit
(colori, carattere, barra laterale) sta in .streamlit/config.toml.
"""

import html
import json
import os

import streamlit as st

from config import PREZZI

NOME = "Sustainability Copilot"  # il nome dell'agente, in un punto solo
# Stile grafico: "carta" (bianco e pulito), "aurora" (bianco con luce nell'intestazione), "ardesia" (scuro e animato)
STILE = os.getenv("ESG_STILE", "carta")
AVATAR_UTENTE = ":material/person:"
AVATAR_AGENTE = ":material/eco:"
BUDGET_MENSILE = 4.0  # dollari del piano gratuito del Generative Engine

FRASI = ["legge bilanci, certificati e schede tecniche.", "calcola le emissioni con il codice.",
         "trova gli errori nei dati.", "verifica ogni citazione nei documenti.",
         "costruisce passaporti digitali di prodotto.", "prepara report Excel e PDF."]

CSS = r"""
<style>
@property --angolo { syntax: '<angle>'; initial-value: 0deg; inherits: false; }

:root, html[data-esg-tema="scuro"] {
  --fondo: #0B1317; --testo: #E6EEEA; --testo-2: #9DB2A9;
  --vetro: rgba(20, 33, 40, .58); --vetro-forte: rgba(16, 27, 33, .78);
  --bordo: rgba(255, 255, 255, .08); --luce: rgba(255, 255, 255, .06);
  --lichene: #7DCB8A; --ambra: #F0AE4E; --menta: #B8F2C1;
  --ombra: 0 30px 60px -30px rgba(0, 0, 0, .8);
  --tabella-testa: rgba(125, 203, 138, .16);
}
html[data-esg-tema="chiaro"] {
  --fondo: #E9F0EC; --testo: #12201A; --testo-2: #4D635A;
  --vetro: rgba(255, 255, 255, .62); --vetro-forte: rgba(255, 255, 255, .82);
  --bordo: rgba(18, 40, 32, .10); --luce: rgba(255, 255, 255, .7);
  --lichene: #2F8A45; --ambra: #C2780F; --menta: #1F6B33;
  --ombra: 0 30px 60px -34px rgba(20, 50, 40, .45);
  --tabella-testa: rgba(47, 138, 69, .12);
}

/* ---------- tela di fondo ---------- */
html, body { background: var(--fondo) !important; transition: background .6s ease; }
#esg-tela { position: fixed; inset: 0; width: 100vw; height: 100vh; z-index: -1; pointer-events: none; }
#esg-aurora { position: fixed; inset: -20vmax; z-index: -1; pointer-events: none; filter: blur(70px); opacity: .55;
  background:
    radial-gradient(35vmax 30vmax at 20% 25%, rgba(125, 203, 138, .20), transparent 70%),
    radial-gradient(30vmax 26vmax at 80% 70%, rgba(240, 174, 78, .16), transparent 70%),
    radial-gradient(28vmax 24vmax at 60% 10%, rgba(80, 160, 190, .12), transparent 70%);
  animation: esg-aurora 26s ease-in-out infinite alternate; }
html[data-esg-tema="chiaro"] #esg-aurora { opacity: .8; }
@keyframes esg-aurora { 0% { transform: translate3d(0, 0, 0) rotate(0deg) scale(1); }
  50% { transform: translate3d(4vmax, -3vmax, 0) rotate(8deg) scale(1.08); }
  100% { transform: translate3d(-3vmax, 2vmax, 0) rotate(-6deg) scale(1.02); } }
#esg-grana { position: fixed; inset: 0; z-index: -1; pointer-events: none; opacity: .05; mix-blend-mode: overlay;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E"); }

.stApp, [data-testid="stAppViewContainer"], .stMain, [data-testid="stHeader"],
[data-testid="stBottom"], [data-testid="stBottomBlockContainer"], [data-testid="stBottom"] > div {
  background: transparent !important; }
.stApp { color: var(--testo); }
.stMain [data-testid="stMarkdownContainer"], .stMain p,
.stMain li, .stMain h1, .stMain h2, .stMain h3,
.stMain td, .stMain th, .stMain summary { color: var(--testo); }
.stMain :where(p, li, h1, h2, h3, h4, td, th, summary, em, span, label, textarea):not(.esg-testata *):not([data-testid="stDownloadButton"] *):not([data-testid="stIconMaterial"]) {
  color: var(--testo) !important; }
html[data-esg-tema="chiaro"] .stMain strong:not(.esg-testata *) { color: var(--menta) !important; }
html[data-esg-tema="chiaro"] [data-testid="stChatInput"] textarea::placeholder { color: #6B8077 !important; }
[data-testid="stDecoration"], [data-testid="stHeaderActionElements"] { display: none; }
.block-container { padding-top: 1rem; padding-bottom: 6rem; max-width: 1200px; }

/* ---------- vetro ---------- */
.esg-vetro, [data-testid="stChatMessage"], .st-key-domande button, [data-testid="stChatInput"] > div {
  background: var(--vetro) !important; border: 1px solid var(--bordo) !important;
  backdrop-filter: blur(18px) saturate(150%); -webkit-backdrop-filter: blur(18px) saturate(150%);
  box-shadow: inset 0 1px 0 var(--luce), var(--ombra); }

/* luce che segue il mouse */
[data-testid="stChatMessage"], .st-key-domande button, .esg-testata { position: relative; overflow: hidden; }
[data-testid="stChatMessage"]::before, .st-key-domande button::before, .esg-testata::before {
  content: ""; position: absolute; inset: 0; pointer-events: none; opacity: 0; transition: opacity .35s;
  background: radial-gradient(420px circle at var(--mx, 50%) var(--my, 50%), rgba(125, 203, 138, .13), transparent 60%); }
[data-testid="stChatMessage"]:hover::before, .st-key-domande button:hover::before, .esg-testata:hover::before { opacity: 1; }

/* ---------- intestazione ---------- */
.esg-testata { border-radius: 1.1rem; padding: 1.4rem 2rem 1.4rem; margin-bottom: 1.5rem;
  background: linear-gradient(140deg, rgba(14, 26, 31, .82), rgba(14, 26, 31, .55)) !important; color: #E6EEEA; }
/* l'entrata animata solo alla prima apertura, non a ogni aggiornamento dei contatori */
html:not([data-esg-visto]) .esg-testata { animation: esg-entra .9s cubic-bezier(.16, 1, .3, 1) both; }
html[data-esg-tema="chiaro"] .esg-testata { background: linear-gradient(140deg, rgba(14, 30, 26, .92), rgba(22, 44, 38, .78)) !important; }
.esg-testata.lavoro::after { content: ""; position: absolute; inset: 0; border-radius: inherit; padding: 1.5px; pointer-events: none;
  background: conic-gradient(from var(--angolo), transparent 0 62%, var(--ambra) 78%, #7DCB8A 90%, transparent 100%);
  -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0); -webkit-mask-composite: xor;
  mask: linear-gradient(#000 0 0) content-box exclude, linear-gradient(#000 0 0);
  animation: esg-gira 2.2s linear infinite; }
@keyframes esg-gira { to { --angolo: 360deg; } }
@keyframes esg-entra { from { opacity: 0; transform: translateY(14px) scale(.985); filter: blur(6px); } to { opacity: 1; transform: none; filter: none; } }

.esg-alto { display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; }
.esg-stato { display: inline-flex; align-items: center; gap: .55rem; padding: .35rem .8rem .35rem .65rem;
  border-radius: 99px; background: rgba(125, 203, 138, .12); border: 1px solid rgba(125, 203, 138, .25);
  font-size: .82rem; color: #B8F2C1; font-weight: 600; }
.esg-stato i { width: .5rem; height: .5rem; border-radius: 50%; background: #7DCB8A; box-shadow: 0 0 10px #7DCB8A; }
.esg-testata.lavoro .esg-stato { background: rgba(240, 174, 78, .12); border-color: rgba(240, 174, 78, .35); color: #FFD08A; }
.esg-testata.lavoro .esg-stato i { background: #F0AE4E; box-shadow: 0 0 12px #F0AE4E; animation: esg-impulso 1.1s ease-out infinite; }
@keyframes esg-impulso { 0% { box-shadow: 0 0 0 0 rgba(240, 174, 78, .8); } 100% { box-shadow: 0 0 0 .75rem rgba(240, 174, 78, 0); } }

.esg-tema { all: unset; cursor: pointer; width: 2.6rem; height: 2.6rem; border-radius: 50%; display: grid; place-items: center;
  background: rgba(255, 255, 255, .06); border: 1px solid rgba(255, 255, 255, .12); color: #E6EEEA; font-size: 1.15rem;
  transition: transform .5s cubic-bezier(.16, 1, .3, 1), background .3s; }
.esg-tema:hover { background: rgba(255, 255, 255, .12); transform: rotate(40deg); }
.esg-tema:focus-visible { outline: 2px solid #7DCB8A; outline-offset: 3px; }
.esg-comandi { display: flex; gap: .55rem; }
/* tutto schermo: icona disegnata in CSS, cambia quando si entra o si esce */
.esg-schermo { font-size: 0; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23E6EEEA' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: center;
  background-size: 1.15rem; }
.esg-schermo:hover { transform: scale(1.08); }
html[data-esg-schermo="pieno"] .esg-schermo { background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23E6EEEA' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M9 4v5H4M15 4v5h5M9 20v-5H4M15 20v-5h5'/%3E%3C/svg%3E"); }

.esg-titolo { margin: .7rem 0 0; font-size: clamp(2.4rem, 5.4vw, 4rem); line-height: .95; font-weight: 800;
  letter-spacing: -0.045em; padding: 0;
  background: linear-gradient(100deg, #FFFFFF 10%, #B8F2C1 35%, #7DCB8A 50%, #F0AE4E 68%, #FFFFFF 90%);
  background-size: 300% 100%; -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
  animation: esg-scorre 9s ease-in-out infinite alternate; }
@keyframes esg-scorre { from { background-position: 0% 0; } to { background-position: 100% 0; } }
.esg-macchina { margin: .7rem 0 0; font-size: 1.15rem; color: #A9BFB5; min-height: 1.6em; }
.esg-macchina b { color: #FFFFFF; font-weight: 600; }
.esg-macchina b::after { content: ""; display: inline-block; width: 2px; height: 1.1em; margin-left: 3px; vertical-align: -0.18em;
  background: #7DCB8A; animation: esg-cursore 1s steps(1) infinite; }
@keyframes esg-cursore { 50% { opacity: 0; } }

/* ---------- pannello dei contatori, fisso a destra e richiudibile ---------- */
.esg-pannello { position: fixed; top: 4.2rem; right: 1.2rem; width: 290px; z-index: 999990; max-height: calc(100vh - 6rem);
  overflow-y: auto; padding: 1rem; border-radius: 1.1rem; color: #E6EEEA;
  background: rgba(12, 22, 27, .74); border: 1px solid rgba(255, 255, 255, .08);
  backdrop-filter: blur(20px) saturate(150%); -webkit-backdrop-filter: blur(20px) saturate(150%);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, .06), 0 30px 60px -30px rgba(0, 0, 0, .8);
  transition: transform .55s cubic-bezier(.16, 1, .3, 1), opacity .4s; }
html[data-esg-pannello="chiuso"] .esg-pannello { transform: translateX(calc(100% + 2rem)); opacity: 0; pointer-events: none; }
.esg-pannello-testa { display: flex; justify-content: space-between; align-items: center; margin-bottom: .7rem; }
.esg-pannello-testa h4 { margin: 0; padding: 0; font-size: .95rem; font-weight: 700; color: #CDEFD3; }
.esg-chiudi { all: unset; cursor: pointer; width: 2rem; height: 2rem; display: grid; place-items: center; border-radius: .6rem;
  color: #E6EEEA; background: rgba(255, 255, 255, .06); border: 1px solid rgba(255, 255, 255, .1); font-size: 1rem; }
.esg-chiudi:hover { background: rgba(255, 255, 255, .12); }
.esg-strumenti { display: grid; gap: .6rem; }
.esg-strumento { padding: .75rem .9rem; border-radius: .8rem; background: rgba(255, 255, 255, .04);
  border: 1px solid rgba(255, 255, 255, .07); }
.esg-strumento span { display: block; font-size: .76rem; color: #8FA79C; }
.esg-strumento b { display: block; margin-top: .2rem; font-size: 1.45rem; font-weight: 700; color: #FFFFFF;
  font-variant-numeric: tabular-nums; letter-spacing: -0.02em; }
.esg-strumento.costo { background: linear-gradient(160deg, rgba(240, 174, 78, .14), rgba(240, 174, 78, .03));
  border-color: rgba(240, 174, 78, .28); }
.esg-strumento.costo b { color: #FFC46E; text-shadow: 0 0 22px rgba(240, 174, 78, .45); }
.esg-budget { height: 4px; margin-top: .55rem; border-radius: 9px; background: rgba(255, 255, 255, .08); overflow: hidden; }
.esg-budget i { display: block; height: 100%; width: var(--quota, 0%); min-width: 3px; border-radius: 9px;
  background: linear-gradient(90deg, #7DCB8A, #F0AE4E); box-shadow: 0 0 12px rgba(240, 174, 78, .6);
  transition: width 1s cubic-bezier(.16, 1, .3, 1); }
.esg-budget-nota { font-size: .72rem; color: #8FA79C; margin-top: .3rem; }
.esg-strumento small, .esg-strumento small span { display: block; margin-top: .25rem; font-size: .74rem; color: #8FA79C; line-height: 1.3; }
.esg-strumento.tempo b { color: #CDEFD3; font-size: 1.9rem; }
.esg-pannello.lavoro .esg-strumento.tempo { border-color: rgba(240, 174, 78, .45); box-shadow: 0 0 24px -6px rgba(240, 174, 78, .5); }
.esg-pannello.lavoro::after { content: ""; position: absolute; inset: 0; border-radius: inherit; padding: 1.5px; pointer-events: none;
  background: conic-gradient(from var(--angolo), transparent 0 62%, #F0AE4E 78%, #7DCB8A 90%, transparent 100%);
  -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0); -webkit-mask-composite: xor;
  mask: linear-gradient(#000 0 0) content-box exclude, linear-gradient(#000 0 0); animation: esg-gira 2.2s linear infinite; }

/* pannello chiuso: resta una pillola con tempo e costo, che lo riapre */
.esg-pillola { all: unset; cursor: pointer; position: fixed; top: 4.2rem; right: 1.2rem; z-index: 999990;
  display: flex; align-items: center; gap: .7rem; padding: .5rem .9rem .5rem .7rem; border-radius: 99px;
  background: rgba(12, 22, 27, .8); color: #E6EEEA; border: 1px solid rgba(240, 174, 78, .3);
  backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); font-size: .85rem; font-variant-numeric: tabular-nums;
  box-shadow: 0 16px 40px -16px rgba(0, 0, 0, .7); opacity: 0; transform: translateX(1rem); pointer-events: none;
  transition: opacity .4s .15s, transform .55s .15s cubic-bezier(.16, 1, .3, 1); }
html[data-esg-pannello="chiuso"] .esg-pillola { opacity: 1; transform: none; pointer-events: auto; }
.esg-pillola b { color: #FFFFFF; font-weight: 700; } .esg-pillola .c { color: #FFC46E; }
.esg-pillola i { width: .5rem; height: .5rem; border-radius: 50%; background: #7DCB8A; box-shadow: 0 0 10px #7DCB8A; }
.esg-pillola.lavoro i { background: #F0AE4E; animation: esg-impulso 1.1s ease-out infinite; }

/* con il pannello aperto il contenuto lascia spazio a destra (sugli schermi larghi) */
@media (min-width: 1200px) {
  html:not([data-esg-pannello="chiuso"]) .block-container { padding-right: 330px !important; }
  html:not([data-esg-pannello="chiuso"]) [data-testid="stBottomBlockContainer"] { padding-right: 330px !important; }
}

/* misure sotto ogni risposta */
.esg-misure { display: flex; flex-wrap: wrap; gap: .45rem; margin: .2rem 0 .7rem; }
.esg-misure span { padding: .22rem .65rem; border-radius: 99px; font-size: .8rem; font-variant-numeric: tabular-nums;
  background: rgba(125, 203, 138, .10); border: 1px solid rgba(125, 203, 138, .22); color: var(--testo) !important; }
.esg-misure span.c { background: rgba(240, 174, 78, .10); border-color: rgba(240, 174, 78, .3); }

/* barra laterale richiudibile: il pulsante per chiuderla e riaprirla sempre visibile */
[data-testid="stSidebarCollapseButton"], [data-testid="stSidebarCollapseButton"] button { opacity: 1 !important; visibility: visible !important; display: flex !important; }
[data-testid="stExpandSidebarButton"] { opacity: 1 !important; visibility: visible !important;
  background: rgba(12, 22, 27, .8) !important; border: 1px solid rgba(125, 203, 138, .35) !important; border-radius: .6rem !important; color: #E6EEEA !important; }

/* ---------- pagina iniziale ---------- */
.esg-invito h2 { font-size: 1.7rem; font-weight: 800; letter-spacing: -0.03em; margin: .2rem 0 .25rem; padding: 0; }
.esg-invito p { color: var(--testo-2) !important; margin: 0 0 1.1rem; }
.st-key-domande button { min-height: 5.4rem; border-radius: 1rem !important; color: var(--testo) !important;
  font-weight: 650; font-size: 1rem; justify-content: flex-start; align-items: flex-end; padding: 1rem 1.1rem; text-align: left;
  transition: transform .35s cubic-bezier(.16, 1, .3, 1), border-color .3s; animation: esg-entra .8s cubic-bezier(.16, 1, .3, 1) both; }
.st-key-domande [data-testid="stColumn"]:nth-child(1) button { animation-delay: .15s; }
.st-key-domande [data-testid="stColumn"]:nth-child(2) button { animation-delay: .25s; }
.st-key-domande [data-testid="stColumn"]:nth-child(3) button { animation-delay: .35s; }
.st-key-domande [data-testid="stColumn"]:nth-child(4) button { animation-delay: .45s; }
.st-key-domande button > div, .st-key-domande button [data-testid="stMarkdownContainer"] { width: 100%; justify-content: flex-start; text-align: left; }
.st-key-domande button:hover { transform: translateY(-3px); border-color: rgba(125, 203, 138, .5) !important; }
.st-key-domande button [data-testid="stIconMaterial"] { font-size: 1.6rem; color: var(--lichene); position: absolute; top: 1rem; left: 1.1rem; }

/* ---------- conversazione ---------- */
[data-testid="stChatMessage"] { border-radius: 1rem; padding: 1.2rem 1.4rem; margin-bottom: 1.1rem;
  animation: esg-entra .7s cubic-bezier(.16, 1, .3, 1) both; }
[data-testid="stChatMessage"][data-esg-utente] { background: transparent !important; border-color: transparent !important;
  box-shadow: none; backdrop-filter: none; padding-top: .3rem; padding-bottom: .3rem; }
[data-testid="stChatMessage"][data-esg-utente] p { font-size: 1.12rem; font-weight: 550; }
[data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li { line-height: 1.62; max-width: 84ch; }
[data-testid="stChatMessage"] h1, [data-testid="stChatMessage"] h2, [data-testid="stChatMessage"] h3 {
  font-size: 1.28rem; font-weight: 750; letter-spacing: -0.02em; margin-top: 1.1rem; }
[data-testid="stChatMessage"] strong { color: var(--menta); }
[data-testid="stChatMessageAvatarCustom"] { background: rgba(125, 203, 138, .15) !important; border: 1px solid rgba(125, 203, 138, .3); }
[data-testid="stChatMessageAvatarCustom"] [data-testid="stIconMaterial"] { color: var(--lichene) !important; }

/* bordo luminoso attorno alla risposta mentre l'agente lavora */
[data-testid="stChatMessage"][data-esg-attivo]::after { content: ""; position: absolute; inset: 0; border-radius: inherit; padding: 1.5px;
  pointer-events: none; background: conic-gradient(from var(--angolo), transparent 0 60%, var(--ambra) 78%, var(--lichene) 92%, transparent 100%);
  -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0); -webkit-mask-composite: xor;
  mask: linear-gradient(#000 0 0) content-box exclude, linear-gradient(#000 0 0); animation: esg-gira 2s linear infinite; }

/* tabelle: righe che entrano una alla volta */
[data-testid="stChatMessage"] table { border-collapse: separate; border-spacing: 0; font-size: .95rem; margin: .8rem 0 1.2rem;
  border: 1px solid var(--bordo); border-radius: .8rem; overflow: hidden; }
[data-testid="stChatMessage"] th { background: var(--tabella-testa); font-weight: 700; text-align: left; padding: .6rem .85rem; border: none; }
[data-testid="stChatMessage"] td { padding: .5rem .85rem; border: none; border-top: 1px solid var(--bordo);
  font-variant-numeric: tabular-nums; vertical-align: top; }
[data-testid="stChatMessage"] tbody tr { animation: esg-riga .6s cubic-bezier(.16, 1, .3, 1) both; transition: background .2s; }
[data-testid="stChatMessage"] tbody tr:hover td { background: rgba(125, 203, 138, .07); }
""" + "".join(f'[data-testid="stChatMessage"] tbody tr:nth-child({i}) {{ animation-delay: {0.25 + i * 0.07:.2f}s; }}\n'
              for i in range(1, 16)) + r"""
@keyframes esg-riga { from { opacity: 0; transform: translateX(-10px); } to { opacity: 1; transform: none; } }

/* pannello dei passaggi */
[data-testid="stChatMessage"] [data-testid="stExpander"] details { background: rgba(0, 0, 0, .12); border: 1px solid var(--bordo);
  border-left: 3px solid var(--lichene); border-radius: .7rem; }
html[data-esg-tema="chiaro"] [data-testid="stChatMessage"] [data-testid="stExpander"] details { background: rgba(255, 255, 255, .5); }

/* download: brillano quando compaiono */
[data-testid="stDownloadButton"] button { position: relative; overflow: hidden; border: none !important; border-radius: .7rem;
  background: linear-gradient(135deg, #8FDB9C, #4FA864) !important; color: #06150B !important; font-weight: 750;
  box-shadow: 0 10px 30px -10px rgba(125, 203, 138, .9); animation: esg-pronto 1.4s ease-out 1 both; }
[data-testid="stDownloadButton"] button p { color: #06150B !important; }
[data-testid="stDownloadButton"] button::after { content: ""; position: absolute; top: 0; bottom: 0; width: 40%; left: -60%;
  background: linear-gradient(100deg, transparent, rgba(255, 255, 255, .65), transparent); animation: esg-lampo 3.5s ease-in-out infinite; }
[data-testid="stDownloadButton"] button:hover { transform: translateY(-1px); filter: brightness(1.06); }
@keyframes esg-lampo { 0%, 55% { left: -60%; } 100% { left: 130%; } }
@keyframes esg-pronto { 0% { transform: scale(.9); box-shadow: 0 0 0 0 rgba(125, 203, 138, .9); }
  60% { transform: scale(1.02); } 100% { transform: none; box-shadow: 0 0 0 18px rgba(125, 203, 138, 0), 0 10px 30px -10px rgba(125, 203, 138, .9); } }

/* barra di scrittura */
[data-testid="stChatInput"] > div { border-radius: 1rem !important; transition: box-shadow .3s, border-color .3s; }
[data-testid="stChatInput"] > div:focus-within { border-color: rgba(125, 203, 138, .6) !important;
  box-shadow: 0 0 0 4px rgba(125, 203, 138, .15), var(--ombra); }
[data-testid="stChatInput"] textarea { color: var(--testo) !important; font-size: 1.02rem; }
[data-testid="stChatInput"] textarea:focus, [data-testid="stChatInput"] textarea:focus-visible { outline: none !important; box-shadow: none !important; }
[data-testid="stChatInputSubmitButton"] { background: var(--lichene) !important; color: #06150B !important; border-radius: .6rem; }

/* barra laterale in vetro scuro, uguale nei due temi */
[data-testid="stSidebar"] { background: rgba(8, 15, 18, .72) !important; backdrop-filter: blur(22px) saturate(140%);
  border-right: 1px solid rgba(255, 255, 255, .06); }
[data-testid="stSidebar"] > div { background: transparent !important; }
[data-testid="stSidebar"] h3 { font-size: .9rem; font-weight: 700; color: #8FA79C; margin-top: .6rem; }


:focus-visible { outline: 2px solid var(--lichene) !important; outline-offset: 2px; }


/* ================= STILI CHIARI E PULITI: "carta" e "aurora" ================= */
html[data-esg-tema="chiaro"] {
  --fondo: #FFFFFF; --testo: #17211C; --testo-2: #56655D;
  --vetro: #FFFFFF; --vetro-forte: #FFFFFF; --bordo: #DFE6E2; --luce: rgba(255, 255, 255, 0);
  --lichene: #2E7D47; --ambra: #B0650A; --menta: #1D6B37;
  --ombra: 0 1px 2px rgba(16, 24, 20, .05), 0 10px 28px -18px rgba(16, 24, 20, .22);
  --tabella-testa: #EEF3F0;
}
/* meno fronzoli: niente vetro sfocato, niente luce che segue il mouse, niente riflessi continui */
html:is([data-esg-stile="carta"], [data-esg-stile="aurora"]) :is(.esg-vetro, [data-testid="stChatMessage"], [data-testid="stChatInput"] > div) {
  backdrop-filter: none !important; -webkit-backdrop-filter: none !important; }
html:is([data-esg-stile="carta"], [data-esg-stile="aurora"]) :is([data-testid="stChatMessage"], .esg-testata)::before { display: none; }
html:is([data-esg-stile="carta"], [data-esg-stile="aurora"]) [data-testid="stDownloadButton"] button::after { display: none; }
html:is([data-esg-stile="carta"], [data-esg-stile="aurora"]) [data-testid="stChatMessage"] tbody tr { animation: none; }
html:is([data-esg-stile="carta"], [data-esg-stile="aurora"]) [data-testid="stChatMessage"] { animation-duration: .4s; }

/* conversazione e tabelle nel tema chiaro: alto contrasto */
html[data-esg-tema="chiaro"] [data-testid="stChatMessage"] { box-shadow: var(--ombra); }
html[data-esg-tema="chiaro"] [data-testid="stChatMessage"] [data-testid="stExpander"] details { background: #F7F9F8; }
html[data-esg-tema="chiaro"] [data-testid="stChatMessage"] th { color: #17211C !important; }
html[data-esg-tema="chiaro"] [data-testid="stChatMessageAvatarCustom"] { background: #E8F3EC !important; border-color: #CFE5D6; }
html[data-esg-tema="chiaro"] [data-testid="stDownloadButton"] button { background: #2E7D47 !important; color: #FFFFFF !important;
  box-shadow: 0 6px 16px -8px rgba(46, 125, 71, .7); }
html[data-esg-tema="chiaro"] [data-testid="stDownloadButton"] button p { color: #FFFFFF !important; }
html[data-esg-tema="chiaro"] [data-testid="stChatInputSubmitButton"] { background: #2E7D47 !important; color: #FFFFFF !important; }
html[data-esg-tema="chiaro"] [data-testid="stChatInput"] > div { background: #FFFFFF !important; border: 1.5px solid #C9D3CD !important; }

/* pannello Tempi e costi e pillola nel tema chiaro */
html[data-esg-tema="chiaro"] .esg-pannello, html[data-esg-tema="chiaro"] .esg-pillola {
  background: #FFFFFF; color: #17211C; border: 1px solid #DFE6E2; backdrop-filter: none; -webkit-backdrop-filter: none;
  box-shadow: 0 1px 2px rgba(16, 24, 20, .05), 0 16px 40px -24px rgba(16, 24, 20, .3); }
html[data-esg-tema="chiaro"] .esg-pannello-testa h4 { color: #17211C; }
html[data-esg-tema="chiaro"] .esg-chiudi { color: #17211C; background: #F2F5F3; border-color: #DFE6E2; }
html[data-esg-tema="chiaro"] .esg-strumento { background: #F7F9F8; border-color: #E6ECE8; }
html[data-esg-tema="chiaro"] .esg-strumento span, html[data-esg-tema="chiaro"] .esg-strumento small,
html[data-esg-tema="chiaro"] .esg-strumento small span, html[data-esg-tema="chiaro"] .esg-budget-nota { color: #56655D; }
html[data-esg-tema="chiaro"] .esg-strumento b { color: #17211C; }
html[data-esg-tema="chiaro"] .esg-strumento.tempo b { color: #1D6B37; }
html[data-esg-tema="chiaro"] .esg-strumento.costo { background: #FFF7EC; border-color: #F1D6AE; }
html[data-esg-tema="chiaro"] .esg-strumento.costo b, html[data-esg-tema="chiaro"] .esg-pillola .c { color: #A45C06; text-shadow: none; }
html[data-esg-tema="chiaro"] .esg-pillola b { color: #17211C; }
html[data-esg-tema="chiaro"] .esg-budget { background: #E9EEEB; }

/* ---------- CARTA: bianco, tipografia, una linea viva ---------- */
html[data-esg-stile="carta"][data-esg-tema="chiaro"] [data-testid="stSidebar"] { background: #F5F7F6 !important;
  backdrop-filter: none; border-right: 1px solid #E3E8E5; }
html[data-esg-stile="carta"][data-esg-tema="chiaro"] [data-testid="stSidebar"] h3 { color: #56655D; }
html[data-esg-stile="carta"][data-esg-tema="chiaro"] .esg-testata { background: #FFFFFF !important; color: #17211C;
  border: 1px solid #DFE6E2 !important; box-shadow: var(--ombra); }
html[data-esg-stile="carta"] .esg-testata { padding-bottom: 3.6rem !important; }
html[data-esg-stile="carta"] .esg-testata::before { display: block !important; content: ""; position: absolute; left: 0; right: 0; bottom: 0; top: auto;
  height: 46px; opacity: 1; pointer-events: none; background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 480 90' preserveAspectRatio='none'%3E %3Cstyle%3E.l%7Bfill:none;stroke:%232E7D47;stroke-width:2.2;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:700;stroke-dashoffset:700;animation:d 2.2s cubic-bezier(.16,1,.3,1) .3s forwards%7D .a%7Bfill:url(%23g);opacity:0;animation:f 1.2s ease 1.6s forwards%7D%40keyframes d%7Bto%7Bstroke-dashoffset:0%7D%7D%40keyframes f%7Bto%7Bopacity:1%7D%7D %40media (prefers-reduced-motion:reduce)%7B.l%7Banimation:none;stroke-dashoffset:0%7D.a%7Banimation:none;opacity:1%7D%7D%3C/style%3E %3Cdefs%3E%3ClinearGradient id='g' x1='0' y1='0' x2='0' y2='1'%3E%3Cstop offset='0' stop-color='%232E7D47' stop-opacity='.16'/%3E%3Cstop offset='1' stop-color='%232E7D47' stop-opacity='0'/%3E%3C/linearGradient%3E%3C/defs%3E %3Cpolygon class='a' points='0,70 40,62 80,66 120,50 160,54 200,40 240,46 280,30 320,36 360,22 400,28 440,16 480,20 480,90 0,90'/%3E%3Cpolyline class='l' points='0,70 40,62 80,66 120,50 160,54 200,40 240,46 280,30 320,36 360,22 400,28 440,16 480,20'/%3E%3C/svg%3E") center / 100% 100% no-repeat; }
html[data-esg-stile="carta"] .esg-testata.lavoro::before { background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 480 90' preserveAspectRatio='none'%3E %3Cstyle%3E.b%7Bfill:none;stroke:%232E7D47;stroke-opacity:.35;stroke-width:2.2%7D.m%7Bfill:none;stroke:%23C77712;stroke-width:3;stroke-linecap:round;stroke-dasharray:60 640;animation:m 1.6s linear infinite%7D %40keyframes m%7Bfrom%7Bstroke-dashoffset:0%7Dto%7Bstroke-dashoffset:-700%7D%7D%3C/style%3E %3Cpolyline class='b' points='0,70 40,62 80,66 120,50 160,54 200,40 240,46 280,30 320,36 360,22 400,28 440,16 480,20'/%3E%3Cpolyline class='m' points='0,70 40,62 80,66 120,50 160,54 200,40 240,46 280,30 320,36 360,22 400,28 440,16 480,20'/%3E%3C/svg%3E"); }
html[data-esg-stile="carta"][data-esg-tema="chiaro"] .esg-titolo { background: none; -webkit-text-fill-color: #17211C; color: #17211C;
  animation: none; position: relative; }
html[data-esg-stile="carta"][data-esg-tema="chiaro"] .esg-macchina { color: #56655D; position: relative; }
html[data-esg-stile="carta"][data-esg-tema="chiaro"] .esg-macchina b { color: #17211C; }
html[data-esg-tema="chiaro"] .esg-stato { background: #E8F3EC; border-color: #CFE5D6; color: #1D6B37; }
html[data-esg-tema="chiaro"] .esg-stato i { box-shadow: none; background: #2E7D47; }
html[data-esg-tema="chiaro"] .esg-testata.lavoro .esg-stato { background: #FDF1E1; border-color: #F1D6AE; color: #8A4F05; }
html[data-esg-tema="chiaro"] .esg-testata.lavoro .esg-stato i { background: #C77712; }
html[data-esg-tema="chiaro"] .esg-tema { background-color: #F2F5F3; border-color: #DFE6E2; color: #17211C; }
html[data-esg-tema="chiaro"] .esg-schermo { background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2317211C' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5'/%3E%3C/svg%3E"); }
html[data-esg-tema="chiaro"][data-esg-schermo="pieno"] .esg-schermo { background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2317211C' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M9 4v5H4M15 4v5h5M9 20v-5H4M15 20v-5h5'/%3E%3C/svg%3E"); }

/* ---------- AURORA: bianco, intestazione con una luce morbida che si muove ---------- */
html[data-esg-stile="aurora"][data-esg-tema="chiaro"] .esg-testata { color: #17211C; border: 1px solid #DCE8E1 !important;
  background: linear-gradient(115deg, #E4F4EA 0%, #E3EFF5 30%, #FBF1E3 55%, #E4F4EA 80%, #E3EFF5 100%) !important;
  background-size: 300% 300% !important; animation: esg-luce 18s ease-in-out infinite alternate; box-shadow: var(--ombra); }
html[data-esg-stile="aurora"][data-esg-tema="chiaro"] .esg-testata.lavoro { animation-duration: 3s; }
@keyframes esg-luce { from { background-position: 0% 40%; } to { background-position: 100% 60%; } }
html[data-esg-stile="aurora"][data-esg-tema="chiaro"] .esg-titolo {
  background: linear-gradient(100deg, #14432A 0%, #1F6B45 45%, #1E5E70 100%); -webkit-background-clip: text; background-clip: text;
  -webkit-text-fill-color: transparent; animation: none; }
html[data-esg-stile="aurora"][data-esg-tema="chiaro"] .esg-macchina { color: #3F5248; }
html[data-esg-stile="aurora"][data-esg-tema="chiaro"] .esg-macchina b { color: #17211C; }
html[data-esg-stile="aurora"][data-esg-tema="chiaro"] .esg-tema { background-color: rgba(255, 255, 255, .7); }
html[data-esg-stile="aurora"][data-esg-tema="chiaro"] [data-testid="stSidebar"] { background: #15261D !important; backdrop-filter: none; }

@media (prefers-reduced-motion: reduce) {
  html[data-esg-stile="aurora"] .esg-testata { animation: none !important; }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important; transition: none !important; }
  .esg-titolo { -webkit-text-fill-color: #FFFFFF; }
}
</style>
"""

JS = r"""
<script>
(() => {
  const D = document, W = window;
  const lento = W.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // ---------- tema ----------
  const leggiTema = () => { try { return localStorage.getItem('esg-tema') || 'chiaro'; } catch (e) { return 'chiaro'; } };
  D.documentElement.dataset.esgTema = D.documentElement.dataset.esgTema || leggiTema();

  if (W.esgPronto) { W.esgAggiorna && W.esgAggiorna(); return; }
  W.esgPronto = true;
  setTimeout(() => D.documentElement.setAttribute('data-esg-visto', ''), 1500);

  try { if (localStorage.getItem('esg-pannello') === 'chiuso') D.documentElement.dataset.esgPannello = 'chiuso'; } catch (e) {}
  // ---------- tutto schermo (si esce anche con Esc) ----------
  D.addEventListener('click', ev => {
    if (!ev.target.closest('[data-esg-schermo-pulsante]')) return;
    if (D.fullscreenElement) D.exitFullscreen(); else D.documentElement.requestFullscreen().catch(() => {});
  });
  D.addEventListener('fullscreenchange', () => {
    if (D.fullscreenElement) D.documentElement.dataset.esgSchermo = 'pieno';
    else delete D.documentElement.dataset.esgSchermo;
  });

  D.addEventListener('click', ev => {
    if (!ev.target.closest('[data-esg-pannello-pulsante]')) return;
    const chiuso = D.documentElement.dataset.esgPannello === 'chiuso' ? 'aperto' : 'chiuso';
    D.documentElement.dataset.esgPannello = chiuso;
    try { localStorage.setItem('esg-pannello', chiuso); } catch (e) {}
  });
  D.addEventListener('click', ev => {
    const b = ev.target.closest('[data-esg-tema-pulsante]');
    if (!b) return;
    const nuovo = D.documentElement.dataset.esgTema === 'chiaro' ? 'scuro' : 'chiaro';
    D.documentElement.dataset.esgTema = nuovo;
    try { localStorage.setItem('esg-tema', nuovo); } catch (e) {}
    W.esgAggiorna();
  });

  // ---------- luce che segue il mouse ----------
  D.addEventListener('pointermove', ev => {
    const el = ev.target.closest('[data-testid="stChatMessage"], .st-key-domande button, .esg-testata');
    if (!el) return;
    const r = el.getBoundingClientRect();
    el.style.setProperty('--mx', (ev.clientX - r.left) + 'px');
    el.style.setProperty('--my', (ev.clientY - r.top) + 'px');
  }, { passive: true });

  // ---------- sfondo: aurora, grana e campo di flusso ----------
  const vivo = D.documentElement.dataset.esgStile === 'ardesia';  // particelle e aurora solo nello stile ardesia
  if (vivo) ['esg-aurora', 'esg-grana'].forEach(id => { if (!D.getElementById(id)) { const d = D.createElement('div'); d.id = id; D.body.prepend(d); } });
  const tela = D.createElement('canvas'); tela.id = 'esg-tela'; if (vivo) D.body.prepend(tela);
  const ctx = tela.getContext('2d');
  let L = 0, A = 0, particelle = [], energia = .5, obiettivo = .5, t = 0;
  const dpr = Math.min(W.devicePixelRatio || 1, 1.5);
  const nuova = () => ({ x: Math.random() * L, y: Math.random() * A, vita: 80 + Math.random() * 220 });
  const misura = () => {
    L = W.innerWidth; A = W.innerHeight; tela.width = L * dpr; tela.height = A * dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    const n = Math.min(1100, Math.round(L * A / 1700));
    particelle = Array.from({ length: n }, nuova);
  };
  misura(); W.addEventListener('resize', misura);

  const mescola = (a, b, k) => a.map((v, i) => Math.round(v + (b[i] - v) * k));
  const AMBRA = [240, 174, 78], LICHENE = [125, 203, 138];
  const AMBRA_C = [194, 120, 15], LICHENE_C = [47, 138, 69];

  const passo = () => {
    const chiaro = D.documentElement.dataset.esgTema === 'chiaro';
    if (chiaro !== W.esgUltimoChiaro) {  // cambio di tema: ripulisce la tela in un colpo solo
      W.esgUltimoChiaro = chiaro; ctx.fillStyle = chiaro ? '#E9F0EC' : '#0B1317'; ctx.fillRect(0, 0, L, A);
    }
    energia += (obiettivo - energia) * .03;
    t += .004 + energia * .006;
    ctx.globalCompositeOperation = 'source-over';
    ctx.fillStyle = chiaro ? 'rgba(233,240,236,0.10)' : 'rgba(11,19,23,0.09)';
    ctx.fillRect(0, 0, L, A);
    ctx.lineWidth = 1.1;
    const v = .55 + energia * 2.2;
    for (const p of particelle) {
      const ang = (Math.sin(p.x * .0021 + t) + Math.cos(p.y * .0026 - t * .8) + Math.sin((p.x + p.y) * .0012 + t * .5)) * Math.PI * .75;
      const nx = p.x + Math.cos(ang) * v, ny = p.y + Math.sin(ang) * v;
      const k = Math.min(1, Math.max(0, p.x / L));
      const c = chiaro ? mescola(AMBRA_C, LICHENE_C, k) : mescola(AMBRA, LICHENE, k);
      const alfa = (chiaro ? .20 : .32) * (0.6 + energia * .5);
      ctx.strokeStyle = `rgba(${c[0]},${c[1]},${c[2]},${alfa})`;
      ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(nx, ny); ctx.stroke();
      p.x = nx; p.y = ny; p.vita--;
      if (p.vita < 0 || p.x < -5 || p.x > L + 5 || p.y < -5 || p.y > A + 5) Object.assign(p, nuova());
    }
    if (!lento && !D.hidden) requestAnimationFrame(passo);
  };
  D.addEventListener('visibilitychange', () => { if (vivo && !D.hidden && !lento) requestAnimationFrame(passo); });
  if (vivo) { if (lento) { for (let i = 0; i < 120; i++) passo(); } else requestAnimationFrame(passo); }



  // ---------- cronometro della richiesta in corso e del totale ----------
  const durata = s => s < 60 ? s.toFixed(1).replace('.', ',') + ' s'
    : Math.floor(s / 60) + ' min ' + String(Math.floor(s % 60)).padStart(2, '0') + ' s';
  setInterval(() => {
    D.querySelectorAll('[data-inizio]').forEach(el => {
      const s = parseFloat(el.dataset.base || '0') + (Date.now() - parseFloat(el.dataset.inizio)) / 1000;
      el.textContent = (el.dataset.prefisso ? el.dataset.prefisso + ' ' : '') + durata(Math.max(0, s));
    });
  }, 100);

  // ---------- frase che si scrive da sola ----------
  let f = 0, c = 0, cancella = false;
  setInterval(() => {
    const el = D.querySelector('.esg-macchina b'); if (!el) return;
    const frasi = JSON.parse(el.dataset.frasi || '[]'); if (!frasi.length) return;
    const frase = frasi[f % frasi.length];
    if (lento) { el.textContent = frase; return; }
    if (!cancella) { c++; if (c > frase.length + 28) cancella = true; }
    else { c -= 2; if (c <= 0) { c = 0; cancella = false; f++; } }
    el.textContent = frase.slice(0, Math.min(c, frase.length));
  }, 55);

  // ---------- ad ogni aggiornamento della pagina ----------
  W.esgAggiorna = () => {
    const lavoro = !!D.querySelector('.esg-testata.lavoro');
    obiettivo = lavoro ? 1.6 : .45;
    const messaggi = [...D.querySelectorAll('[data-testid="stChatMessage"]')];
    messaggi.forEach((m, i) => {
      const icona = m.querySelector('[data-testid="stIconMaterial"]');
      const utente = icona && icona.textContent.trim() === 'person';
      // attributi data-* e non classi: React riscrive le classi a ogni aggiornamento
      m.toggleAttribute('data-esg-utente', !!utente);
      m.toggleAttribute('data-esg-attivo', lavoro && !utente && i === messaggi.length - 1);
    });
    D.documentElement.toggleAttribute('data-esg-lavoro', lavoro);
    const pulsante = D.querySelector('[data-esg-tema-pulsante]');
    if (pulsante) pulsante.textContent = D.documentElement.dataset.esgTema === 'chiaro' ? '☾' : '☀';

    // contatori che scorrono dal valore precedente al nuovo
    D.querySelectorAll('.esg-strumento b[data-valore]').forEach(el => {
      if (el.dataset.fatto) return; el.dataset.fatto = '1';
      const fine = parseFloat(el.dataset.valore), formato = el.dataset.formato, chiave = 'esg-' + el.dataset.chiave;
      let inizio = 0;
      try { inizio = parseFloat(sessionStorage.getItem(chiave) || '0') || 0; sessionStorage.setItem(chiave, String(fine)); } catch (e) {}
      const scrivi = v => {
        if (formato === 'int') el.textContent = Math.round(v).toLocaleString('it-IT');
        else el.textContent = v.toFixed(v < 1 ? 4 : 2).replace('.', ',') + ' $';  // sempre in dollari, come in Python
      };
      if (lento || inizio === fine) { scrivi(fine); return; }
      const t0 = performance.now();
      const anima = now => { const p = Math.min(1, (now - t0) / 1100), e = 1 - Math.pow(1 - p, 4);
        scrivi(inizio + (fine - inizio) * e); if (p < 1) requestAnimationFrame(anima); };
      requestAnimationFrame(anima);
    });
  };
  // al massimo un aggiornamento ogni 80 ms (la frase che si scrive genera mutazioni di continuo)
  new MutationObserver(() => { if (!W.esgAttesa) W.esgAttesa = setTimeout(() => { W.esgAttesa = null; W.esgAggiorna(); }, 80); })
    .observe(D.body, { childList: true, subtree: true });
  W.esgAggiorna();
})();
</script>
"""


def stile():
    """Da chiamare una volta, subito dopo st.set_page_config.
    Il CSS viene inserito dal JavaScript. Attenzione: dentro lo script niente testo simile a tag HTML
    (il filtro di st.html lo scarterebbe), per questo i '<' nelle stringhe sono scritti come \\u003c."""
    regole = CSS.replace("<style>", "").replace("</style>", "")
    inserisci = (f"document.documentElement.dataset.esgStile = '{STILE}';\n"
                 "(() => { let s = document.getElementById('esg-stile');"
                 " if (!s) { s = document.createElement('style'); s.id = 'esg-stile'; document.head.appendChild(s); }"
                 f" s.textContent = {json.dumps(regole).replace('<', '\\u003c')}; }})();\n")  # '<' scritto come \\u003c per il filtro HTML
    st.html(JS.replace("<script>", "<script>" + inserisci, 1), unsafe_allow_javascript=True)


def nome_breve(modello):
    """anthropic.claude-haiku-5-5 -> Haiku 5.5, amazon.nova-lite-v1:0 -> Nova Lite"""
    nome = modello.split(".", 1)[-1].replace("claude-", "").split(":")[0]
    parti = [p for p in nome.split("-") if not (p.startswith("v") and p[1:].isdigit())]
    numeri = [p for p in parti if p.isdigit()]
    parole = [p.capitalize() for p in parti if not p.isdigit()]
    return " ".join(parole) + (" " + ".".join(numeri) if numeri else "")


def _intero(n):
    return f"{int(n):,}".replace(",", ".")


def _costo(dollari):
    """Sempre in dollari, come il catalogo dei prezzi: 4 decimali sotto il dollaro (0,0312 $), poi 2."""
    return f"{dollari:.{4 if dollari < 1 else 2}f} $".replace(".", ",")


def _durata(secondi):
    if secondi < 60:
        return f"{secondi:.1f} s".replace(".", ",")
    return f"{int(secondi // 60)} min {int(secondi % 60):02d} s"


def testata(contenitore, modello, documenti, token, dollari, secondi, ultima,
            inizio=None, token_richiesta=0, costo_richiesta=0.0, tok_in=0, tok_out=0, frasi=None):
    """Intestazione con i contatori. token, dollari e secondi sono i totali della sessione;
    durante una richiesta (inizio valorizzato) si aggiungono i valori parziali, e il tempo scorre nel browser."""
    lavoro = inizio is not None
    token_tot, costo_tot = token + token_richiesta, dollari + costo_richiesta
    quota = min(100.0, costo_tot / BUDGET_MENSILE * 100)
    prezzo_in, prezzo_out = PREZZI.get(modello, (0, 0))
    stato = "L'agente sta lavorando" if lavoro else "Pronto"
    frasi = html.escape(json.dumps(frasi or FRASI, ensure_ascii=False))  # le frasi che si scrivono da sole

    if lavoro:  # tempo della richiesta in corso: lo fa scorrere il JavaScript
        tempo = f'<b data-inizio="{inizio * 1000:.0f}" data-base="0">0,0 s</b>'
        tempo_nota = f'<span data-inizio="{inizio * 1000:.0f}" data-base="{secondi}" data-prefisso="Totale">Totale {_durata(secondi)}</span>'
        nota_costo = f"Questa richiesta {_costo(costo_richiesta)}"
    elif ultima:
        tempo = f"<b>{_durata(ultima['secondi'])}</b>"
        tempo_nota = f"<span>Totale {_durata(secondi)}</span>"
        nota_costo = f"Ultima richiesta {_costo(ultima['costo'])}"
    else:
        tempo, tempo_nota = "<b>–</b>", "<span>Nessuna richiesta</span>"
        nota_costo = "Nessuna richiesta"
    # token divisi in input e output: il costo si ricalcola a mano con i prezzi del modello
    nota_token = f"input {_intero(tok_in)}, output {_intero(tok_out)}"

    if lavoro:
        pillola_tempo = f'<b data-inizio="{inizio * 1000:.0f}" data-base="0">0,0 s</b>'
    else:
        pillola_tempo = f"<b>{_durata(ultima['secondi']) if ultima else '–'}</b>"

    contenitore.html(f"""
<div class="esg-testata esg-vetro{' lavoro' if lavoro else ''}">
  <div class="esg-alto">
    <div class="esg-stato"><i></i>{stato}</div>
    <div class="esg-comandi">
      <button class="esg-tema esg-schermo" data-esg-schermo-pulsante title="Tutto schermo" aria-label="Tutto schermo">schermo</button>
      <button class="esg-tema" data-esg-tema-pulsante title="Cambia tema" aria-label="Cambia tema chiaro o scuro">☀</button>
    </div>
  </div>
  <h1 class="esg-titolo">{NOME}</h1>
  <p class="esg-macchina">L'agente <b data-frasi="{frasi}"></b></p>
</div>

<aside class="esg-pannello{' lavoro' if lavoro else ''}" aria-label="Contatori della sessione">
  <div class="esg-pannello-testa"><h4>Tempi e costi</h4>
    <button class="esg-chiudi" data-esg-pannello-pulsante title="Chiudi il pannello" aria-label="Chiudi il pannello">›</button></div>
  <div class="esg-strumenti">
    <div class="esg-strumento tempo"><span>Tempo richiesta</span>{tempo}<small>{tempo_nota}</small></div>
    <div class="esg-strumento costo"><span>Costo della sessione</span>
      <b data-chiave="costo" data-valore="{costo_tot}" data-formato="costo">{_costo(costo_tot)}</b><small>{nota_costo}</small>
      <div class="esg-budget" style="--quota:{quota:.3f}%"><i></i></div>
      <div class="esg-budget-nota">{f"{quota:.2f}".replace(".", ",")}% del budget mensile di 4 $</div>
    </div>
    <div class="esg-strumento"><span>Token della sessione</span>
      <b data-chiave="token" data-valore="{token_tot}" data-formato="int">{_intero(token_tot)}</b><small>{nota_token}</small></div>
    <div class="esg-strumento"><span>Modello</span><b>{html.escape(nome_breve(modello))}</b>
      <small>{f"{prezzo_in:g}".replace(".", ",")} $ in / {f"{prezzo_out:g}".replace(".", ",")} $ out per milione di token</small></div>
    <div class="esg-strumento"><span>Documenti letti</span><b>{documenti}</b><small>nella memoria dell'agente</small></div>
  </div>
</aside>

<button class="esg-pillola{' lavoro' if lavoro else ''}" data-esg-pannello-pulsante title="Apri tempi e costi" aria-label="Apri tempi e costi">
  <i></i>{pillola_tempo}<b class="c">{_costo(costo_tot)}</b><span>‹</span>
</button>""")


def misure(a):
    """Riga sotto ogni risposta: quanto ci ha messo, quanti token, quanto è costata e con quale modello."""
    st.html(f"""<div class="esg-misure">
  <span>⏱ {_durata(a['secondi'])}</span><span>{_intero(a['token'])} token</span>
  <span class="c">{_costo(a['costo'])}</span><span>{html.escape(nome_breve(a['modello']))}</span></div>""")
