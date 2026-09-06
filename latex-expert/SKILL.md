---
name: latex-expert
description: "Professional LaTeX for official documents: class and engine choice, fonts, microtype, booktabs tables, biblatex/biber, KOMA letters, academic CVs, Eisvogel/pandoc PDFs, IEEE/Elsevier/Springer submission. Use whenever the user writes, reviews, or compiles .tex/.sty/.cls, mentions XeLaTeX/LuaLaTeX/latexmk, wants a thesis, CV, report, letter, or journal PDF, or asks to make a document look official — even if they only paste a preamble or a Markdown file."
---

# LaTeX Expert

<instructions>
Official look = rules, not decoration. Load **one** ref. Templates have gaps → [templates.md](references/templates.md).
</instructions>

<stack>

| Doc | Class | Engine | Ref |
|---|---|---|---|
| Article | `scrartcl` (`article` if publisher forbids KOMA) | LuaLaTeX | [classes-engines.md](references/classes-engines.md) |
| Thesis/report | Alcazar **or** `scrreprt`/`scrbook`/`memoir` | Alcazar: pdfLaTeX+`latexmk`. New: LuaLaTeX | [templates.md](references/templates.md) |
| CV | Awesome-CV | XeLaTeX | [cv-letters.md](references/cv-letters.md) |
| Letter | `scrlttr2` | Lua/Xe | [cv-letters.md](references/cv-letters.md) |
| MD→PDF | Eisvogel | `pandoc` | [templates.md](references/templates.md) |
| IEEE/Elsevier/Springer | publisher class | publisher engine | [publishers.md](references/publishers.md) |

fonts/margins/headers/microtype → [typography.md](references/typography.md)  
tables/SI → [tables.md](references/tables.md)  
cites → [bibliography.md](references/bibliography.md)  
color/logo/TikZ → [branding.md](references/branding.md)  
build/lint → [workflow.md](references/workflow.md)

</stack>

<rules>
- Content ≠ presentation. Ban `\vspace`/manual breaks/`minipage` stacks as "official."
- Computer Modern → drafts/math only. Pair text face + matching math.
- New: LuaLaTeX (Unicode + full `microtype`). CV fonts: XeLaTeX. Frozen template/journal: pdfLaTeX.
- Tables: `booktabs`, no vertical rules, no double rules. Numbers: `siunitx` `S`.
- Cite: `biblatex`+Biber. Not BibTeX unless publisher forbids.
- KOMA → `scrlayer-scrpage`, not `fancyhdr`.
- Logos: PDF/EPS. Colors: named `xcolor` (RGB screen, CMYK print).
- Build: `!latexmk`. Flatten `.bbl` + drop subfolders only at upload.
</rules>

<constraints>
- Publisher/institutional class wins.
- Editing Alcazar / Awesome-CV / Eisvogel: keep engine+class; apply doctrine inside that box.
</constraints>
