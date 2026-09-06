# Bibliography

<rules>
- Default: `biblatex` + Biber. Unicode, ibid, split bibs, LaTeX styles.
- `numeric-comp` → `[1-3]`. Author-year: `authoryear`. Alcazar: keep `ieee`/`ieee-comp`.
- No `natbib`+`biblatex`. No BibTeX on `backend=biber`.
- Build: `!latexmk` ([workflow.md](workflow.md)). Flatten `.bbl` at upload ([publishers.md](publishers.md)).
</rules>

<code>
```latex
\usepackage{csquotes}
\usepackage[style=numeric-comp,backend=biber]{biblatex}
\addbibresource{references.bib}
\printbibliography
```
</code>

<constraints>
#must biber unless publisher forbids. #never mix natbib+biblatex.
</constraints>
