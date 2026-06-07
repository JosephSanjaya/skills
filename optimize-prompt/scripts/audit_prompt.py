#!/usr/bin/env python3
"""
Prompt Audit Tool - Static heuristic analysis and automatic refactoring of LLM and Claude Code prompts.

Performs static analysis to detect:
1. Politeness waste (redundant tokens)
2. Persona role-prompting (placebo effects, bias risk)
3. Prefix caching issues (dynamic placeholders too early)
4. Suffix-loading / Prism Prompting constraints (recency bias utilization)
5. XML-style formatting hierarchy
6. Wall-of-text patterns
7. Claude Code specific issues (vague targets, full implementation requests, missing bounding operators)
8. Inefficient data formats (raw JSON/XML where Markdown/YAML is denser)
9. Overly long prompts requiring compression
"""

import argparse
import re
import sys
from pathlib import Path


class PromptAuditor:
    def __init__(self, content: str, filename: str = "Prompt"):
        self.content = content
        self.filename = filename
        self.lines = content.splitlines()
        self.total_words = len(content.split())
        self.total_chars = len(content)
        # Approximate tokens (simple heuristic: 1 token ~ 4 chars or 0.75 words)
        self.est_tokens = int(max(self.total_chars / 4.0, self.total_words / 0.75))

    def audit(self) -> dict:
        results = {
            "politeness": self._check_politeness(),
            "persona": self._check_persona(),
            "caching": self._check_caching(),
            "prism": self._check_prism(),
            "xml": self._check_xml(),
            "wall_of_text": self._check_wall_of_text(),
            "claude_code": self._check_claude_code(),
            "data_formats": self._check_data_formats(),
            "token_compression": self._check_token_compression(),
            "metrics": {
                "words": self.total_words,
                "chars": self.total_chars,
                "est_tokens": self.est_tokens,
            }
        }
        return results

    def _check_politeness(self) -> dict:
        patterns = [
            (r"\bplease\b", "please"),
            (r"\bthank\s+you\b", "thank you"),
            (r"\bthanks\b", "thanks"),
            (r"\bif\s+you\s+don't\s+mind\b", "if you don't mind"),
            (r"\bappreciate\s+it\b", "appreciate it"),
            (r"\bcould\s+you\b", "could you"),
            (r"\bcan\s+you\b", "can you"),
            (r"\bwould\s+you\b", "would you"),
            (r"\bi\s+(?:need|want)\s+you\s+to\b", "i need/want you to"),
        ]
        found = []
        for pat, name in patterns:
            matches = list(re.finditer(pat, self.content, re.IGNORECASE))
            if matches:
                found.append((name, len(matches)))
        
        passed = len(found) == 0
        details = ""
        if not passed:
            occurrences = ", ".join([f"'{name}' ({count}x)" for name, count in found])
            details = f"Detected polite fillers or indirect requests: {occurrences}. Drop pleasantries and use direct imperatives."
        else:
            details = "No polite fillers or conversational overhead detected."

        return {"passed": passed, "details": details, "score": 100 if passed else 50}

    def _check_persona(self) -> dict:
        patterns = [
            (r"\bact\s+as\s+(?:a|an)\b", "act as a/an"),
            (r"\byou\s+are\s+(?:a|an|the)\s+expert\b", "you are an expert"),
            (r"\byou\s+are\s+(?:a|an|the)\s+(?:senior|genius|ivy\s+league)\b", "high-level persona declaration"),
            (r"\broleplay\s+as\b", "roleplay as"),
        ]
        found = []
        for pat, name in patterns:
            matches = list(re.finditer(pat, self.content, re.IGNORECASE))
            if matches:
                found.append((name, len(matches)))

        passed = len(found) == 0
        details = ""
        if not passed:
            occurrences = ", ".join([f"'{name}' ({count}x)" for name, count in found])
            details = f"Detected role-prompting: {occurrences}. Replace generic psychological personas with structural rules and direct examples."
        else:
            details = "No generic role prompting detected."

        return {"passed": passed, "details": details, "score": 100 if passed else 70}

    def _check_caching(self) -> dict:
        placeholders = re.findall(r"\{[a-zA-Z0-9_-]+\}", self.content)
        if not placeholders:
            return {"passed": True, "details": "No placeholders detected (likely a static prompt).", "score": 100}

        first_half_vars = []
        half_char_idx = self.total_chars // 2
        for match in re.finditer(r"\{([a-zA-Z0-9_-]+)\}", self.content):
            if match.start() < half_char_idx:
                first_half_vars.append(match.group(1))

        passed = len(first_half_vars) == 0
        details = ""
        if not passed:
            details = f"Dynamic placeholders {first_half_vars} found in first 50% of prompt. This invalidates prefix/KV caching for subsequent tokens. Move dynamic variables to the absolute end."
        else:
            details = "All dynamic variables located in the last 50% of the prompt, maximizing prefix caching efficiency."

        return {"passed": passed, "details": details, "score": 100 if passed else 40}

    def _check_prism(self) -> dict:
        last_20_percent = self.content[int(self.total_chars * 0.8):]
        keywords = ["must", "should", "require", "format", "output", "schema", "wrap", "only"]
        found = [kw for kw in keywords if re.search(r"\b" + kw + r"\b", last_20_percent, re.IGNORECASE)]

        passed = len(found) >= 2
        details = ""
        if passed:
            details = f"Constraints are suffix-loaded. Detected instruction anchors ({', '.join(found)}) near the prompt end."
        else:
            details = "No formatting rules or constraint keywords detected in the final 20% of the prompt. Risk of lost-in-the-middle rule evasion."

        return {"passed": passed, "details": details, "score": 100 if passed else 60}

    def _check_xml(self) -> dict:
        xml_tags = re.findall(r"<([a-zA-Z0-9_-]+)(?:\s+[^>]+)?>.*?</\1>", self.content, re.DOTALL)
        passed = len(xml_tags) >= 2
        details = ""
        if passed:
            unique_tags = list(set(xml_tags))
            details = f"Strong semantic layout. Found hierarchical XML tags: {unique_tags}."
        else:
            details = "No structured XML tag pairs detected. Risk of semantic boundary confusion."

        return {"passed": passed, "details": details, "score": 100 if passed else 50}

    def _check_wall_of_text(self) -> dict:
        paragraphs = [p.strip() for p in self.content.split("\n\n") if p.strip()]
        dense_paragraphs = [p for p in paragraphs if len(p.split()) > 150 and not p.startswith(("#", "-", "*", "1.", "<"))]
        
        passed = len(dense_paragraphs) == 0
        details = ""
        if not passed:
            details = f"Found {len(dense_paragraphs)} massive paragraph(s) (>150 words) lacking structure. Break these into lists or use XML structuring."
        else:
            details = "Prompt structure is highly readable and well-delineated."

        return {"passed": passed, "details": details, "score": 100 if passed else 60}

    def _check_claude_code(self) -> dict:
        issues = []
        score_penalty = 0

        # Check for vague target (e.g. "fix the database module") without file:line reference
        if re.search(r"\b(fix|look at|check|help with)\s+the\s+\w+\s+(module|service|component|file)\b", self.content, re.IGNORECASE):
            issues.append("Vague target. Specify file:line using '@file:line' operator.")
            score_penalty += 20

        # Asking for full implementation without Plan Mode
        if re.search(r"\bimplement\s+(the\s+)?(entire|whole|full|complete)\b", self.content, re.IGNORECASE) and not re.search(r"\bplan\s+mode\b", self.content, re.IGNORECASE):
            issues.append("Requesting full implementation directly. Use Plan Mode (Shift+Tab) first, then request step 1.")
            score_penalty += 20

        # Long prompt without files (@) or commands (!)
        if len(self.content) > 400 and not re.search(r"[@!#<]", self.content):
            issues.append("Long instruction prompt with no context-bounding operators (@file or !command).")
            score_penalty += 20

        # Prompt too long without session reset suggestion (>2000 chars)
        if len(self.content) > 2000:
            issues.append("Prompt exceeds 2000 characters. Suggest `/clear` or `/compact` to prevent context decay.")
            score_penalty += 10

        passed = len(issues) == 0
        details = ""
        if not passed:
            details = " | ".join(issues)
        else:
            details = "Passed all Claude Code command and context isolation checks."

        return {"passed": passed, "details": details, "score": max(0, 100 - score_penalty)}

    def _check_data_formats(self) -> dict:
        # Check for raw JSON or XML formatted data blocks in the prompt
        has_json = re.search(r'\{\s*"[a-zA-Z0-9_-]+"\s*:', self.content)
        # Avoid matching system/instruction XML tags (e.g. <instructions>)
        has_xml_data = re.search(r'<([a-zA-Z0-9_-]+)(?:\s+[^>]+)?>[^<]*</\1>', self.content) and not re.search(r'</?(instructions|context|task|goal|constraints|verify|thinking|source_code)>', self.content)
        
        passed = not (has_json or has_xml_data)
        details = ""
        score = 100
        if not passed:
            issues = []
            if has_json:
                issues.append("raw JSON data blocks")
                score -= 20
            if has_xml_data:
                issues.append("verbose XML data nodes")
                score -= 20
            details = f"Detected verbose data structures: {', '.join(issues)}. Use Markdown (up to 38% denser than JSON) or YAML for optimal token savings and reasoning."
        else:
            details = "No verbose raw JSON/XML data formats detected. Optimal data encoding."

        return {"passed": passed, "details": details, "score": max(0, score)}

    def _check_token_compression(self) -> dict:
        passed = self.est_tokens <= 1000
        details = ""
        if not passed:
            details = f"Prompt length (~{self.est_tokens} tokens) is high. Recommend compressing with `scripts/compress_prompt.py` to strip pleasantries/filler words and optimize whitespaces."
        else:
            details = f"Prompt length is optimal (~{self.est_tokens} tokens)."

        return {"passed": passed, "details": details, "score": 100 if passed else 70}

    def generate_report(self) -> str:
        report = []
        data = self.audit()
        
        report.append(f"# Prompt Audit Report: `{self.filename}`")
        report.append(f"Estimated Tokens: **{data['metrics']['est_tokens']}** | Words: {data['metrics']['words']} | Characters: {data['metrics']['chars']}\n")
        
        scores = [
            data["politeness"]["score"],
            data["persona"]["score"],
            data["caching"]["score"],
            data["prism"]["score"],
            data["xml"]["score"],
            data["wall_of_text"]["score"],
            data["claude_code"]["score"],
            data["data_formats"]["score"],
            data["token_compression"]["score"],
        ]
        avg_score = sum(scores) / len(scores)
        
        report.append(f"## Overall Efficiency Score: **{avg_score:.1f}/100**\n")
        report.append("## Detailed Audits\n")
        
        categories = [
            ("Politeness Waste (Redundant Tokens)", "politeness"),
            ("Persona Placebo (Role-Prompting)", "persona"),
            ("Prefix Cache Friendliness", "caching"),
            ("Prism Prompting (Suffix-Loading)", "prism"),
            ("Semantic Delineation (XML Tags)", "xml"),
            ("Instruction Density (Wall of Text)", "wall_of_text"),
            ("Claude Code Specific Mechanics", "claude_code"),
            ("Data Format Efficiency (Markdown/YAML vs JSON/XML)", "data_formats"),
            ("Token Compression Potential", "token_compression"),
        ]
        
        for name, key in categories:
            cat_data = data[key]
            status = "✅ PASS" if cat_data["passed"] else "❌ WARN"
            report.append(f"### {status} | {name}")
            report.append(f"- **Details**: {cat_data['details']}")
            report.append(f"- **Metric Score**: {cat_data['score']}/100\n")

        report.append("## Recommendation Action Plan")
        actions = []
        if not data["politeness"]["passed"]:
            actions.append("- Ruthlessly strip conversational pleasantries (e.g. 'please', 'thank you', 'could you').")
        if not data["persona"]["passed"]:
            actions.append("- Replace persona-based constraints ('Act as a...') with direct structural guidelines and code/text examples.")
        if not data["caching"]["passed"]:
            actions.append("- Move all dynamic parameters (e.g. `{input_code}`) to the very end of the file to preserve prefix caching.")
        if not data["prism"]["passed"]:
            actions.append("- Restate your formatting requirements, output schemas, or primary target queries in the last 20% of the prompt.")
        if not data["xml"]["passed"]:
            actions.append("- Wrap system instructions, context documents, and outputs in custom matching XML tags (e.g. `<instructions>`, `<context>`).")
        if not data["wall_of_text"]["passed"]:
            actions.append("- Refactor massive text paragraphs into bullet points, nested configurations, or XML nodes.")
        if not data["claude_code"]["passed"]:
            actions.append("- Bound targets explicitly with @file:line, run commands using !command, and reset sessions using `/clear` or `/compact` for long chats.")
        if not data["data_formats"]["passed"]:
            actions.append("- Convert tabular or structured raw data blocks from JSON/XML to Markdown or YAML to save tokens.")
        if not data["token_compression"]["passed"]:
            actions.append("- Run `python scripts/compress_prompt.py` to compress whitespace and apply symbolic/caveman protocol abbreviations.")

        if not actions:
            report.append("Prompt is fully optimized! No immediate changes required.")
        else:
            report.extend(actions)

        return "\n".join(report)

    def refactor(self) -> str:
        """Applies automated best-effort corrections to the prompt text."""
        fixed = self.content

        # 1. Strip politeness
        polite_patterns = [
            (r"\bplease\s*", ""),
            (r"\bthank\s+you(?:\s+so\s+much)?\s*(?:very\s+much)?(?:\s*appreciate\s+it)?[\.,!\?]*\s*", ""),
            (r"\bthanks\s*[\.,!\?]*\s*", ""),
            (r"\bif\s+you\s+don't\s+mind\s*[\.,!\?]*\s*", ""),
            (r"\bappreciate\s+it\s*[\.,!\?]*\s*", ""),
            (r"\bcould\s+you\s*", ""),
            (r"\bcan\s+you\s*", ""),
            (r"\bwould\s+you\s*", ""),
            (r"\bi\s+(?:need|want)\s+you\s+to\s*", ""),
        ]
        for pat, replacement in polite_patterns:
            fixed = re.sub(pat, replacement, fixed, flags=re.IGNORECASE)

        # 2. Strip simple persona prompts (e.g. "Act as a...", "You are a...")
        persona_patterns = [
            r"\bAct\s+as\s+(?:an?\s+)?(?:expert\s+)?(?:senior\s+)?(?:genius\s+)?(?:level\s+)?[a-zA-Z0-9_-]+(?:\s+[a-zA-Z0-9_-]+){0,3}[\.,!\?]*\s*",
            r"\bYou\s+are\s+(?:an?\s+)?(?:expert\s+)?(?:senior\s+)?(?:genius\s+)?(?:level\s+)?[a-zA-Z0-9_-]+(?:\s+[a-zA-Z0-9_-]+){0,3}[\.,!\?]*\s*",
        ]
        for pat in persona_patterns:
            fixed = re.sub(pat, "", fixed, flags=re.IGNORECASE)

        # 3. Cache compliance: Shift dynamic parameters to the end
        placeholders = re.findall(r"(\{[a-zA-Z0-9_-]+\})", fixed)
        if placeholders:
            lines = fixed.splitlines()
            static_lines = []
            dynamic_lines = []
            for line in lines:
                if any(ph in line for ph in placeholders):
                    dynamic_lines.append(line)
                else:
                    static_lines.append(line)
            
            static_body = "\n".join(static_lines).strip()
            dynamic_body = "\n".join(dynamic_lines).strip()
            
            # 4. XML Delineation wrapping
            if not re.search(r"<[a-zA-Z0-9_-]+>.*?</[a-zA-Z0-9_-]+>", fixed, re.DOTALL):
                fixed = f"<instructions>\n{static_body}\n</instructions>\n\n<context>\n{dynamic_body}\n</context>"
            else:
                fixed = f"{static_body}\n\n{dynamic_body}"
        else:
            if not re.search(r"<[a-zA-Z0-9_-]+>.*?</[a-zA-Z0-9_-]+>", fixed, re.DOTALL):
                fixed = f"<instructions>\n{fixed.strip()}\n</instructions>"

        # Double check spacing
        fixed = re.sub(r"\n{3,}", "\n\n", fixed)
        return fixed.strip() + "\n"


