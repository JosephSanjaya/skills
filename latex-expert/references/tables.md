# Tables

<rules>
- No vertical rules. No double rules. No `|c|c|` cages.
- `\toprule` / `\midrule` / `\bottomrule`. Grouped heads: `\cmidrule(lr)`.
- Numbers: `siunitx` `S`. Wrap non-numeric heads in `{...}`.
- Caption: tables above, figures below. Alcazar: keep sf/small/bf/endash captions.
- Eisvogel: MD pipe tables → booktabs. Dense Alcazar BOM grid: rewrite only if asked.
</rules>

<code>
```latex
\usepackage{booktabs,siunitx}
\begin{table}[htbp]
  \centering
  \caption{Measured throughput.}
  \label{tab:throughput}
  \begin{tabular}{l S[table-format=2.1] S[table-format=1.3]}
    \toprule
    Device & {Rate / MHz} & {Error} \\
    \midrule
    A & 12.0 & 0.013 \\
    B &  8.5 & 0.102 \\
    \bottomrule
  \end{tabular}
\end{table}
```
</code>

<constraints>
#must booktabs on new tables even inside Alcazar. #never vertical rules. #never \hline\hline.
</constraints>
