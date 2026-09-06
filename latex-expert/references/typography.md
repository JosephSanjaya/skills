# Typography

<rules>
- Computer Modern = student draft outside math papers. Pair body + math.
- 70–90 chars/line.
- KOMA/Eisvogel headers: `scrlayer-scrpage`. `report`/`article` (Alcazar, Awesome-CV): keep `fancyhdr`.
- 2-side: page # outer; header = short title + section.
- `microtype` full on pdf/Lua; Xe partial. Alcazar missing it → add. Awesome-CV: no `fontenc`.
</rules>

| Role | Faces | Note |
|---|---|---|
| Body | Libertinus, LM Roman, TeX Gyre Pagella, Charter, EB Garamond, Source Serif | Alcazar: Libertinus+`newtxmath` |
| Sans | Libertinus Sans, Source Sans, TeX Gyre Heros | scale ~0.95 |
| Mono | IBM Plex Mono, Inconsolata, Source Code Pro, Fira Mono | scale ~0.85 w/ Libertinus |
| Math | `newtxmath` / `unicode-math` | match body weight |

| Doc | Margin |
|---|---|
| Letter | 1.0 in |
| Report | 1.1 in |
| Academic CV | 1.2 in |
| Journal | publisher / ~1.0 in |
| Eisvogel | keep `2.5cm`+head/foot unless asked |

<code>
```latex
% pdfLaTeX
\usepackage{libertinus}
\usepackage[libertine]{newtxmath}
\usepackage[scale=0.85]{plex-mono}
\usepackage[T1]{fontenc}

% Xe/Lua
\usepackage{fontspec,unicode-math}
\setmainfont{Libertinus Serif}
\setsansfont{Libertinus Sans}
\setmonofont{IBM Plex Mono}[Scale=0.85]
\setmathfont{Libertinus Math}

\usepackage[activate={true,nocompatibility},final,tracking=true,kerning=true,spacing=true]{microtype}
\usepackage[a4paper,margin=1.1in]{geometry}
```
</code>

<constraints>
#never fancyhdr on KOMA. #never fontenc on Awesome-CV. #must matching math face.
</constraints>
