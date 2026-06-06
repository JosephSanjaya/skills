export const meta = {
  name: 'architecture-recovery',
  description: 'Multi-agent codebase architecture recovery: parallel static/git/DI analysis → synthesis',
  phases: [
    { title: 'Gather', detail: 'Run gather_context.py + git archaeology + DI wiring detection in parallel' },
    { title: 'Deep Dive', detail: 'Per-module agents: scary sections + bounded context mapping + dynamic wiring' },
    { title: 'Synthesize', detail: 'Merge all findings into architecture.json + identify verification targets' },
  ],
}

// ── Schema definitions ────────────────────────────────────────────────────

const STATIC_SCHEMA = {
  type: 'object',
  properties: {
    project_type: { type: 'string' },
    entry_points: { type: 'array', items: { type: 'string' } },
    module_structure: { type: 'object' },
    scary_sections: { type: 'array' },
    git_hot_files: { type: 'array', items: { type: 'object', properties: { file: { type: 'string' }, commit_count: { type: 'number' } }, required: ['file', 'commit_count'] } },
    di_wiring: { type: 'array', items: { type: 'string' } },
    android_signals: { type: 'object' },
  },
  required: ['project_type', 'entry_points', 'module_structure'],
}

const COMPONENT_SCHEMA = {
  type: 'object',
  properties: {
    name: { type: 'string' },
    type: { type: 'string', enum: ['viewmodel', 'repository', 'usecase', 'service', 'module', 'screen', 'adapter', 'mapper', 'dao', 'api', 'other'] },
    file: { type: 'string' },
    imports: { type: 'array', items: { type: 'string' } },
    exports: { type: 'array', items: { type: 'string' } },
    bounded_context: { type: 'string' },
    is_scary: { type: 'boolean' },
    notes: { type: 'string' },
  },
  required: ['name', 'type', 'file'],
}

const MODULE_ANALYSIS_SCHEMA = {
  type: 'object',
  properties: {
    module_name: { type: 'string' },
    components: { type: 'array', items: COMPONENT_SCHEMA },
    bounded_context: { type: 'string' },
    context_type: { type: 'string', enum: ['core', 'supporting', 'generic'] },
    context_relations: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          to_context: { type: 'string' },
          pattern: { type: 'string', enum: ['ACL', 'Customer-Supplier', 'Conformist', 'Shared-Kernel', 'OHS'] },
          via: { type: 'string' },
        },
        required: ['to_context', 'pattern'],
      },
    },
    dynamic_wiring: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          config_file: { type: 'string' },
          loader: { type: 'string' },
          loads: { type: 'array', items: { type: 'string' } },
        },
        required: ['config_file'],
      },
    },
    constraints: {
      type: 'object',
      properties: {
        forbidden: { type: 'array', items: { type: 'array', items: { type: 'string' } } },
        interface_only: { type: 'array', items: { type: 'array', items: { type: 'string' } } },
      },
    },
    verification_targets: { type: 'array', items: { type: 'string' } },
  },
  required: ['module_name', 'components'],
}

const SYNTHESIS_SCHEMA = {
  type: 'object',
  properties: {
    project_type: { type: 'string' },
    components: { type: 'object' },
    bounded_contexts: { type: 'object' },
    context_relations: { type: 'array' },
    dynamic_wiring: { type: 'object' },
    constraints: { type: 'object' },
    scary_sections: { type: 'array' },
    verification_targets: { type: 'array', items: { type: 'string' } },
    high_churn_files: { type: 'array', items: { type: 'string' } },
    suggested_exploration_order: { type: 'array', items: { type: 'string' } },
  },
  required: ['project_type', 'components', 'bounded_contexts'],
}

// ── Phase 1: Parallel static + git gathering ─────────────────────────────

phase('Gather')

const repoRoot = args && args.repo_root ? args.repo_root : '.'

const [staticResult, gitResult, dynamicWiringResult] = await parallel([
  () => agent(
    `Run this command and return the JSON output exactly as-is:
\`\`\`
python3 ~/.claude/skills/context-collector/scripts/gather_context.py ${repoRoot}
\`\`\`
Parse and return the JSON.`,
    { label: 'static-scan', phase: 'Gather', schema: STATIC_SCHEMA }
  ),

  () => agent(
    `In git repo at ${repoRoot}, run archaeology analysis:
1. \`git log --since="90 days ago" --name-only --format="" | sort | uniq -c | sort -rn | head -30\` — top churned files
2. \`git log --since="90 days ago" --oneline | head -20\` — recent commits summary
3. \`git shortlog -sn --since="90 days ago" | head -10\` — active authors

Return JSON: { "top_churned_files": [{"file": string, "count": number}], "recent_commit_summary": string, "active_authors": [string] }`,
    {
      label: 'git-archaeology',
      phase: 'Gather',
      schema: {
        type: 'object',
        properties: {
          top_churned_files: { type: 'array', items: { type: 'object', properties: { file: { type: 'string' }, count: { type: 'number' } }, required: ['file', 'count'] } },
          recent_commit_summary: { type: 'string' },
          active_authors: { type: 'array', items: { type: 'string' } },
        },
        required: ['top_churned_files'],
      },
    }
  ),

  () => agent(
    `In repo at ${repoRoot}, find ALL dynamic dependency registration:
1. \`rg "ServiceLoader|importlib|forName|registerPlugin|loadClass|AutoService" --type kotlin --type java -l\` — list files
2. \`rg "startKoin|KoinApplication|val module = module" --type kotlin -l\` — Koin roots
3. \`rg "@Module.*@ComponentScan" --type kotlin -l\` — Koin annotation modules
4. Read the most relevant files found

Return JSON: { "registry_files": [string], "koin_roots": [string], "koin_modules": [string], "notes": string }`,
    {
      label: 'dynamic-wiring',
      phase: 'Gather',
      schema: {
        type: 'object',
        properties: {
          registry_files: { type: 'array', items: { type: 'string' } },
          koin_roots: { type: 'array', items: { type: 'string' } },
          koin_modules: { type: 'array', items: { type: 'string' } },
          notes: { type: 'string' },
        },
        required: ['registry_files', 'koin_modules'],
      },
    }
  ),
])

