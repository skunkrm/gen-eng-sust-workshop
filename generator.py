"""Generazione di file (PDF, Word, Excel) e grafici, sempre in memoria con BytesIO."""

import re
from io import BytesIO

import docx
import matplotlib
import openpyxl
from docx.shared import Inches
from fpdf import FPDF, FontFace
from openpyxl.styles import Font, PatternFill

matplotlib.use("Agg")  # nessuna finestra: il grafico viene solo salvato in memoria
import matplotlib.pyplot as plt  # noqa: E402

VERDE = "1F4E5A"
MIME = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


# ---------- lettura del contenuto in markdown semplice ----------

def _blocchi(testo):
    """Divide il testo in blocchi: titoli, elenchi, tabelle, paragrafi."""
    blocchi, tabella = [], []
    for riga in testo.splitlines() + [""]:
        r = riga.strip()
        if "|" in r:
            celle = [c.strip() for c in r.strip("|").split("|")]
            if not all(re.fullmatch(r":?-{2,}:?", c) for c in celle if c):  # salta |---|---|
                tabella.append(celle)
            continue
        if tabella:
            blocchi.append(("tabella", tabella))
            tabella = []
        if not r:
            continue
        if r.startswith("## "):
            blocchi.append(("h2", r[3:]))
        elif r.startswith("# "):
            blocchi.append(("h1", r[2:]))
        elif r.startswith(("- ", "* ")):
            blocchi.append(("punto", r[2:]))
        else:
            blocchi.append(("testo", r))
    return blocchi


def _pulisci(testo):
    """Toglie il grassetto markdown."""
    return testo.replace("**", "")


def _numero(valore):
    """Converte '1.234,5' o '1234.5' o '12%' in numero, se possibile."""
    s = valore.replace(" ", "").replace(" ", "")
    perc = s.endswith("%")
    s = s.rstrip("%")
    if re.fullmatch(r"-?\d{1,3}(\.\d{3})+(,\d+)?", s) or re.fullmatch(r"-?\d+,\d+", s):
        s = s.replace(".", "").replace(",", ".")
    try:
        n = float(s)
    except ValueError:
        return valore
    return n / 100 if perc else n


# ---------- grafico ----------

def make_chart(titolo, etichette, valori, unita, serie_confronto=None, nomi_serie=None):
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150)
    x = range(len(etichette))
    if serie_confronto and len(serie_confronto) == len(valori):
        nomi = nomi_serie if nomi_serie and len(nomi_serie) == 2 else ["Serie 1", "Serie 2"]
        w = 0.38
        b1 = ax.bar([i - w / 2 for i in x], valori, w, label=nomi[0], color="#1F4E5A")
        b2 = ax.bar([i + w / 2 for i in x], serie_confronto, w, label=nomi[1], color="#9BC4BC")
        ax.legend(frameon=False)
        barre = list(b1) + list(b2)
    else:
        barre = ax.bar(list(x), valori, color="#1F4E5A")
    for b in barre:
        ax.annotate(f"{b.get_height():,.1f}".replace(",", "X").replace(".", ",").replace("X", "."),
                    (b.get_x() + b.get_width() / 2, b.get_height()), ha="center", va="bottom", fontsize=8)
    ax.set_xticks(list(x), etichette)
    ax.set_ylabel(unita)
    ax.set_title(titolo, fontsize=12, fontweight="bold", color="#1F4E5A")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    return buf.getvalue()


# ---------- Excel ----------

def _xlsx(titolo, contenuto):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Report"
    ws.append([titolo])
    ws["A1"].font = Font(bold=True, size=14, color=VERDE)
    ws.append([])
    for tipo, valore in _blocchi(contenuto):
        if tipo == "tabella":
            for i, riga in enumerate(valore):
                if i == 0:
                    ws.append([_pulisci(c) for c in riga])
                    for cella in ws[ws.max_row]:
                        cella.font = Font(bold=True, color="FFFFFF")
                        cella.fill = PatternFill("solid", fgColor=VERDE)
                else:
                    ws.append([_numero(_pulisci(c)) for c in riga])
                    for cella, testo in zip(ws[ws.max_row], riga):
                        if isinstance(cella.value, float) and testo.strip().endswith("%"):
                            cella.number_format = "0.0%"
                        elif isinstance(cella.value, (int, float)):
                            cella.number_format = "#,##0.0"
            ws.append([])
        elif tipo in ("h1", "h2"):
            ws.append([_pulisci(valore)])
            ws.cell(row=ws.max_row, column=1).font = Font(bold=True, size=12 if tipo == "h1" else 11, color=VERDE)
        else:
            ws.append([("• " if tipo == "punto" else "") + _pulisci(valore)])
    for colonna in ws.columns:
        lunghezza = max(len(str(c.value)) if c.value is not None and c.row > 2 else 0 for c in colonna)
        ws.column_dimensions[colonna[0].column_letter].width = min(max(12, lunghezza + 2), 60)
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ---------- Word ----------

