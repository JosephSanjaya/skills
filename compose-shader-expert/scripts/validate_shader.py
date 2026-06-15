#!/usr/bin/env python3
"""AGSL shader validator script.

Checks AGSL shader source code for potential performance and syntax issues:
- discard keyword usage (Early-Z rejection disablement).
- if/else branching statements (SIMD thread divergence).
- normalized coordinates evaluated on shaders (eval() expects pixel coordinates).
- un-premultiplied color outputs.
"""

import re
import sys
from pathlib import Path


def validate_agsl(source: str) -> list[str]:
    warnings = []

    # 1. Check for discard
    if "discard" in source:
        warnings.append(
            "[PERFORMANCE] Found 'discard' keyword. This disables Early-Z depth-testing optimizations."
        )

    # 2. Check for branching (if-else)
    branching_matches = len(re.findall(r"\bif\b", source))
    if branching_matches > 0:
        warnings.append(
            f"[PERFORMANCE] Found {branching_matches} 'if' statements. Branching can cause SIMD warp execution divergence. "
            "Consider replacing with step(), clamp(), mix(), or smoothstep() where possible."
        )

    # 3. Check for normalized coordinate texture sampling
    # AGSL shader.eval() expects absolute pixel coordinates (e.g. fragCoord), not normalized uv (0 to 1).
    eval_pattern = re.compile(r"\b(\w+)\.eval\s*\(\s*([^)]+)\)")
    for match in eval_pattern.finditer(source):
        sampler_name, args = match.groups()
        # If args looks like standard uv (e.g., divided by resolution, or named uv/normCoords)
        if "/" in args or any(x in args for x in ["uv", "normalized"]):
            warnings.append(
                f"[WARNING] Child shader evaluation '{sampler_name}.eval({args})' appears to use normalized coordinates. "
                "AGSL child shader eval() expects absolute pixel coordinates. Pass coordinates multiplied by resolution."
            )

    # 4. Check for premultiplied alpha (heuristic)
    # If the return statement returns vec4/half4 directly and doesn't seem to multiply rgb by alpha:
    return_pattern = re.compile(
        r"return\s+half4\s*\(\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^)]+)\)"
    )
    for match in return_pattern.finditer(source):
        r, g, b, a = [x.strip() for x in match.groups()]
        if a != "1.0" and a != "1." and not any(a in channel for channel in [r, g, b]):
            warnings.append(
                "[CORRECTNESS] Return statement returns transparent color without premultiplying alpha. "
                f"Make sure RGB components are multiplied by alpha '{a}' before returning (e.g. half4(rgb * {a}, {a}))."
            )

    return warnings


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python3 validate_shader.py <path_to_shader_or_txt>")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"Error: File '{file_path}' does not exist.")
        sys.exit(1)

    content = file_path.read_text(errors="ignore")
    warnings = validate_agsl(content)

    if not warnings:
        print("\n\u2705 AGSL Shader looks good! No obvious issues found.")
    else:
        print(f"\n\u26a0\ufe0f Found {len(warnings)} potential issues in {file_path.name}:")
        for warning in warnings:
            print(f"  - {warning}")
        print("\nReview performance references for guidelines on fixing these.")


if __name__ == "__main__":
    main()