def main():
    parser = argparse.ArgumentParser(description="Audit and refactor LLM and Claude Code prompts for token efficiency and cache optimization.")
    parser.add_argument("prompt", nargs="?", help="Prompt text or path (or - for stdin)")
    parser.add_argument("--file", "-f", help="Path to prompt text file to audit")
    parser.add_argument("--fix", help="Path to output the automatically refactored/fixed prompt")
    args = parser.parse_args()

    # Determine input content
    content = ""
    filename = "Prompt"
    
    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"[ERROR] File not found: {file_path}", file=sys.stderr)
            sys.exit(1)
        content = file_path.read_text(encoding="utf-8")
        filename = file_path.name
    elif args.prompt:
        if args.prompt == "-":
            content = sys.stdin.read()
        elif Path(args.prompt).exists():
            file_path = Path(args.prompt)
            content = file_path.read_text(encoding="utf-8")
            filename = file_path.name
        else:
            content = args.prompt
    else:
        # Fallback to stdin if no args provided and not interactive
        if not sys.stdin.isatty():
            content = sys.stdin.read()
        else:
            parser.print_help()
            sys.exit(1)

    # If auditing a skill, strip out frontmatter to analyze the core instructions
    skill_frontmatter = ""
    if filename == "SKILL.md":
        parts = content.split("---")
        if len(parts) >= 3:
            skill_frontmatter = "---" + parts[1] + "---\n\n"
            content = "---".join(parts[2:])

    auditor = PromptAuditor(content, filename=filename)
    
    if args.fix:
        refactored_content = auditor.refactor()
        output_path = Path(args.fix)
        try:
            if filename == "SKILL.md":
                output_path.write_text(skill_frontmatter + refactored_content, encoding="utf-8")
            else:
                output_path.write_text(refactored_content, encoding="utf-8")
            print(f"[OK] Refactored prompt successfully written to: {output_path}")
        except Exception as e:
            print(f"[ERROR] Could not write refactored output: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(auditor.generate_report())


if __name__ == "__main__":
    main()
