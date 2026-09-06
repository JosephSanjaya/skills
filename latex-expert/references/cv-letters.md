# CVs and letters

<rules>
- CV: importance order, reverse-chronology, one indent scheme. Contact compact (header/footer). Bold/italic own name in pubs. ~1.2 in margins unless Awesome-CV geometry.
- Awesome-CV: XeLaTeX+`fontspec` (Source Sans 3, Roboto). Edit `examples/`. Don't fork `.cls` for content. No `inputenc`/`fontenc`/pdfLaTeX.
- Letters: `scrlttr2` vars (DIN 5008, fold marks, subject, ref, enclosures). Signature via `\closing`.
</rules>

<code>
```latex
\documentclass[11pt,a4paper]{awesome-cv}
```

```bash
!xelatex cv.tex
```

```latex
\documentclass[foldmarks=true,fromalign=right,fromphone,fromemail]{scrlttr2}
\setkomavar{fromname}{...}
\setkomavar{fromaddress}{...}
\setkomavar{subject}{...}
\begin{letter}{Recipient\\Address}
\opening{Dear ...}
\closing{Yours sincerely,}
\end{letter}
```
</code>

<constraints>
#must XeLaTeX for Awesome-CV. #never fontenc on CV class. #must reverse-chronology.
</constraints>