def _docx(titolo, contenuto, grafico):
    d = docx.Document()
    d.add_heading(titolo, 0)
    for tipo, valore in _blocchi(contenuto):
        if tipo == "h1":
            d.add_heading(_pulisci(valore), 1)
        elif tipo == "h2":
            d.add_heading(_pulisci(valore), 2)
        elif tipo == "punto":
            d.add_paragraph(_pulisci(valore), style="List Bullet")
        elif tipo == "tabella":
            colonne = max(len(r) for r in valore)
            t = d.add_table(rows=0, cols=colonne)
            t.style = "Light Grid Accent 1"
            for riga in valore:
                celle = t.add_row().cells
                for i, c in enumerate(riga):
                    celle[i].text = _pulisci(c)
        else:
            d.add_paragraph(_pulisci(valore))
    if grafico:
        d.add_picture(BytesIO(grafico), width=Inches(6))
    buf = BytesIO()
    d.save(buf)
    return buf.getvalue()


# ---------- PDF ----------

_SOSTITUZIONI = {"€": "EUR", "’": "'", "‘": "'", "“": '"', "”": '"', "–": "-", "—": "-", "•": "-",
                 "₂": "2", "³": "3", "…": "...", "≈": "~", "→": "->", "≥": ">=", "≤": "<="}


def _latin1(testo):
    """I font standard del PDF usano latin-1: sostituiamo i caratteri che non ci stanno."""
    for a, b in _SOSTITUZIONI.items():
        testo = testo.replace(a, b)
    return testo.encode("latin-1", "replace").decode("latin-1")


def _pdf(titolo, contenuto, grafico):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(31, 78, 90)
    pdf.multi_cell(0, 9, _latin1(titolo), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    for tipo, valore in _blocchi(contenuto):
        pdf.set_text_color(31, 78, 90) if tipo in ("h1", "h2") else pdf.set_text_color(0, 0, 0)
        if tipo == "tabella":
            pdf.set_font("Helvetica", size=8.5)
            colonne = max(len(r) for r in valore)
            righe = [[_latin1(_pulisci(c)) for c in r] + [""] * (colonne - len(r)) for r in valore]
            stile = FontFace(emphasis="BOLD", color=255, fill_color=(31, 78, 90))
            with pdf.table(first_row_as_headings=True, headings_style=stile, line_height=5.5) as tabella:
                for r in righe:
                    riga = tabella.row()
                    for c in r:
                        riga.cell(c)
            pdf.ln(3)
        elif tipo in ("h1", "h2"):
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 13 if tipo == "h1" else 11.5)
            pdf.multi_cell(0, 7, _latin1(_pulisci(valore)), new_x="LMARGIN", new_y="NEXT")
        else:
            pdf.set_font("Helvetica", size=10)
            prefisso = "- " if tipo == "punto" else ""
            pdf.multi_cell(0, 5.5, _latin1(prefisso + _pulisci(valore)), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)
    if grafico:
        pdf.ln(3)
        pdf.image(BytesIO(grafico), w=pdf.epw)
    return bytes(pdf.output())


def make_document(formato, nome_file, titolo, contenuto, grafico=None):
    """Restituisce (bytes, nome del file, tipo MIME)."""
    formato = formato.lower()
    if formato == "xlsx":
        dati = _xlsx(titolo, contenuto)
    elif formato == "docx":
        dati = _docx(titolo, contenuto, grafico)
    elif formato == "pdf":
        dati = _pdf(titolo, contenuto, grafico)
    else:
        raise ValueError(f"Formato non supportato: {formato}")
    nome = re.sub(r"[^\w\-]+", "_", nome_file).strip("_") or "documento"
    return dati, f"{nome}.{formato}", MIME[formato]
