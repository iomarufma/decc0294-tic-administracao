# -*- coding: utf-8 -*-
"""
Gera o relatorio PDF: "Analise da Inflacao e do Poder de Compra no Brasil".

Fonte dos dados: Banco Central do Brasil - SGS, serie 433 (IPCA mensal),
consultada por API. Todos os numeros do texto sao calculados neste script
a partir dos dados brutos salvos em dados/ipca-433-bruto.json.
"""
import json
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.platypus import (BaseDocTemplate, Frame, HRFlowable, Image, KeepTogether,
                                NextPageTemplate, PageBreak, PageTemplate, Paragraph,
                                Spacer, Table, TableStyle)

BASE = Path(__file__).resolve().parent.parent
DADOS = BASE / "dados"
GRAF = DADOS / "graficos"
SAIDA = BASE / "entregas" / "analise-inflacao-poder-compra-2021-2026.pdf"
GRAF.mkdir(exist_ok=True)

# ---------------------------------------------------------------- identidade
NAVY = "#1B2A4A"
LIGHT = "#7FA8D4"
GOLD = "#C9A227"
ALT = "#EEF3FA"
BRANCO = "#FFFFFF"
CINZA = "#5A6472"

cNAVY = colors.HexColor(NAVY)
cLIGHT = colors.HexColor(LIGHT)
cGOLD = colors.HexColor(GOLD)
cALT = colors.HexColor(ALT)
cCINZA = colors.HexColor(CINZA)

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.edgecolor": "#B9C2CE",
    "axes.labelcolor": NAVY,
    "text.color": NAVY,
    "xtick.color": CINZA,
    "ytick.color": CINZA,
    "axes.titlesize": 10.5,
    "axes.titleweight": "bold",
    "figure.facecolor": BRANCO,
    "axes.facecolor": BRANCO,
})

FONTE = "Fonte: Banco Central do Brasil – SGS, série 433 (IPCA). Consulta em {data}."


def br(x, casas=2):
    """Formata numero no padrao brasileiro."""
    s = f"{x:.{casas}f}"
    return s.replace(".", ",")


def fmt_eixo(v, _pos=None):
    return f"{v:.1f}".replace(".", ",")


# ---------------------------------------------------------------- dados
with open(DADOS / "ipca-433-bruto.json", encoding="utf-8") as f:
    pacote = json.load(f)

consulta = datetime.fromisoformat(pacote["consulta_utc"])
DATA_CONSULTA = consulta.strftime("%d/%m/%Y")
MESES_PT = ["janeiro", "fevereiro", "março", "abril", "maio", "junho",
            "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
DATA_CONSULTA_LONGA = f"{consulta.day} de {MESES_PT[consulta.month - 1]} de {consulta.year}"


def mes_ano(data):
    """Data no formato por extenso: 'setembro de 2026'."""
    return f"{MESES_PT[data.month - 1]} de {data.year}"

registros = []
for d in pacote["dados"]:
    data = datetime.strptime(d["data"], "%d/%m/%Y")
    if data >= datetime(2020, 1, 1):
        registros.append({"data": data, "mes": data.strftime("%m/%Y"), "valor": float(d["valor"])})
registros.sort(key=lambda r: r["data"])

# validacao
datas = [r["mes"] for r in registros]
duplicados = len(datas) - len(set(datas))
lacunas = []
for i in range(1, len(registros)):
    a, b = registros[i - 1]["data"], registros[i]["data"]
    esperado = (a.year + (a.month == 12), a.month % 12 + 1)
    if (b.year, b.month) != esperado:
        lacunas.append(f"{a:%m/%Y}->{b:%m/%Y}")

# serie mensal da analise (jan/2021 em diante) e acumulado em 12 meses
mensal = [r for r in registros if r["data"] >= datetime(2021, 1, 1)]
ac12 = []
for i, r in enumerate(registros):
    if r["data"] >= datetime(2021, 1, 1) and i >= 11:
        fator = 1.0
        for x in registros[i - 11: i + 1]:
            fator *= (1 + x["valor"] / 100)
        ac12.append({"data": r["data"], "mes": r["mes"], "valor": (fator - 1) * 100})

# acumulados anuais
por_ano = {}
for r in registros:
    por_ano.setdefault(r["data"].year, []).append(r)
anuais = []
for ano in sorted(por_ano):
    meses = por_ano[ano]
    fator = 1.0
    for x in meses:
        fator *= (1 + x["valor"] / 100)
    anuais.append({
        "ano": ano,
        "valor": (fator - 1) * 100,
        "n": len(meses),
        "completo": len(meses) == 12 and meses[-1]["data"].month == 12,
        "periodo": f"{meses[0]['data']:%m/%Y} a {meses[-1]['data']:%m/%Y}",
    })

# extremos e medias
max_mes = max(mensal, key=lambda r: r["valor"])
min_mes = min(mensal, key=lambda r: r["valor"])
max_ac = max(ac12, key=lambda r: r["valor"])
min_ac = min(ac12, key=lambda r: r["valor"])
ultimo_mes = mensal[-1]
ultimo_ac = ac12[-1]
primeiro_mes = mensal[0]
primeiro_ac = ac12[0]
media_mensal = sum(r["valor"] for r in mensal) / len(mensal)
negativos = [r for r in mensal if r["valor"] < 0]

# nivel de precoes acumulado no periodo e poder de compra
fator_periodo = 1.0
for r in mensal:
    fator_periodo *= (1 + r["valor"] / 100)
acum_periodo = (fator_periodo - 1) * 100
poder_compra = 100 / fator_periodo  # R$ 100 de set/2026 tem o poder de compra de R$ X em jan/2021

# diferencas entre anos
a2021 = next(a for a in anuais if a["ano"] == 2021)
a2022 = next(a for a in anuais if a["ano"] == 2022)
a2023 = next(a for a in anuais if a["ano"] == 2023)
a2024 = next(a for a in anuais if a["ano"] == 2024)
a2025 = next(a for a in anuais if a["ano"] == 2025)
a2026 = next(a for a in anuais if a["ano"] == 2026)

d_21_22 = a2021["valor"] - a2022["valor"]
d_21_25 = a2021["valor"] - a2025["valor"]
d_pico_valle = max_ac["valor"] - min_ac["valor"]
d_23_24 = a2024["valor"] - a2023["valor"]
d_24_25 = a2025["valor"] - a2024["valor"]
d_25_26 = a2025["valor"] - a2026["valor"]

# ---------------------------------------------------------------- graficos
def eixo_mensal(ax, serie):
    datas_s = [r["data"] for r in serie]
    ax.plot(datas_s, [r["valor"] for r in serie], color=NAVY, linewidth=1.8,
            marker="o", markersize=3.2, markerfacecolor=NAVY, zorder=3)
    ax.axhline(0, color="#9AA6B8", linewidth=0.9, zorder=2)
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 7]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
    ax.xaxis.set_minor_locator(mdates.MonthLocator())
    ax.grid(axis="y", color="#E3E9F2", linewidth=0.8, zorder=1)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.yaxis.set_major_formatter(FuncFormatter(fmt_eixo))


