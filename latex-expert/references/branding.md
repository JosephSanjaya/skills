# Branding

<rules>
- Named tokens. RGB screen, CMYK print. Tints for rules/boxes, not page washes.
- Alcazar: extend `style/colors.sty` — no second palette.
- Logos: PDF/EPS only. PNG = photos. Header: `parbox`/`minipage` for baseline.
- Eisvogel `titlepage-logo`: path relative to cwd (`--resource-path` ignored).
- Diagrams: TikZ (match text fonts/weights). Prefer PDF export over screenshot PNG.
</rules>

<code>
```latex
\usepackage[dvipsnames]{xcolor}
\definecolor{Brand}{RGB}{0, 51, 102}
\colorlet{LightBrand}{Brand!20}
\includegraphics[height=12mm]{logo.pdf}
```
</code>

<constraints>
#must named colors. #must vector logos. #never raster logos.
</constraints>
