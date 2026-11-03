# -*- coding: utf-8 -*-
"""Renderiza as paginas do PDF para PNG, para conferencia visual."""
from pathlib import Path
import fitz

BASE = Path(__file__).resolve().parent.parent
PDF = BASE / "entregas" / "analise-inflacao-poder-compra-2021-2026.pdf"
SAIDA = Path(r"C:\Users\aluno\AppData\Local\Temp\opencode\previa-inflacao")
SAIDA.mkdir(parents=True, exist_ok=True)

doc = fitz.open(PDF)
print("paginas:", doc.page_count)
for i, page in enumerate(doc, 1):
    pix = page.get_pixmap(dpi=110)
    caminho = SAIDA / f"pagina-{i:02d}.png"
    pix.save(caminho)
    print(caminho)