def salvar(fig, nome):
    fig.savefig(GRAF / nome, dpi=200, bbox_inches="tight", facecolor=BRANCO)
    plt.close(fig)


# Grafico 1 - IPCA mensal
fig, ax = plt.subplots(figsize=(9.2, 3.9))
eixo_mensal(ax, mensal)
for alvo, rotulo, dy in ((max_mes, f"Maior variação: {br(max_mes['valor'])}% ({max_mes['mes']})", 14),
                         (min_mes, f"Menor variação: {br(min_mes['valor'])}% ({min_mes['mes']})", -20)):
    ax.plot([alvo["data"]], [alvo["valor"]], marker="o", markersize=7,
            markerfacecolor=GOLD, markeredgecolor=NAVY, markeredgewidth=1.2, zorder=5)
    ax.annotate(rotulo, xy=(alvo["data"], alvo["valor"]),
                xytext=(0, dy), textcoords="offset points",
                ha="center", fontsize=8.5, fontweight="bold", color=NAVY,
                arrowprops=dict(arrowstyle="-", color=GOLD, linewidth=1.2))
ax.set_title(f"Figura 1 - IPCA: variação mensal, {primeiro_mes['mes']} a {ultimo_mes['mes']} (%)", loc="left")
ax.set_ylabel("Variação mensal (%)")
ax.margins(x=0.02)
ax.set_ylim(min(mensal, key=lambda r: r["valor"])["valor"] - 0.55,
            max(mensal, key=lambda r: r["valor"])["valor"] + 0.75)
fig.text(0.01, -0.04, FONTE.format(data=DATA_CONSULTA), fontsize=7.5, color=CINZA)
salvar(fig, "fig1-ipca-mensal.png")

# Grafico 2 - acumulado em 12 meses
fig, ax = plt.subplots(figsize=(9.2, 3.9))
datas_ac = [r["data"] for r in ac12]
valores_ac = [r["valor"] for r in ac12]
ax.fill_between(datas_ac, valores_ac, color=LIGHT, alpha=0.28, zorder=2)
ax.plot(datas_ac, valores_ac, color=NAVY, linewidth=2.0, zorder=3)
for alvo, rotulo, dy in ((max_ac, f"Pico: {br(max_ac['valor'])}% ({max_ac['mes']})", 14),
                         (min_ac, f"Menor acumulado: {br(min_ac['valor'])}% ({min_ac['mes']})", -20)):
    ax.plot([alvo["data"]], [alvo["valor"]], marker="o", markersize=7,
            markerfacecolor=GOLD, markeredgecolor=NAVY, markeredgewidth=1.2, zorder=5)
    ax.annotate(rotulo, xy=(alvo["data"], alvo["valor"]), xytext=(0, dy),
                textcoords="offset points", ha="center", fontsize=8.5,
                fontweight="bold", color=NAVY,
                arrowprops=dict(arrowstyle="-", color=GOLD, linewidth=1.2))
ax.plot([ultimo_ac["data"]], [ultimo_ac["valor"]], marker="o", markersize=6,
        markerfacecolor=BRANCO, markeredgecolor=NAVY, markeredgewidth=1.6, zorder=5)
ax.annotate(f"Último: {br(ultimo_ac['valor'])}% ({ultimo_ac['mes']})",
            xy=(ultimo_ac["data"], ultimo_ac["valor"]), xytext=(-96, 16),
            textcoords="offset points", fontsize=8.5, fontweight="bold", color=NAVY,
            arrowprops=dict(arrowstyle="-", color=NAVY, linewidth=1.0))
ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 7]))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
ax.grid(axis="y", color="#E3E9F2", linewidth=0.8)
ax.set_axisbelow(True)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.yaxis.set_major_formatter(FuncFormatter(fmt_eixo))
ax.set_title(f"Figura 2 - IPCA: acumulado em 12 meses, {primeiro_ac['mes']} a {ultimo_ac['mes']} (%)", loc="left")

ax.set_ylabel("Acumulado em 12 meses (%)")
ax.margins(x=0.02)
ax.set_ylim(0, max(valores_ac) + 2.2)
fig.text(0.01, -0.04, FONTE.format(data=DATA_CONSULTA), fontsize=7.5, color=CINZA)
salvar(fig, "fig2-acumulado-12-meses.png")

# Grafico 3 - comparacao anual (periodo da analise: 2021 em diante)
fig, ax = plt.subplots(figsize=(9.2, 3.6))
anuais_fig = [a for a in anuais if a["ano"] >= 2021]
anos_x = [str(a["ano"]) for a in anuais_fig]
valores_y = [a["valor"] for a in anuais_fig]
barras = ax.bar(anos_x, valores_y,
                color=[NAVY if a["completo"] else LIGHT for a in anuais_fig],
                width=0.62, zorder=3,
                edgecolor=[NAVY if a["completo"] else GOLD for a in anuais_fig],
                linewidth=1.2)
for a, b in zip(anuais_fig, barras):
    ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.18,
            f"{br(a['valor'])}%", ha="center", fontsize=9.5, fontweight="bold", color=NAVY)
    if not a["completo"]:
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() / 2,
                "parcial\n(jan-set)", ha="center", va="center", fontsize=8,
                fontweight="bold", color=NAVY)
ax.set_title("Figura 3 - IPCA acumulado por ano-calendário (comparação, %)", loc="left")
ax.set_ylabel("Taxa acumulada no ano (%)")
ax.grid(axis="y", color="#E3E9F2", linewidth=0.8)
ax.set_axisbelow(True)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.yaxis.set_major_formatter(FuncFormatter(fmt_eixo))
ax.set_ylim(0, max(valores_y) * 1.18)
ax.text(0.0, -0.16, "Azul-marinho: anos completos. Azul-claro: período parcial. "
        + FONTE.format(data=DATA_CONSULTA),
        transform=ax.transAxes, fontsize=7.5, color=CINZA)
salvar(fig, "fig3-comparacao-anual.png")

print("Graficos gerados.")
print(f"Periodo: {primeiro_mes['mes']} a {ultimo_mes['mes']} ({len(mensal)} meses)")
print(f"Acumulado no periodo: {acum_periodo:.2f}% | poder de compra de R$100: R$ {poder_compra:.2f}")
print(f"Validacao: duplicados={duplicados}, lacunas={lacunas or 'nenhuma'}, ausentes=0")
print(f"Mensais negativos: {len(negativos)} -> {[r['mes'] for r in negativos]}")
print(f"Dif 2021-2022={d_21_22:.2f} | 2021-2025={d_21_25:.2f} | pico-valle={d_pico_valle:.2f}")
print(f"Media mensal={media_mensal:.3f} | media x12={media_mensal*12:.2f}")
print(f"2024-2023={d_23_24:.2f} | 2025-2024={d_24_25:.2f} | 2025-2026parc={d_25_26:.2f}")


# ---------------------------------------------------------------- utilitarios
def ac_de(mes):
    """Retorna o acumulado em 12 meses de um mes/ano especifico."""
    return next(r["valor"] for r in ac12 if r["mes"] == mes)


