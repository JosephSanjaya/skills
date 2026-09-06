# Repo templates

Skeletons beside this skill. Keep vs patch vs don't:

| | Alcazar | Awesome-CV | Eisvogel |
|---|---|---|---|
| Job | thesis | CV/résumé/cover | MD→PDF |
| Class | `report` 12pt `twoside,openright` | `awesome-cv` | `scrartcl` (`scrbook` if `book: true`) |
| Engine | pdfLaTeX `!latexmk`/`make` | XeLaTeX | pandoc |
| Keep | latexmk, biblatex+Biber, Libertinus, vars in `main.tex` | Xe+fontspec, Source Sans, semantic markup | KOMA, booktabs, YAML |
| Patch | add `booktabs`+`siunitx`+`microtype` on **new** tables | reverse-chronology, compact contact, name-emphasis in pubs | named colors, vector `titlepage-logo`, Lua engine if full microtype |
| Don't | silent `scrbook`/Lua switch; copy BOM `\|` grid | `fontenc`, CM, pdfLaTeX, fork `.cls` for content | assume `eisvogel.latex` in git (releases only) |

Alcazar needs Biber + Python3 + Pygments. Style: `@alcazar/style/pkgs.sty`, `@alcazar/style/alcazar.sty`.

Eisvogel YAML keys: `titlepage`, `titlepage-logo`, `header-*`, `footer-*`, `watermark`, `toc-own-page`. Source: `template-multi-file/`.

<code>
```yaml
title: "Lecture notes"
author: [Name]
date: "2026-09-06"
titlepage: true
```

```bash
pandoc notes.md -o notes.pdf --template eisvogel --syntax-highlighting idiomatic
```
</code>

<constraints>
#must keep template engine+class. #must booktabs on new Alcazar tables. #never fontenc on Awesome-CV.
</constraints>
