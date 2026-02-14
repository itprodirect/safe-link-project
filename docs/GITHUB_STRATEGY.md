# GitHub Strategy

## Decision: Monorepo (Not Multi-Repo)

**Use a single repository** with clear internal boundaries, not separate repos per module.

### Why monorepo wins here

The ChatGPT plan implies building modules independently and "combining later." That sounds clean in theory but creates real pain in practice. Here's the tradeoff:

**Multi-repo problems you'd hit:**
- Shared core engine means cross-repo dependencies from day one
- Pydantic model changes require coordinated releases across repos
- Testing module interactions requires pulling multiple repos
- CI/CD multiplies — each repo needs its own pipeline
- Claude Code and Codex work better with full project context in one repo

**Monorepo gives you:**
- Single `pip install -e .` and everything works
- Refactoring core models updates all modules in one commit
- One CI pipeline, one test suite, one lint config
- Agents see the full codebase and make better decisions
- You can still extract modules to separate repos later (this direction is easy; the reverse is painful)

### When to split

Consider extracting a module to its own repo only when:
- It has a genuinely independent user base (e.g., QR decoder becomes a popular standalone library)
- It needs a different release cadence (e.g., the Go port ships as a separate binary)
- It has different contributors who don't need the rest of the codebase

## Branch Strategy

```
main                    ← Always deployable, all tests pass
  └── dev               ← Integration branch, where modules merge together
       ├── feat/core-models          ← Core engine work
       ├── feat/mod-homoglyph        ← Module #1
       ├── feat/mod-redirect         ← Module #2
       ├── feat/mod-email-auth       ← Module #5
       ├── feat/adapter-cli          ← CLI adapter
       ├── fix/homoglyph-unicode     ← Bug fixes
       └── chore/ci-setup            ← Infrastructure
```

### Branch rules

- `main`: Protected. Requires PR with passing CI. Only merge from `dev`.
- `dev`: Semi-protected. Requires passing tests. Feature branches merge here.
- `feat/*`: One feature or module per branch. Name format: `feat/mod-<module>` for modules, `feat/core-<thing>` for core, `feat/adapter-<name>` for adapters.
- `fix/*`: Bug fixes. Can go to `dev` or directly to `main` via hotfix if critical.

### Workflow

```
1. Create feature branch from dev
2. Build + test locally
3. Open PR to dev with description of what the module does
4. CI runs tests, lint, typecheck
5. Merge to dev
6. When dev is stable, merge dev → main with a version tag
```

## Commit Conventions

Use conventional commits so changelogs can be auto-generated later:

```
feat(homoglyph): add IDN/punycode detection
feat(core): define Finding and AnalysisInput models
fix(redirect): handle timeout on slow redirects
test(email-auth): add SPF fail test fixtures
docs(architecture): add data flow diagram
chore(ci): add GitHub Actions workflow
log(session): 2026-02-13 core engine models MVP
```

**Note:** Session log updates get their own commit with the `log(session)` prefix. Don't bundle them into feature commits — the log should be a clean, append-only history.

## Recommended GitHub Settings

- **Branch protection on `main`:** Require PR, require status checks, require linear history
- **Branch protection on `dev`:** Require status checks
- **Issue templates:** Bug report, new module proposal, feature request
- **Labels:** `module:homoglyph`, `module:redirect`, `module:email-auth`, `core`, `adapter:cli`, `docs`, `good-first-issue`
- **Projects board:** Kanban with columns: Backlog → In Progress → Review → Done
- **Releases:** Tag `main` with semver after each phase milestone (v0.1.0 = Phase 1 CLI, v0.2.0 = Phase 2 web, etc.)

## CI/CD Pipeline (GitHub Actions)

Start simple and expand:

### Phase 1 (immediate)

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -e ".[dev]"
      - run: ruff check src/ tests/
      - run: mypy src/
      - run: pytest -v --tb=short
```

### Phase 2 (when web app exists)

Add: Docker build, integration tests with network access, frontend lint/build.

### Phase 3 (distribution)

Add: PyPI publish on tag, Go binary build matrix (linux/mac/windows), release notes generation.

## Tag & Release Strategy

```
v0.1.0  Phase 1 complete: CLI with modules #1, #2, #5, #7, #9
v0.2.0  Phase 2 complete: Web app + API
v0.3.0  Phase 3 complete: Inbox scanner + QR camera
v1.0.0  Phase 4: Hardened, documented, ready for public use
```

## Working with AI Agents

### Claude Code

- The `CLAUDE.md` file in the repo root gives Claude Code full project context
- When starting a Claude Code session, it will read CLAUDE.md and understand the module contract, tech stack, and conventions
- Use Claude Code for: implementing new modules, writing tests, refactoring core

### OpenAI Codex

- Same CLAUDE.md serves as context (rename-friendly — the content matters, not the filename)
- Use Codex for: boilerplate generation, test fixture creation, documentation

### Tips for agent-assisted development

1. **Always commit working code before starting an agent session.** If the agent makes a mess, you can reset.
2. **Read the last 2-3 entries in `SESSION_LOG.md` before starting.** This is how agents (and you) maintain continuity between sessions.
3. **One module per session.** Don't ask an agent to build three modules at once.
4. **Run tests after every agent session.** Agents sometimes break things they didn't touch.
5. **Review agent PRs like you would a junior developer's.** Trust but verify.
6. **End every session with `/session-logger`.** This logs changes, decisions, open questions, and next steps to `SESSION_LOG.md`. Non-negotiable — it's how the project maintains memory across agents and sessions.
7. **Include the agent name in the log.** Claude Code, Codex, and manual sessions have different strengths. Tracking which agent did what helps you optimize your workflow over time.
