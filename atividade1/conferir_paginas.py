# -*- coding: utf-8 -*-
"""Lista o primeiro trecho de texto de cada pagina do PDF, para conferencia."""
from pathlib import Path
import pymupdf

BASE = Path(__file__).resolve().parent.parent
PDF = BASE / "entregas" / "analise-inflacao-poder-compra-2021-2026.pdf"

doc = pymupdf.open(PDF)
print("total de paginas:", doc.page_count)
for i, page in enumerate(doc, 1):
    texto = " ".join(page.get_text().split())
    rodape = ""
    for bloco in page.get_text("dict")["blocks"]:
        for linha in bloco.get("lines", []):
            for span in linha["spans"]:
                if "Página" in span["text"]:
                    rodape = span["text"]
    print(f"\n--- pág. {i} [{rodape}] ---")
    print(texto[:260])
