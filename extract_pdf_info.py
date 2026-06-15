# -*- coding: utf-8 -*-
import fitz
from pathlib import Path

src = Path(r"F:\2026spring2\出图\html制作\源文件")
out = Path(r"F:\2026spring2\出图\html制作\pdf_info.txt")

lines = []
for i in range(58, 86):
    p = src / f"{i}.pdf"
    if not p.exists():
        lines.append(f"{i}: MISSING")
        continue
    doc = fitz.open(p)
    text = "".join(page.get_text() for page in doc)
    n_pages = len(doc)
    doc.close()
    lines.append(f"=== {i}.pdf | pages={n_pages} | size={p.stat().st_size} ===")
    lines.append(text[:1200].strip() or "(no text)")
    lines.append("")

out.write_text("\n".join(lines), encoding="utf-8")
print(f"written {out}")
