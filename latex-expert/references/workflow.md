# Workflow

<rules>
- `!latexmk` owns pass count (LaTeX/Biber/makeindex).
- Alcazar: `-shell-escape` (`minted`). Awesome-CV: `!xelatex`. Eisvogel: `pandoc` or `pandoc/extra` Docker.
- Lint: ChkTeX. Prose: TeXtidote. Fix overfull `\hbox`; don't silence in official PDFs.
- Local+Git: VS Code LaTeX Workshop. Multi-author: Overleaf.
</rules>

<code>
```bash
!latexmk -shell-escape -synctex=1 -interaction=nonstopmode -file-line-error -pdf main
!latexmk -lualatex -synctex=1 -interaction=nonstopmode -file-line-error main.tex
!xelatex cv.tex
pandoc document.md -o document.pdf --from markdown --template eisvogel --syntax-highlighting idiomatic
```
</code>

<constraints>
#must latexmk (or template `make`). #must -shell-escape on Alcazar.
</constraints>
