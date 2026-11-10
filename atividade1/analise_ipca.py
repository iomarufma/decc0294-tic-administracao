# -*- coding: utf-8 -*-
"""Valida os dados brutos do IPCA (BCB/SGS serie 433) e calcula indicadores."""
import json
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
ARQ = BASE / "dados" / "ipca-433-bruto.json"

with open(ARQ, encoding="utf-8") as f:
    pacote = json.load(f)

bruto = pacote["dados"]
consulta = pacote["consulta_utc"]

# --- validacao ---
datas = [d["data"] for d in bruto]
duplicados = sorted({d for d in datas if datas.count(d) > 1})
valores_ausentes = [d for d in bruto if d.get("valor") in (None, "", "-")]
datas_ordenadas = all(
    datetime.strptime(datas[i], "%d/%m/%Y") <= datetime.strptime(datas[i + 1], "%d/%m/%Y")
    for i in range(len(datas) - 1)
)

registros = []
for d in bruto:
    data = datetime.strptime(d["data"], "%d/%m/%Y")
    registros.append({"data": data, "mes": data.strftime("%m/%Y"), "valor": float(d["valor"])})

# checagem de lacunas mensais a partir de 01/2020
registros = sorted([r for r in registros if r["data"] >= datetime(2020, 1, 1)], key=lambda r: r["data"])
lacunas = []
prev = None
for r in registros:
    if prev is not None:
        esperado = (prev.year + (prev.month == 12), prev.month % 12 + 1)
        obtido = (r["data"].year, r["data"].month)
        if obtido != esperado:
            lacunas.append(f"{prev:%m/%Y} -> {r['mes']}")
    prev = r["data"]

ultimo = registros[-1]
primeiro = registros[0]

# --- acumulado em 12 meses por composicao ---
ac12 = []
for i, r in enumerate(registros):
    if i >= 11:
        janela = registros[i - 11: i + 1]
        fator = 1.0
        for x in janela:
            fator *= (1 + x["valor"] / 100)
        ac12.append({"data": r["data"], "mes": r["mes"], "valor": (fator - 1) * 100})

# --- acumulados anuais (composicao das taxas do ano) ---
anos = {}
for r in registros:
    anos.setdefault(r["data"].year, []).append(r)

resumo_anual = []
for ano in sorted(anos):
    meses = anos[ano]
    fator = 1.0
    for x in meses:
        fator *= (1 + x["valor"] / 100)
    resumo_anual.append({
        "ano": ano,
        "valor": (fator - 1) * 100,
        "n_meses": len(meses),
        "completo": len(meses) == 12 and meses[-1]["data"].month == 12,
        "periodo": f"{meses[0]['mes']} a {meses[-1]['mes']}",
    })

# --- extremos no periodo da analise (a partir de 01/2021) ---
analise_mes = [r for r in registros if r["data"] >= datetime(2021, 1, 1)]
analise_ac12 = [r for r in ac12 if r["data"] >= datetime(2021, 1, 1)]

max_mes = max(analise_mes, key=lambda r: r["valor"])
min_mes = min(analise_mes, key=lambda r: r["valor"])
max_ac = max(analise_ac12, key=lambda r: r["valor"])
min_ac = min(analise_ac12, key=lambda r: r["valor"])

# media mensal do periodo
media_mes = sum(r["valor"] for r in analise_mes) / len(analise_mes)

# --- saida ---
saida = {
    "consulta_utc": consulta,
    "total_registros_api": len(bruto),
    "primeiro_periodo_analise": primeiro["mes"],
    "ultimo_periodo": ultimo["mes"],
    "ultimo_valor": ultimo["valor"],
    "duplicados": duplicados,
    "valores_ausentes": valores_ausentes,
    "ordenado": datas_ordenadas,
    "lacunas": lacunas,
    "n_meses_analise": len(analise_mes),
    "media_mensal": media_mes,
    "max_mes": {"mes": max_mes["mes"], "valor": max_mes["valor"]},
    "min_mes": {"mes": min_mes["mes"], "valor": min_mes["valor"]},
    "max_ac12": {"mes": max_ac["mes"], "valor": max_ac["valor"]},
    "min_ac12": {"mes": min_ac["mes"], "valor": min_ac["valor"]},
    "anual": resumo_anual,
    "serie_mensal": [{"mes": r["mes"], "valor": r["valor"]} for r in analise_mes],
    "serie_ac12": [{"mes": r["mes"], "valor": r["valor"]} for r in analise_ac12],
}

with open(BASE / "dados" / "ipca-indicadores.json", "w", encoding="utf-8") as f:
    json.dump(saida, f, ensure_ascii=False, indent=2)

print(f"Consulta: {consulta}")
print(f"API: {len(bruto)} registros, do {datas[0]} ao {datas[-1]}")
print(f"Analise: {primeiro['mes']} a {ultimo['mes']} ({len(analise_mes)} meses)")
print(f"Duplicados: {duplicados or 'nenhum'} | Ausentes: {valores_ausentes or 'nenhum'} | Ordenado: {datas_ordenadas} | Lacunas: {lacunas or 'nenhuma'}")
print(f"Ultimo valor mensal: {ultimo['valor']:.2f}%")
print(f"Media mensal do periodo: {media_mes:.2f}%")
print(f"Maior mes: {max_mes['mes']} ({max_mes['valor']:.2f}%) | Menor mes: {min_mes['mes']} ({min_mes['valor']:.2f}%)")
print(f"Maior ac12: {max_ac['mes']} ({max_ac['valor']:.2f}%) | Menor ac12: {min_ac['mes']} ({min_ac['valor']:.2f}%)")
print("--- Anuais ---")
for a in resumo_anual:
    tipo = "completo" if a["completo"] else "PARCIAL"
    print(f"{a['ano']}: {a['valor']:.2f}% ({a['periodo']}, {a['n_meses']} meses, {tipo})")
print("--- Ac12 pontos ---")
for r in analise_ac12:
    print(f"{r['mes']}: {r['valor']:.2f}")