log(`Static scan: ${staticResult ? staticResult.module_structure?.modules?.length ?? 0 : 0} modules detected`)
log(`Git hot files: ${gitResult ? gitResult.top_churned_files?.length ?? 0 : 0} churned files`)
log(`DI wiring: ${dynamicWiringResult ? dynamicWiringResult.koin_modules?.length ?? 0 : 0} Koin modules`)

// ── Phase 2: Per-module deep dive ─────────────────────────────────────────

phase('Deep Dive')

const modules = (staticResult?.module_structure?.modules ?? []).slice(0, 12)
const scaryFiles = staticResult?.scary_sections ?? []
const hotFiles = (gitResult?.top_churned_files ?? []).slice(0, 10).map(f => f.file)

const moduleResults = await pipeline(
  modules,
  (moduleName) => agent(
    `Analyze module "${moduleName}" in repo at ${repoRoot}.

Context:
- Project type: ${staticResult?.project_type ?? 'unknown'}
- Scary files in this module: ${scaryFiles.filter(s => s.file?.includes(moduleName)).map(s => s.file).join(', ') || 'none'}
- Hot files in this module: ${hotFiles.filter(f => f.includes(moduleName)).join(', ') || 'none'}

Tool Rules:
- Prefer CBM tools (e.g. search_graph, query_graph) first (always pass the required 'project' parameter).
- Fallback to Serena tools (e.g. get_symbols_overview(relative_path=...), find_symbol, find_implementations) next.
- Only use grep/find/cat as a last resort on code files, or for non-code files (XML, Gradle, properties).

Tasks:
1. List all Kotlin/Java files in this module using search_graph or relative find fallback.
2. For files with names ending in ViewModel, Repository, UseCase, Service, Presenter — read their class signatures using get_symbols_overview(relative_path=...).
3. Identify the bounded context (what business noun does this module own?).
4. Find any ACL adapters: classes named *Adapter, *Translator, *Mapper at package boundaries using find_symbol or CBM.
5. Find any dynamic wiring: ServiceLoader, importlib, registerPlugin, @AutoService annotations.
6. Note any inter-module dependencies (import statements pointing to sibling modules).`,
    { label: `module:${moduleName}`, phase: 'Deep Dive', schema: MODULE_ANALYSIS_SCHEMA }
  )
)

const validModuleResults = moduleResults.filter(Boolean)
log(`Deep dive complete: ${validModuleResults.length}/${modules.length} modules analyzed`)

// ── Phase 3: Synthesize ───────────────────────────────────────────────────

phase('Synthesize')

const synthesis = await agent(
  `Synthesize architecture recovery findings into a final architecture.json.

## Static Scan Result
${JSON.stringify(staticResult, null, 2)}

## Git Archaeology
${JSON.stringify(gitResult, null, 2)}

## Dynamic Wiring Discovery
${JSON.stringify(dynamicWiringResult, null, 2)}

## Per-Module Analysis
${JSON.stringify(validModuleResults, null, 2)}

## Instructions
1. Merge all components from module analyses into a flat "components" map (key = component name)
2. Group into "bounded_contexts" by the bounded_context field from module analyses
3. Extract "context_relations" from all module analyses
4. Build "dynamic_wiring" from dynamicWiringResult + any module-level dynamic wiring
5. Merge all "constraints" (forbidden deps, interface-only access)
6. Set "scary_sections" = top 10 by line count from static scan
7. Set "high_churn_files" = top 10 from git archaeology
8. Set "verification_targets" = components marked is_scary=true + high-churn files that are components
9. Set "suggested_exploration_order":
   - Start with scary + high-churn overlap
   - Then DI/module roots
   - Then entry points
   - Then supporting modules last

Output a complete architecture.json following the schema exactly.`,
  { label: 'synthesize', phase: 'Synthesize', schema: SYNTHESIS_SCHEMA }
)

log(`Synthesis complete: ${Object.keys(synthesis?.components ?? {}).length} components, ${Object.keys(synthesis?.bounded_contexts ?? {}).length} bounded contexts`)

return synthesis
