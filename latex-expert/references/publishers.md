# Journal submission

<rules>
- House class wins. Don't restyle fonts/margins/sections on a publisher template.
- Elsevier `elsarticle`: **one folder**. Subdirs break Editorial Manager.
- Springer: no custom fonts. Special chars = TeX commands, not ad-hoc Unicode.
- IEEE `IEEEtran`: ~24 pt title, 10 pt Times, hard page limits. Class drift = amateur.
</rules>

<constraints>
Flatten before upload:
1. `!latexmk` until cites resolve
2. Paste `.bbl` into main `.tex` (drop `\printbibliography` / `\bibliography`)
3. Flatten figure paths → single dir
4. Confirm publisher engine (often pdfLaTeX) still builds
#never KOMA on Elsevier/IEEE. #never extra fonts on Springer. #never subfolders on Elsevier.
</constraints>
