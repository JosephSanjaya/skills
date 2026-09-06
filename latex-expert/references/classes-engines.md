# Classes and engines

<rules>
- Default official: KOMA `scr*`. Publisher class if mandated. `memoir` = one-class kitchen sink.
- New work: LuaLaTeX. System/OTF-only (Awesome-CV): XeLaTeX. Frozen (Alcazar, many journals): pdfLaTeX.
- Xe/Lua: no `inputenc`/`fontenc`. pdfLaTeX: no `fontspec`.
</rules>

| Class | Unit | Paging | Front/back | Use |
|---|---|---|---|---|
| `article` | section | 1-side | no | Short paper, publisher requires it |
| `report` | chapter | 1-side def. | no | Alcazar. Prefer KOMA for new |
| `book` | chapter | 2-side | yes | Books |
| `memoir` | flexible | 2-side | yes | Total control |
| `scrartcl`/`scrreprt`/`scrbook` | sec/ch | KOMA | yes on book | **Default official** |
| `scrlttr2` | letter vars | — | — | DIN letters |
| `IEEEtran` | section | pub | — | IEEE only |
| `elsarticle` | section | pub | heavy FM | Elsevier only |
| `awesome-cv` | article | 1-side | — | CV/résumé/letter |

| | pdfLaTeX | XeLaTeX | LuaLaTeX |
|---|---|---|---|
| Fonts | Type1/8-bit | OTF/TTF `fontspec` | OTF/TTF `fontspec` |
| Unicode | `inputenc` | native | native |
| `microtype` | full | partial | full |
| Speed | fast | med | slow |
| When | Alcazar, journals | Awesome-CV, branded OTF | **new official** |

<code>
```latex
\documentclass[11pt,a4paper,twoside]{scrreprt}
```
</code>

<constraints>
#must KOMA unless publisher class. #must LuaLaTeX on greenfield. #never fontspec+pdfLaTeX. #never inputenc on Xe/Lua.
</constraints>
