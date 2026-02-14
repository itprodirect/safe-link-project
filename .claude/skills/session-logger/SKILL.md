---
name: session-logger
description: Log development session activity with structured categories. Use when ending a session, reviewing progress, or documenting decisions. Trigger on "log this session", "update the log", "what should I log?", "end session".
disable-model-invocation: true
---

# Session Logger

Structured session logging for the Link Safety Hub project. Every coding session — whether in Claude Code, Codex, or manual development — gets a log entry appended to `SESSION_LOG.md` in the project root.

## When to Trigger

- User says: "log this session", "update the log", "what should I log?", "end session"
- End of any significant development session
- After completing a module, fixing a bug, or making an architectural decision

## Log Entry Format

Append the following template to `SESSION_LOG.md` (create the file if it doesn't exist):

```markdown
## YYYY-MM-DD HH:MM — [Brief Goal]

**Agent:** [Claude Code | Codex | Manual | Claude.ai]

**Goal:** What this session was trying to accomplish

**Module(s) Touched:** [core | homoglyph | redirect | email_auth | qr_decode | family_mode | inbox_scanner | adapter:cli | adapter:api | docs | ci | none]

**Changes:**
- Specific changes made (files created, modified, deleted)

**Decisions:**
- Choice made — because [reasoning]

**Open Questions:**
- Unresolved items that need future attention

**Next:**
- Immediate next steps for the next session

**Tests:** [Added | Updated | Passing | Failing | N/A]
```

## Decision Tree for Categorization

When reviewing session activity, categorize each item:

```
Changed a file or feature?          → CHANGE (include file path)
Made a choice between options?      → DECISION (include WHY)
Something you're unsure about?      → OPEN QUESTION
What should happen next?            → NEXT
```

## Rules

1. **Always include the agent type.** This project uses multiple AI coding agents. Knowing which agent did the work helps with debugging and pattern recognition.
2. **Always include module(s) touched.** This tracks which modules are getting attention and which are being neglected.
3. **Decisions MUST include reasoning.** "Used Pydantic v2" is useless. "Used Pydantic v2 — because v1 is EOL and v2's model_validator pattern fits our Finding validation needs" is useful.
4. **Open Questions carry forward.** If an open question from a previous session is resolved, move it to Decisions in the new entry with the resolution. Don't just delete it.
5. **Keep entries concise.** Each section should be 1-5 bullet points. If you need more, the session was too large — split future sessions into smaller units.
6. **Log even "failed" sessions.** If you spent an hour debugging and didn't fix it, that's valuable context for the next session. Document what you tried and what you ruled out.

## Example Entry

```markdown
## 2026-02-13 14:30 — Core engine models and scorer MVP

**Agent:** Claude Code

**Goal:** Implement the core Pydantic models and risk scoring engine

**Module(s) Touched:** core

**Changes:**
- Created `src/lsh/core/models.py` — AnalysisInput, Finding, Evidence, AnalysisResult
- Created `src/lsh/core/scorer.py` — normalize() with severity bands (0-20 INFO → 81-100 CRITICAL)
- Created `tests/core/test_models.py` — 8 test cases for model validation
- Created `tests/core/test_scorer.py` — 5 test cases including edge cases

**Decisions:**
- Used max-score-wins for aggregate risk — because it's the simplest to explain to family users and avoids score averaging that hides critical findings
- Made Finding.family_explanation optional — because modules can leave it empty and Family Mode (#9) fills it in as a post-processing step

**Open Questions:**
- Should severity bands be configurable per-deployment, or hardcoded?
- How to handle modules that return 0 findings — is that INFO or should it be silent?

**Next:**
- Build homoglyph detector (#1) using the confusables package
- Add Unicode script analysis for mixed-script detection
- Create test fixtures with real-world punycode phishing domains

**Tests:** Added — 13 tests, all passing
```

## Cross-Session Patterns

Periodically (every 5-10 sessions), review the log for patterns:

- **Stalled modules:** Modules that keep showing up in Open Questions but never in Changes
- **Decision drift:** Contradictory decisions across sessions (sign of unclear architecture)
- **Agent effectiveness:** Which agents produce the most Changes vs Open Questions
- **Scope creep:** Next items that keep growing instead of shrinking