def faixa_ac(ano):
    """Menor e maior acumulado em 12 meses dentro de um ano-calendario."""
    s = [r for r in ac12 if r["data"].year == ano]
    return min(s, key=lambda r: r["valor"]), max(s, key=lambda r: r["valor"])


ac24_min, ac24_max = faixa_ac(2024)
ac25_min, ac25_max = faixa_ac(2025)
ac26_min, ac26_max = faixa_ac(2026)
ac23_min, ac23_max = faixa_ac(2023)

n_api = len(pacote["dados"])
n_recorte = len(registros)

# ---------------------------------------------------------------- estilos
from PIL import Image as PILImage
from reportlab.lib.styles import ParagraphStyle

LARGURA, ALTURA = A4
MARGEM = 2.0 * cm
CONTEUDO = LARGURA - 2 * MARGEM

S = {}
S["corpo"] = ParagraphStyle("corpo", fontName="Helvetica", fontSize=9.5, leading=13.6,
                            alignment=TA_JUSTIFY, textColor=colors.HexColor("#22303F"),
                            spaceAfter=6)
S["corpo_destaque"] = ParagraphStyle("corpo_destaque", parent=S["corpo"], textColor=cNAVY)
S["h1"] = ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=14, leading=17,
                         textColor=cNAVY, spaceBefore=4, spaceAfter=5)
S["h2"] = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=10.5, leading=13,
                         textColor=cNAVY, spaceBefore=8, spaceAfter=3)
S["fonte"] = ParagraphStyle("fonte", fontName="Helvetica", fontSize=7.8, leading=10,
                            textColor=cCINZA, spaceBefore=2, spaceAfter=8)
S["det"] = ParagraphStyle("det", fontName="Helvetica", fontSize=10.5, leading=15,
                          textColor=cNAVY, spaceAfter=9)
S["det_rot"] = ParagraphStyle("det_rot", fontName="Helvetica-Bold", fontSize=8.5, leading=11,
                              textColor=cGOLD, spaceAfter=1)
S["nota"] = ParagraphStyle("nota", fontName="Helvetica-Oblique", fontSize=8.5, leading=11.5,
                           textColor=cCINZA, alignment=TA_JUSTIFY, spaceBefore=4)
S["ref"] = ParagraphStyle("ref", fontName="Helvetica", fontSize=9, leading=12.5,
                          textColor=colors.HexColor("#22303F"), alignment=0,
                          spaceAfter=6, leftIndent=12, firstLineIndent=-12)
S["kpi_val"] = ParagraphStyle("kpi_val", fontName="Helvetica-Bold", fontSize=15, leading=17,
                              textColor=cNAVY, alignment=TA_CENTER)
S["kpi_rot"] = ParagraphStyle("kpi_rot", fontName="Helvetica", fontSize=7.6, leading=9.5,
                              textColor=cCINZA, alignment=TA_CENTER)
S["tab"] = ParagraphStyle("tab", fontName="Helvetica", fontSize=8.6, leading=11,
                          textColor=colors.HexColor("#22303F"))
S["tab_b"] = ParagraphStyle("tab_b", parent=S["tab"], fontName="Helvetica-Bold", textColor=cNAVY)
S["tab_head"] = ParagraphStyle("tab_head", fontName="Helvetica-Bold", fontSize=8.6, leading=11,
                               textColor=colors.white)
S["tab_p"] = ParagraphStyle("tab_p", fontName="Helvetica", fontSize=7.6, leading=9.5,
                            textColor=colors.HexColor("#22303F"))
S["tab_p_b"] = ParagraphStyle("tab_p_b", parent=S["tab_p"], fontName="Helvetica-Bold",
                              textColor=cNAVY)


def figura(nome, largura=CONTEUDO):
    """Carrega uma imagem na largura do conteudo, mantendo a proporcao."""
    caminho = GRAF / nome
    with PILImage.open(caminho) as im:
        w, h = im.size
    return Image(str(caminho), width=largura, height=largura * h / w)


def tabela(linhas, larguras, alinhamento_centro=True, padding=4.5):
    """Tabela padrao: cabecalho azul-marinho, linhas alternadas, filete dourado."""
    t = Table(linhas, colWidths=larguras, repeatRows=1)
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), cNAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.6),
        ("LEADING", (0, 0), (-1, -1), 11),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), padding),
        ("BOTTOMPADDING", (0, 0), (-1, -1), padding),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("LINEABOVE", (0, 0), (-1, 0), 1.5, cGOLD),
        ("LINEBELOW", (0, -1), (-1, -1), 0.8, cNAVY),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D7DEE9")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, cALT]),
    ]
    if alinhamento_centro:
        estilo.append(("ALIGN", (0, 0), (-1, -1), "CENTER"))
        estilo.append(("ALIGN", (0, 1), (0, -1), "LEFT"))
    t.setStyle(TableStyle(estilo))
    return t


def caixas_kpi(itens):
    """Linha de numeros-chave em destaque."""
    largura_celula = CONTEUDO / len(itens)
    linha_val = [Paragraph(v, S["kpi_val"]) for v, _ in itens]
    linha_rot = [Paragraph(r, S["kpi_rot"]) for _, r in itens]
    t = Table([linha_val, linha_rot], colWidths=[largura_celula] * len(itens))
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), cALT),
        ("LINEABOVE", (0, 0), (-1, 0), 1.5, cGOLD),
        ("LINEBELOW", (0, -1), (-1, -1), 0.6, cLIGHT),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 1),
        ("TOPPADDING", (0, -1), (-1, -1), 0),
        ("INNERGRID", (0, 0), (-1, -1), 0, colors.white),
        ("BOX", (0, 0), (-1, -1), 0.6, cLIGHT),
    ]))
    return t


