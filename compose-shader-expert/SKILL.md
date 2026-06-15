---
name: compose-shader-expert
description: "Expert guidance for writing and integrating high-performance AGSL/SkSL shaders in Jetpack Compose and Compose Multiplatform. Trigger this skill whenever the user mentions AGSL, shaders, RenderEffect, custom graphics modifiers, glassmorphism, blur, metaballs, or procedural rendering in Compose, even if they only ask for a simple visual effect."
---

# Compose Shader Expert

Core guidelines for modern (2025/2026) high-performance AGSL/SkSL shader integration in Jetpack Compose and Compose Multiplatform.

<instructions>
Use progressive disclosure: consult specific reference files for details. Maintain strict token efficiency. Shaders must be optimized for mobile GPUs, branchless, and cached to prevent recompositions and compile spikes.
</instructions>

## 1. Quick Decision Matrix

| Task / Domain | Action / Pattern | Details |
| :--- | :--- | :--- |
| **AGSL Syntax & Math** | Coordinate mapping, layout(color), premultiplied alpha | Consult [syntax-coordinate.md](file:///Users/jsanjaya/.gemini/config/skills/compose-shader-expert/references/syntax-coordinate.md) |
| **Compose Integration** | ShaderBrush, RenderEffect, drawWithCache, graphicsLayer | Consult [compose-lifecycle.md](file:///Users/jsanjaya/.gemini/config/skills/compose-shader-expert/references/compose-lifecycle.md) |
| **GPU Optimization** | Branching avoidance, precision choice, register pressure, caching | Consult [performance-gpu.md](file:///Users/jsanjaya/.gemini/config/skills/compose-shader-expert/references/performance-gpu.md) |
| **Visual Effects** | Glassmorphism, liquid metaballs, noise textures, SDF borders | Consult [shader-use-cases.md](file:///Users/jsanjaya/.gemini/config/skills/compose-shader-expert/references/shader-use-cases.md) |
| **Special Effects** | Glossy 3D Liquid, Topographic Flow, Holographic tilt, Water Ripples | Consult [special-effects.md](file:///Users/jsanjaya/.gemini/config/skills/compose-shader-expert/references/special-effects.md) |

## 2. Directory Structure

All detailed reference materials and scripts are partitioned into subdirectories:

*   **References**:
    *   [syntax-coordinate.md](file:///Users/jsanjaya/.gemini/config/skills/compose-shader-expert/references/syntax-coordinate.md) — AGSL vs GLSL differences, coordinate space alignment, color-space management, and alpha premultiplication.
    *   [compose-lifecycle.md](file:///Users/jsanjaya/.gemini/config/skills/compose-shader-expert/references/compose-lifecycle.md) — Lifetime management, drawWithCache vs drawBehind, RenderEffect offscreen buffers, custom Modifier.Node optimization, and expect/actual KMP abstraction.
    *   [performance-gpu.md](file:///Users/jsanjaya/.gemini/config/skills/compose-shader-expert/references/performance-gpu.md) — Mobile GPU branching rules, precision (float vs half), texture fetch bandwidth limits, and shader warm-up/caching.
    *   [shader-use-cases.md](file:///Users/jsanjaya/.gemini/config/skills/compose-shader-expert/references/shader-use-cases.md) — Detailed mathematics, code snippets, and implementation steps for frosted glassmorphism, liquid metaballs, and procedural noise.
    *   [special-effects.md](file:///Users/jsanjaya/.gemini/config/skills/compose-shader-expert/references/special-effects.md) — Detailed recipes and mathematical formulations for Glossy 3D Liquid, Topographic Flow, Holographic tilt card, and Touch-driven Water ripples.
*   **Scripts**:
    *   [validate_shader.py](file:///Users/jsanjaya/.gemini/config/skills/compose-shader-expert/scripts/validate_shader.py) — Python CLI tool to parse shader strings for common performance and AGSL syntax issues.

Always read the specific file containing the details required for the task.

<constraints>
Developers must follow these constraints:
1. Always create and cache shaders inside drawWithCache or graphicsLayer to avoid per-frame allocation.
2. Ensure Y-coordinate mapping is correctly adjusted for AGSL's top-left origin.
3. Keep all custom shader outputs premultiplied.
4. Pass touch coordinates offscreen (e.g. `Offset(-9999f, -9999f)`) when inactive to avoid top-left `(0, 0)` clustering.
5. Avoid looping over discrete particles inside the pixel fragment shader; draw them using Canvas `drawCircle`/`drawPoints` over the shader background for order-of-magnitude performance improvements.
</constraints>