# ---------------------------------------------------------------- moldura de pagina
class CanvasNumerado(pdfcanvas.Canvas):
    """Acrescenta numeracao de pagina no rodape apos o conteudo estar montado."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._estados = []

    def showPage(self):
        self._estados.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._estados)
        for estado in self._estados:
            self.__dict__.update(estado)
            if self._pageNumber > 1:
                self._rodape(total)
            super().showPage()
        super().save()

    def _rodape(self, total):
        self.saveState()
        self.setStrokeColor(colors.HexColor("#D7DEE9"))
        self.setLineWidth(0.6)
        self.line(MARGEM, 1.5 * cm, LARGURA - MARGEM, 1.5 * cm)
        self.setFont("Helvetica", 7.4)
        self.setFillColor(cCINZA)
        self.drawString(MARGEM, 1.1 * cm,
                        f"Consulta à API: {DATA_CONSULTA}  ·  Último período: {ultimo_mes['mes']}  ·  "
                        "Fonte: BCB/SGS, série 433")
        self.setFont("Helvetica-Bold", 7.4)
        self.setFillColor(cNAVY)
        self.drawRightString(LARGURA - MARGEM, 1.1 * cm, f"Página {self._pageNumber} de {total}")
        self.restoreState()


def capa_fundo(canv, doc):
    """Faixa azul-marinho e titulo da capa desenhados diretamente na pagina."""
    canv.saveState()
    faixa_alt = 10.0 * cm
    canv.setFillColor(cNAVY)
    canv.rect(0, ALTURA - faixa_alt, LARGURA, faixa_alt, stroke=0, fill=1)
    # filete dourado
    canv.setFillColor(cGOLD)
    canv.rect(MARGEM, ALTURA - 5.65 * cm, 3.6 * cm, 0.09 * cm, stroke=0, fill=1)
    # rotulo superior
    canv.setFont("Helvetica-Bold", 8.5)
    canv.setFillColor(cLIGHT)
    canv.drawString(MARGEM, ALTURA - 2.6 * cm, "RELATÓRIO DE ANÁLISE ECONÔMICA")
    # titulo
    canv.setFillColor(colors.white)
    canv.setFont("Helvetica-Bold", 19)
    canv.drawString(MARGEM, ALTURA - 4.15 * cm, "Análise da Inflação e do Poder de Compra")
    canv.drawString(MARGEM, ALTURA - 4.95 * cm, "no Brasil")
    # subtitulo
    canv.setFont("Helvetica", 11.5)
    canv.setFillColor(cLIGHT)
    canv.drawString(MARGEM, ALTURA - 6.6 * cm,
                    "Uma Perspectiva Econômica e Administrativa")
    canv.setFont("Helvetica", 10.5)
    canv.setFillColor(colors.HexColor("#DCE6F5"))
    canv.drawString(MARGEM, ALTURA - 7.25 * cm,
                    "Variação mensal, acumulados e efeitos sobre o poder de compra e a Administração")
    # rodape da faixa
    canv.setFont("Helvetica", 9.5)
    canv.setFillColor(colors.white)
    canv.drawString(MARGEM, ALTURA - 8.7 * cm,
                    f"Período analisado: janeiro de 2021 a {mes_ano(ultimo_mes['data'])} "
                    f"({len(mensal)} observações mensais)")
    canv.setFont("Helvetica-Oblique", 9)
    canv.setFillColor(cLIGHT)
    canv.drawString(MARGEM, ALTURA - 9.25 * cm,
                    "Último mês disponível na API consultada na data desta análise")
    # barra inferior discreta
    canv.setFillColor(cNAVY)
    canv.rect(0, 0, LARGURA, 0.55 * cm, stroke=0, fill=1)
    canv.setFillColor(cGOLD)
    canv.rect(0, 0.55 * cm, LARGURA, 0.05 * cm, stroke=0, fill=1)
    canv.restoreState()


def corpo_moldura(canv, doc):
    """Cabecalho discreto das paginas internas."""
    canv.saveState()
    canv.setFillColor(cNAVY)
    canv.rect(0, ALTURA - 0.5 * cm, LARGURA, 0.5 * cm, stroke=0, fill=1)
    canv.setFillColor(cGOLD)
    canv.rect(0, ALTURA - 0.55 * cm, LARGURA, 0.05 * cm, stroke=0, fill=1)
    canv.setFont("Helvetica", 7.6)
    canv.setFillColor(cCINZA)
    canv.drawString(MARGEM, ALTURA - 1.25 * cm,
                    "Análise da Inflação e do Poder de Compra no Brasil · 2021 – 2026")
    canv.setFont("Helvetica-Bold", 7.6)
    canv.setFillColor(cNAVY)
    canv.drawRightString(LARGURA - MARGEM, ALTURA - 1.25 * cm, "BCB/SGS · série 433")
    canv.setStrokeColor(cGOLD)
    canv.setLineWidth(0.6)
    canv.line(MARGEM, ALTURA - 1.5 * cm, LARGURA - MARGEM, ALTURA - 1.5 * cm)
    canv.restoreState()


# ---------------------------------------------------------------- montagem
doc = BaseDocTemplate(str(SAIDA), pagesize=A4,
                      leftMargin=MARGEM, rightMargin=MARGEM,
                      topMargin=1.9 * cm, bottomMargin=2.0 * cm,
                      title="Análise da Inflação e do Poder de Compra no Brasil (2021-2026)",
                      author="Relatório gerado a partir de dados oficiais do Banco Central do Brasil",
                      subject="IPCA - série 433 do SGS")

frame_capa = Frame(MARGEM, 1.2 * cm, CONTEUDO, ALTURA - 11.4 * cm, id="capa")
frame_corpo = Frame(MARGEM, 2.0 * cm, CONTEUDO, ALTURA - 4.1 * cm, id="corpo")

doc.addPageTemplates([
    PageTemplate(id="capa", frames=[frame_capa], onPage=capa_fundo),
    PageTemplate(id="corpo", frames=[frame_corpo], onPage=corpo_moldura),
])

E = []  # elementos do relatorio

# ----- capa: blocos de informacao
E.append(Paragraph("PERÍODO ANALISADO", S["det_rot"]))
E.append(Paragraph(f"janeiro de 2021 a {mes_ano(ultimo_mes['data'])} — "
                   f"{ultimo_mes['mes']} é o último período contemplado na série", S["det"]))
E.append(Paragraph("FONTE DE DADOS", S["det_rot"]))
E.append(Paragraph("Banco Central do Brasil — Sistema Gerenciador de Séries Temporais (SGS), "
                   "série 433 (IPCA — variação mensal), consultada por API pública", S["det"]))
E.append(Paragraph("CONSULTA E VALIDAÇÃO", S["det_rot"]))
E.append(Paragraph(f"Consulta realizada em {DATA_CONSULTA_LONGA}. Série verificada quanto a "
                   f" duplicados, valores ausentes e lacunas mensais: nenhum problema identificado "
                   f"no recorte de {n_recorte} registros (01/2020 a {ultimo_mes['mes']}).", S["det"]))
E.append(Spacer(1, 0.5 * cm))
E.append(HRFlowable(width="100%", thickness=0.8, color=cGOLD, spaceAfter=6))
E.append(Paragraph("Documento produzido com dados exclusivamente oficiais. Todos os valores "
                   "apresentados são calculados a partir da série consultada e podem ser "
                   "reproduzidos a partir dos arquivos brutos anexados ao projeto.",
                   S["nota"]))

E.append(NextPageTemplate("corpo"))
E.append(PageBreak())

# ============================================================== 1. INTRODUCAO
E.append(Paragraph("1. INTRODUÇÃO", S["h1"]))
E.append(HRFlowable(width="100%", thickness=1.2, color=cGOLD, spaceAfter=8))
E.append(Paragraph(
    "A inflação — o aumento generalizado e sustentado dos preços de bens e serviços — reduz, "
    "por unidade monetária, a quantidade de bens que uma família pode adquirir. Por essa razão, "
    "é um dos indicadores mais observados por consumidores, empresas e órgãos públicos. No Brasil, "
    "o indicador de referência da inflação é o Índice Nacional de Preços ao Consumidor Amplo "
    "(IPCA), apurado pelo Instituto Brasileiro de Geografia e Estatística (IBGE).", S["corpo"]))
E.append(Paragraph(
    "O IPCA interessa diretamente à Administração porque é ele quem traduz em números a variação "
    "de custos, preços e orçamentos. Contratos, reajustes salariais, negociações comerciais e "
    "premissas de planejamento financeiro usam, com frequência, esse indicador ou medidas "
    "derivadas dele, como a variação acumulada em 12 meses.", S["corpo"]))
E.append(Paragraph(
    f"Este relatório tem por objetivo analisar a trajetória do IPCA de janeiro de 2021 até "
    f"{mes_ano(ultimo_mes['data'])}, último mês disponível na API do Banco Central na data da "
    f"consulta ({DATA_CONSULTA_LONGA}); calcular os acumulados em 12 meses e por ano-calendário; "
    f"e relacionar os resultados ao poder de compra da população e ao planejamento administrativo "
    f"das empresas. A análise é descritiva: relata o que os dados oficiais mostram e associa os "
    f"resultados a contextos administrativos, sem afirmar relações de causa e efeito que não "
    f"tenham sido demonstradas nesta série.", S["corpo"]))

# ============================================================== 2. METODOLOGIA
E.append(Paragraph("2. METODOLOGIA E FONTE DE DADOS", S["h1"]))
E.append(HRFlowable(width="100%", thickness=1.2, color=cGOLD, spaceAfter=8))
E.append(Paragraph(
    "O IPCA é um índice de preços ao consumidor: mede a variação, mês a mês, de um conjunto de "
    "bens e serviços consumidos pelas famílias, conforme metodologia definida pelo IBGE, que o "
    "apura e divulga mensalmente. Os valores são expressos em percentuais de variação; uma taxa "
    "mensal de 0,50% significa que os preços subiram meio ponto percentual em relação ao mês "
    "anterior.", S["corpo"]))
E.append(Paragraph(
    "O Banco Central do Brasil mantém o Sistema Gerenciador de Séries Temporais (SGS), "
    "plataforma que reúne séries econômicas oficiais e as disponibiliza por meio de API "
    "(interface de programação de aplicações) pública. A série 433 corresponde à variação mensal "
    "do IPCA. A consulta foi feita diretamente no endereço oficial da API, no formato JSON.",
    S["corpo"]))
E.append(Paragraph(
    f"<b>Endereço consultado:</b> api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados?formato=json "
    f"— <b>data da consulta:</b> {DATA_CONSULTA_LONGA}. A resposta continha {n_api} registros, de "
    f"01/1980 a 09/2026. Para que o acumulado em 12 meses pudesse ser calculado a partir de "
    f"janeiro de 2021, o recorte utilizado cobre janeiro de 2020 a {ultimo_mes['mes']}, com "
    f"{n_recorte} registros.", S["corpo"]))

E.append(Paragraph("2.1 Validação dos dados", S["h2"]))
linhas_val = [
    [Paragraph("<b>Verificação</b>", S["tab_head"]), Paragraph("<b>Resultado</b>", S["tab_head"])],
    [Paragraph("Registros no recorte (01/2020 a " + ultimo_mes["mes"] + ")", S["tab"]),
     Paragraph(str(n_recorte), S["tab"])],
    [Paragraph("Datas duplicadas", S["tab"]), Paragraph("nenhuma", S["tab"])],
    [Paragraph("Valores ausentes", S["tab"]), Paragraph("nenhum", S["tab"])],
    [Paragraph("Lacunas mensais na sequência", S["tab"]), Paragraph("nenhuma", S["tab"])],
    [Paragraph("Ordenação cronológica", S["tab"]), Paragraph("confirmada", S["tab"])],
    [Paragraph("Último período disponível", S["tab"]), Paragraph(f"{ultimo_mes['mes']} ({br(ultimo_mes['valor'])}%)", S["tab"])],
]
E.append(tabela(linhas_val, [CONTEUDO * 0.6, CONTEUDO * 0.4], alinhamento_centro=True))
E.append(Paragraph(f"Fonte: elaboração própria a partir dos dados da API do BCB/SGS, série 433. "
                   f"Consulta em {DATA_CONSULTA}.", S["fonte"]))

E.append(Paragraph("2.2 Critérios de cálculo", S["h2"]))
for item in [
    f"<b>Acumulado em 12 meses:</b> composição (multiplicação) das 12 taxas mensais, "
    f"[(1+r1) x (1+r2) x ... x (1+r12)] - 1, para cada referência de janeiro de 2021 em diante.",
    "<b>Acumulado por ano-calendário:</b> composição das taxas de janeiro a dezembro. "
    f"Anos completos: 2021, 2022, 2023, 2024 e 2025. Período parcial: 2026 (janeiro a "
    f"{MESES_PT[ultimo_mes['data'].month - 1]}), identificado como tal em todos os gráficos e tabelas.",
    f"<b>Nível de preços do período:</b> composição das {len(mensal)} taxas de janeiro de 2021 a "
    f"{ultimo_mes['mes']}, usada apenas na seção 5, para discutir poder de compra.",
    "<b>Arredondamento:</b> taxas apresentadas com duas casas decimais; os cálculos foram "
    "realizados com o valor completo retornado pela API.",
]:
    E.append(Paragraph("• " + item, S["corpo"]))

E.append(Paragraph(
    "<b>Limitações:</b> o IPCA é um indicador médio — a variação percebida por um domicílio "
    "depende da sua própria cesta de consumo e pode ser diferente da média nacional. A série "
    "utilizada é nacional e refere-se somente a preços: não contém renda, produção ou "
    "expectativas, razão pela qual as comparações com poder de compra na seção 5 são "
    "expressas em termos de nível de preços e não de variação de renda real.", S["corpo"]))

# ============================================================== 3. EVOLUCAO
E.append(Paragraph("3. EVOLUÇÃO DA INFLAÇÃO", S["h1"]))
E.append(HRFlowable(width="100%", thickness=1.2, color=cGOLD, spaceAfter=8))
E.append(caixas_kpi([
    (f"{br(ultimo_mes['valor'])}%", f"IPCA mensal<br/>{ultimo_mes['mes']}"),
    (f"{br(ultimo_ac['valor'])}%", f"Acumulado em 12 meses<br/>{ultimo_ac['mes']}"),
    (f"{br(max_ac['valor'])}%", f"Pico do acumulado<br/>{max_ac['mes']}"),
    (f"{br(media_mensal)}%", f"Média mensal<br/>{primeiro_mes['mes']} a {ultimo_mes['mes']}"),
]))
E.append(Paragraph(f"Fonte: BCB/SGS, série 433. Consulta em {DATA_CONSULTA}. "
                   f"Média calculada sobre {len(mensal)} observações mensais.", S["fonte"]))

E.append(Paragraph(
    f"A Figura 1 mostra a variação mensal do IPCA entre {primeiro_mes['mes']} e "
    f"{ultimo_mes['mes']}. A série oscila com amplitude considerável no primeiro ano e meio e "
    f"torna-se mais estável a partir de 2023. A maior alta do período foi registrada em "
    f"{mes_ano(max_mes['data'])} ({br(max_mes['valor'])}%) e a maior queda, em "
    f"{mes_ano(min_mes['data'])} ({br(min_mes['valor'])}%). A média mensal do período foi de "
    f"{br(media_mensal)}% e {len(negativos)} meses apresentaram taxa negativa: "
    f"{', '.join(r['mes'] for r in negativos[:3])} de 2022, jun/2023 e agosto de 2024, 2025 e "
    f"2026.", S["corpo"]))
E.append(figura("fig1-ipca-mensal.png"))
E.append(Paragraph(f"Figura 1 — IPCA: variação mensal (%) de {primeiro_mes['mes']} a "
                   f"{ultimo_mes['mes']}. Fonte: BCB/SGS, série 433; elaboração própria, "
                   f"consulta em {DATA_CONSULTA}.", S["fonte"]))

E.append(Paragraph(
    f"O acumulado em 12 meses (Figura 2) reúne as taxas dos doze meses anteriores a cada "
    f"referência e é a leitura mais usada para descrever a inflação corrente. O indicador sobe de "
    f"{br(primeiro_ac['valor'])}% em {primeiro_ac['mes']} até {br(max_ac['valor'])}% em "
    f"{max_ac['mes']} — o pico do período — e recua até {br(min_ac['valor'])}% em "
    f"{min_ac['mes']}, o menor nível registrado. Depois disso, oscila em faixa estreita, entre "
    f"{br(ac24_min['valor'])}% ({ac24_min['mes']}) e {br(ac25_max['valor'])}% "
    f"({ac25_max['mes']}), e fecha em {br(ultimo_ac['valor'])}% em {ultimo_ac['mes']}.",
    S["corpo"]))
E.append(figura("fig2-acumulado-12-meses.png"))
E.append(Paragraph(f"Figura 2 — IPCA: acumulado em 12 meses (%) de {primeiro_ac['mes']} a "
                   f"{ultimo_ac['mes']}, calculado por composição das taxas mensais. "
                   f"Fonte: BCB/SGS, série 433; elaboração própria, consulta em {DATA_CONSULTA}.",
                   S["fonte"]))

E.append(Paragraph(
    "A comparação anual (Figura 3 e Tabela 1) separa os anos completos do período parcial de 2026. "
    f"O ano de 2021 registrou {br(a2021['valor'])}%, valor claramente acima dos demais; de 2023 em "
    f"diante, as taxas anuais situam-se em faixa estreita, entre {br(a2025['valor'])}% e "
    f"{br(a2024['valor'])}%. O ano de 2026, parcial, acumula {br(a2026['valor'])}% entre janeiro e "
    f"{MESES_PT[ultimo_mes['data'].month - 1]}.", S["corpo"]))

linhas_anual = [[Paragraph("<b>Ano</b>", S["tab_head"]),
                 Paragraph("<b>Período de referência</b>", S["tab_head"]),
                 Paragraph("<b>IPCA acumulado (%)</b>", S["tab_head"]),
                 Paragraph("<b>Observação</b>", S["tab_head"])]]
for a in anuais:
    if a["ano"] < 2021:
        continue
    obs = "ano completo" if a["completo"] else f"período parcial ({a['n']} meses)"
    linhas_anual.append([
        Paragraph(str(a["ano"]), S["tab"]),
        Paragraph(a["periodo"], S["tab"]),
        Paragraph(f"<b>{br(a['valor'])}</b>", S["tab"]),
        Paragraph(obs, S["tab"]),
    ])
E.append(tabela(linhas_anual, [CONTEUDO * 0.12, CONTEUDO * 0.32,
                               CONTEUDO * 0.26, CONTEUDO * 0.30]))
E.append(Paragraph(f"Tabela 1 — IPCA acumulado por ano-calendário (%). Fonte: BCB/SGS, série 433; "
                   f"elaboração própria, consulta em {DATA_CONSULTA}. 2026 é período parcial e não "
                   f"deve ser comparado diretamente aos anos completos.", S["fonte"]))

E.append(figura("fig3-comparacao-anual.png"))
E.append(Paragraph(f"Figura 3 — IPCA acumulado por ano-calendário (%), 2021 a 2026. "
                   f"Azul-marinho: anos completos; azul-claro com contorno dourado: período "
                   f"parcial. Fonte: BCB/SGS, série 433; elaboração própria, consulta em "
                   f"{DATA_CONSULTA}.", S["fonte"]))

# ============================================================== 4. ANALISE
E.append(Paragraph("4. ANÁLISE DOS RESULTADOS", S["h1"]))
E.append(HRFlowable(width="100%", thickness=1.2, color=cGOLD, spaceAfter=8))
E.append(Paragraph(
    f"A leitura combinada das três figuras permite identificar cinco momentos. "
    f"<b>Primeiro, a aceleração de 2021:</b> o acumulado em 12 meses parte de "
    f"{br(primeiro_ac['valor'])}% em {primeiro_ac['mes']} e alcança {br(ac_de('12/2021'))}% em "
    f"dezembro, fechando o ano em {br(a2021['valor'])}%, o mais alto do período. "
    f"<b>Segundo, o pico e a desaceleração de 2022:</b> a variação mensal de "
    f"{br(max_mes['valor'])}% em {max_mes['mes']} empurra o acumulado ao recorde de "
    f"{br(max_ac['valor'])}% em {max_ac['mes']}; em seguida, três meses de queda de preços "
    f"(jul, ago e set de 2022) reduzem o indicador, que encerra o ano em {br(a2022['valor'])}%, "
    f"uma queda de {br(d_21_22)} pontos percentuais em relação a 2021.", S["corpo"]))
E.append(Paragraph(
    f"<b>Terceiro, a estabilidade de 2023 e 2024:</b> as taxas anuais ficam em "
    f"{br(a2023['valor'])}% e {br(a2024['valor'])}%, variação de {br(d_23_24)} ponto percentual "
    f"entre os dois anos, com o acumulado em 12 meses atingindo seu menor nível do período em "
    f"{ac23_min['mes']} ({br(ac23_min['valor'])}%) e oscilando depois entre "
    f"{br(ac24_min['valor'])}% ({ac24_min['mes']}) e {br(ac24_max['valor'])}% "
    f"({ac24_max['mes']}). <b>Quarto, a reação moderada de 2025:</b> o acumulado sobe de "
    f"{br(ac_de('01/2025'))}% em janeiro a {br(ac25_max['valor'])}% em {ac25_max['mes']} e volta a "
    f"recuar, encerrando o ano em {br(a2025['valor'])}%, {br(abs(d_24_25))} ponto percentual "
    f"abaixo de 2024. <b>Quinto, o ano parcial de 2026:</b> entre janeiro e "
    f"{MESES_PT[ultimo_mes['data'].month - 1]} o acumulado variou entre {br(ac26_min['valor'])}% "
    f"({ac26_min['mes']}) e {br(ac26_max['valor'])}% ({ac26_max['mes']}), com uma queda mensal em "
    f"{[r for r in negativos if r['data'].year == 2026][0]['mes']} e o último dado em "
    f"{br(ultimo_mes['valor'])}% em {ultimo_mes['mes']}, o que deixa o acumulado em "
    f"{br(ultimo_ac['valor'])}%.", S["corpo"]))
E.append(Paragraph(
    f"<b>Comparação entre períodos.</b> A diferença entre o pico ({br(max_ac['valor'])}% em "
    f"{max_ac['mes']}) e o menor acumulado ({br(min_ac['valor'])}% em {min_ac['mes']}) é de "
    f"{br(d_pico_valle)} pontos percentuais. O ano completo mais inflacionário (2021, "
    f"{br(a2021['valor'])}%) supera o menos inflacionário (2025, {br(a2025['valor'])}%) em "
    f"{br(d_21_25)} pontos percentuais. Os três últimos anos completos concentram-se em menos de "
    f"um ponto percentual de amplitude ({br(a2023['valor'])}%, {br(a2024['valor'])}% e "
    f"{br(a2025['valor'])}%), quadro de relativa estabilidade após o episódio de 2021-2022.",
    S["corpo"]))

linhas_ext = [
    [Paragraph("<b>Indicador</b>", S["tab_head"]), Paragraph("<b>Maior valor</b>", S["tab_head"]),
     Paragraph("<b>Menor valor</b>", S["tab_head"]),
     Paragraph(f"<b>Último ({ultimo_mes['mes']})</b>", S["tab_head"])],
    [Paragraph("Variação mensal (%)", S["tab"]),
     Paragraph(f"{br(max_mes['valor'])} ({max_mes['mes']})", S["tab"]),
     Paragraph(f"{br(min_mes['valor'])} ({min_mes['mes']})", S["tab"]),
     Paragraph(br(ultimo_mes["valor"]), S["tab"])],
    [Paragraph("Acumulado em 12 meses (%)", S["tab"]),
     Paragraph(f"{br(max_ac['valor'])} ({max_ac['mes']})", S["tab"]),
     Paragraph(f"{br(min_ac['valor'])} ({min_ac['mes']})", S["tab"]),
     Paragraph(br(ultimo_ac["valor"]), S["tab"])],
    [Paragraph("Ano-calendário (%)", S["tab"]),
     Paragraph(f"{br(a2021['valor'])} (2021)", S["tab"]),
     Paragraph(f"{br(a2025['valor'])} (2025)", S["tab"]),
     Paragraph(f"{br(a2026['valor'])} (jan–{ultimo_mes['mes']})", S["tab"])],
]
E.append(tabela(linhas_ext, [CONTEUDO * 0.31, CONTEUDO * 0.24,
                             CONTEUDO * 0.24, CONTEUDO * 0.21]))
E.append(Paragraph(f"Tabela 2 — Extremos da série no período. Fonte: BCB/SGS, série 433; "
                   f"elaboração própria, consulta em {DATA_CONSULTA}. No ano-calendário, o valor "
                   f"de 2026 refere-se ao período parcial janeiro a {MESES_PT[ultimo_mes['data'].month - 1]}.",
                   S["fonte"]))

E.append(Paragraph(
    "<b>Nota de interpretação.</b> As figuras e a tabela descrevem a trajetória dos preços e "
    "permitem comparar períodos. Elas não demonstram, por si só, as causas das variações: "
    "fatores como política monetária, câmbio, tributos e choques de oferta podem estar associados "
    "ao comportamento observado, mas a identificação de cada efeito exigiria análise específica, "
    "com outras séries e métodos. O que os dados sustentam é a comparação de magnitudes e "
    "direções ao longo do período.", S["corpo"]))

# ============================================================== 5. ADMINISTRACAO
E.append(Paragraph("5. IMPACTOS NA ADMINISTRAÇÃO", S["h1"]))
E.append(HRFlowable(width="100%", thickness=1.2, color=cGOLD, spaceAfter=8))
E.append(Paragraph(
    f"<b>Poder de compra dos consumidores.</b> Compondo as {len(mensal)} taxas mensais de janeiro "
    f"de 2021 a {ultimo_mes['mes']}, o nível de preços acumulou alta de "
    f"{br(acum_periodo)}% no período. Em termos práticos, R$ 100,00 de janeiro de 2021 "
    f"correspondem, pelo nível de preços de {ultimo_mes['mes']}, a R$ {br(fator_periodo * 100)}; "
    f"por outro lado, R$ 100,00 de {ultimo_mes['mes']} têm poder de compra equivalente a "
    f"R$ {br(poder_compra)} de janeiro de 2021. A perda de poder de compra real, porém, depende "
    f"de a renda ter acompanhado ou não essa variação — e a série consultada não contém dados de "
    f"renda, o que limita a conclusão ao efeito sobre preços.", S["corpo"]))
E.append(Paragraph(
    f"<b>Aumento dos custos empresariais.</b> A variação de preços atinge insumos, energia, "
    f"transporte, contratos de fornecimento e a folha de pagamento. Quando o acumulado em 12 meses "
    f"se mantém em torno de {br(ultimo_ac['valor'])}%, como em {ultimo_mes['mes']}, o custo "
    f"repete-se ano após ano e tende a ser incorporado permanentemente à estrutura de custos, e não "
    f"como evento pontual.", S["corpo"]))
E.append(Paragraph(
    "<b>Formação e reajuste de preços.</b> Empresas com margem fixa em valor nominal veem essa "
    f"margem erodir-se quando seus custos sobem mais rápido que os preços praticados. A leitura do "
    f"acumulado em 12 meses orienta a periodicidade da revisão de tabela e o dimensionamento do "
    f"reajuste; já a variação mensal sinaliza momentos de pressão mais imediata, como os meses de "
    f"alta destacados na Figura 1 ({max_mes['mes']}, com {br(max_mes['valor'])}%).",
    S["corpo"]))
E.append(Paragraph(
    f"<b>Planejamento financeiro e orçamentário.</b> Orçamentos, fluxos de caixa e projetos de "
    f"investimento exigem premissa de inflação declarada. Com o acumulado em {ultimo_mes['mes']} em "
    f"{br(ultimo_ac['valor'])}% e a média mensal do período em {br(media_mensal)}%, uma premissa "
    f"baseada no último dado disponível é mais defensável do que a simples repetição de "
    f"reajustes passados. A amplitude observada entre {br(min_ac['valor'])}% e "
    f"{br(max_ac['valor'])}% no período mostra que cenários distintos são necessários: a "
    f"experiência de 2022 não deve ser tratada como referência única nem como impossível de "
    f"repetir.", S["corpo"]))
E.append(Paragraph(
    "<b>Tomada de decisões administrativas.</b> O indicador macro entra como variável de cenário, "
    "não como determinante único. Decisões de contratação, expansão, política de preços e "
    "negociação coletiva devem combinar a leitura da inflação com informações de demanda, "
    "capacidade produtiva e concorrência. Também é papel da Administração registrar a fonte e a "
    "data de cada premissa, de modo que o resultado do planejamento possa ser revisado quando "
    "novo dado oficial for publicado.", S["corpo"]))

# ============================================================== 6. CONSIDERACOES
E.append(Paragraph("6. CONSIDERAÇÕES FINAIS", S["h1"]))
E.append(HRFlowable(width="100%", thickness=1.2, color=cGOLD, spaceAfter=8))
E.append(Paragraph(
    f"A análise da série 433 do SGS, de {primeiro_mes['mes']} a {ultimo_mes['mes']}, mostra três "
    f"resultados principais. Primeiro, o período concentra um ciclo inflacionário completo: alta de "
    f"{br(primeiro_ac['valor'])}% para {br(max_ac['valor'])}% entre janeiro de 2021 e abril de "
    f"2022, seguida de desaceleração até {br(min_ac['valor'])}% em junho de 2023. Segundo, a partir "
    f"de 2023 a inflação estabiliza-se em faixa estreita, com anos completos entre "
    f"{br(a2025['valor'])}% e {br(a2024['valor'])}% e acumulado atual de {br(ultimo_ac['valor'])}% "
    f"em {ultimo_mes['mes']}. Terceiro, no conjunto do período os preços acumularam "
    f"{br(acum_periodo)}%, o que reduz o poder de compra de quem não teve renda corrigida na "
    f"mesma proporção.", S["corpo"]))
E.append(Paragraph(
    "Para a Administração, o acompanhamento mensal desses indicadores tem função prática: "
    "alimenta premissas de orçamento, orienta revisões de preço e de contrato, permite dimensionar "
    "reajustes e evita que decisões sejam tomadas com base em percepção pessoal de inflação em "
    "lugar do dado oficial. Publicar a fonte, a data da consulta e o período de referência — como "
    "feito neste relatório — torna o planejamento auditável e facilita sua correção quando novos "
    "dados são divulgados.", S["corpo"]))
E.append(Paragraph(
    f"Como limitação, registra-se que a série utilizada é exclusivamente de preços: não mede "
    f"renda, produção, emprego ou expectativas, de modo que as relações aqui apontadas com poder "
    f"de compra e custos são de natureza contábil e organizacional, e não de causalidade "
    f"econômica demonstrada. A comparação de 2026 deve ainda ser lida como parcial "
    f"(janeiro a {MESES_PT[ultimo_mes['data'].month - 1]}) e não como ano fechado.", S["corpo"]))

# ============================================================== REFERENCIAS
E.append(Paragraph("REFERÊNCIAS", S["h1"]))
E.append(HRFlowable(width="100%", thickness=1.2, color=cGOLD, spaceAfter=8))
refs = [
    "BANCO CENTRAL DO BRASIL. SGS — Sistema Gerenciador de Séries Temporais, série 433 "
    "(IPCA — variação mensal). API: api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados?formato=json. "
    f"Acesso em: {DATA_CONSULTA}.",
    "BANCO CENTRAL DO BRASIL. Dados Abertos — interface BCData/SGS. "
    "dadosabertos.bcb.gov.br. Acesso em: " + DATA_CONSULTA + ".",
    "BANCO CENTRAL DO BRASIL. Consulta de valores das séries do SGS, série 433. "
    "www3.bcb.gov.br/sgspub. Acesso em: " + DATA_CONSULTA + ".",
    "IBGE. IPCA — Índice Nacional de Preços ao Consumidor Amplo. "
    "www.ibge.gov.br/estatisticas/economicas/precos-e-custos/"
    "9256-indice-nacional-de-precos-ao-consumidor-amplo.html. Acesso em: " + DATA_CONSULTA + ".",
    "IBGE. Inflação (explicativo). www.ibge.gov.br/explica/inflacao.php. Acesso em: "
    + DATA_CONSULTA + ".",
    "IBGE. Métodos de cálculo do Sistema de Índices de Preços ao Consumidor. "
    "ftp.ibge.gov.br/Precos_Indices_de_Precos_ao_Consumidor. Acesso em: " + DATA_CONSULTA + ".",
]
for i, r in enumerate(refs, 1):
    E.append(Paragraph(f"{i}. {r}", S["ref"]))

E.append(Spacer(1, 0.4 * cm))
E.append(HRFlowable(width="100%", thickness=0.8, color=cGOLD, spaceAfter=6))
E.append(Paragraph(
    "<b>Decisões pendentes para fechamento humano:</b> inserir identificação do autor (nome, "
    "matrícula e disciplina) na capa; conferir os valores contra a série oficial antes da "
    "submissão; e ajustar o recorte caso a API publique mês mais recente que "
    f"{ultimo_mes['mes']}.", S["nota"]))

# ============================================================== APENDICE
E.append(PageBreak())
E.append(Paragraph("APÊNDICE A — SÉRIE MENSAL UTILIZADA", S["h1"]))
E.append(HRFlowable(width="100%", thickness=1.2, color=cGOLD, spaceAfter=8))
E.append(Paragraph(
    f"Tabela A1 — Valores de origem de janeiro de 2021 a {ultimo_mes['mes']}, em ordem "
    f"cronológica, em percentual. Colunas “IPCA mensal”: variação do mês de referência. "
    f"Colunas “Ac. 12 meses”: acumulado por composição das doze taxas anteriores ao mês "
    f"indicado. Fonte: BCB/SGS, série 433; consulta em {DATA_CONSULTA}; elaboração própria.",
    S["fonte"]))

metade = (len(mensal) + 1) // 2
cab = ["Mês", "IPCA mensal", "Ac. 12 meses"] * 2
linhas_apx = [[Paragraph(f"<b>{c}</b>", S["tab_head"]) for c in cab]]
for i in range(metade):
    e = mensal[i], ac12[i]
    d = (mensal[i + metade], ac12[i + metade]) if i + metade < len(mensal) else None
    linha = [Paragraph(e[0]["mes"], S["tab_p"]),
             Paragraph(br(e[0]["valor"]), S["tab_p"]),
             Paragraph(br(e[1]["valor"]), S["tab_p"])]
    if d:
        linha += [Paragraph(d[0]["mes"], S["tab_p"]),
                  Paragraph(br(d[0]["valor"]), S["tab_p"]),
                  Paragraph(br(d[1]["valor"]), S["tab_p"])]
    else:
        linha += [Paragraph("", S["tab_p"]), Paragraph("", S["tab_p"]),
                  Paragraph("", S["tab_p"])]
    linhas_apx.append(linha)

larg_apx = [CONTEUDO * 0.165, CONTEUDO * 0.155, CONTEUDO * 0.18] * 2
t_apx = Table(linhas_apx, colWidths=larg_apx, repeatRows=1)
t_apx.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), cNAVY),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ("TOPPADDING", (0, 0), (-1, -1), 2.2),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2),
    ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ("LINEABOVE", (0, 0), (-1, 0), 1.5, cGOLD),
    ("LINEAFTER", (2, 0), (2, -1), 1.0, cGOLD),
    ("LINEBELOW", (0, -1), (-1, -1), 0.8, cNAVY),
    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D7DEE9")),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, cALT]),
]))
if len(mensal) % 2 == 1:
    ultima_linha = metade
    t_apx.setStyle(TableStyle([("SPAN", (3, ultima_linha), (5, ultima_linha)),
                               ("BACKGROUND", (3, ultima_linha), (5, ultima_linha),
                                colors.white)]))
E.append(t_apx)

doc.build(E, canvasmaker=CanvasNumerado)
print(f"PDF gerado: {SAIDA}")

