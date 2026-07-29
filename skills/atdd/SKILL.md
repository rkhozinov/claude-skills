---
name: atdd
description: Acceptance-test-driven development with the four-layer model (spec / DSL / protocol driver / SUT). Use when writing acceptance tests, turning Gherkin or Given-When-Then scenarios into executable specs, building a test DSL or protocol driver, or reviewing an acceptance suite that breaks on every refactor.
license: MIT
---

# ATDD — four-layer acceptance testing

Acceptance tests say WHAT the system does, in the language of the problem domain.
Never HOW. A test that names an endpoint, a status code, a CSS selector, or a table
column is coupled to the implementation and will break on the next refactor.

Unit-level red-green-refactor is a different skill (`test-driven-development`). This
one is about the outer loop: one executable spec per business scenario, running
against a production-like system.

## The four layers

| # | Layer | Owns | Never |
|---|-------|------|-------|
| 1 | **Executable spec** | Business language. One scenario = one test. Each Given/When/Then line = exactly one DSL call | Code, technical detail, explanatory comments |
| 2 | **DSL** | Vocabulary of the domain, parameter defaults, aliasing for isolation, delegation to the driver | Assertions, business logic, network calls, any SUT knowledge |
| 3 | **Protocol driver** | ALL assertions. Talks to the SUT through its real public interface. Hides multi-step flows | Holding business state, framework-specific assert APIs |
| 4 | **SUT** | The real deployed system: your DB, cache, queues, internal services | Being stubbed. It is the target, not test infrastructure |

Layer 2 depends on the driver **interface**, never a concrete driver. That is what lets
one spec run over HTTP, CLI, and UI — swap the driver at runtime (`ACCEPTANCE_PROTOCOL=api|web|cli`),
touch no test.

```gherkin
Given the user has an account
And they have a completed todo "Buy milk"
When they archive it
Then it appears in the archive
```
```
dsl.user.hasAccount(email: "user@test.com")   # seeding:      has X
dsl.todo.hasCompleted(name: "Buy milk")       # seeding:      has X
dsl.todo.archives(name: "Buy milk")           # action:       verb
dsl.todo.confirmInArchive(name: "Buy milk")   # verification: confirm X
```

`confirmInArchive`, not `assertInArchive` — the DSL speaks business, and the assert
lives one layer down. DSL method names and driver method names match 1:1.

## Phase cycle

Three phases. **Stop for human review after each one.** Do not advance unaccepted.

**🔴 Phase 1 — spec + DSL.** Write the scenarios and the DSL that mirrors their wording.
DSL calls driver methods that do not exist yet; compile/import failure IS the red state.
First step of every scenario creates its own data partition. Fresh DSL instance per scenario.
→ review: does the DSL read like the scenario? Any assertion leaked in? Aliasing present?

**🟢 Phase 2 — protocol driver.** Implement the driver behind the interface. Assertions and
failure logic all live here: method returns normally = pass, throws the language's native
error = fail. Never a boolean, never `expect()` from the test framework. Error messages carry
context: `Expected tag 'kotlin' in list: [java, spring]`. Poll with a timeout for async work,
never `sleep`. Stub external third parties only.
→ review: interface implemented, tests execute (pass or fail depends on SUT readiness).

**🧼 Phase 3 — refactor + prove isolation.** Run the suite in parallel, then run one scenario
twice. Both must be deterministic. Consolidate near-identical driver methods. Check against
[references/CHECKLIST.md](references/CHECKLIST.md).
→ review: final.

## Isolation — the part everyone skips

Acceptance tests hit a real DB, so they are slow, so they must run in parallel, so they must
not collide. Three levels:

- **System** — stub ONLY third parties you do not control (payment gateway, email provider,
  the clock). Your own database, cache, and services are the SUT. Stubbing what you own means
  testing a system that does not exist.
- **Functional** — every scenario creates its own partition (its own account / workspace /
  tenant) as its first action and works only inside it.
- **Temporal** — every uniqueness-bearing identifier goes through an alias helper that appends
  a per-run counter: `user@test.com` → `user@test.com1`, `user@test.com2`. Same scenario, run
  twice, same result.

Alias identifiers (emails, usernames, order IDs, todo names). Use defaults for everything
descriptive (passwords, roles, addresses) so the spec states only what the behaviour needs.

Do NOT clean up after each scenario. Aliased data accumulates harmlessly. Wipe once, at the
start of the next run.

## Required infrastructure

Before Phase 1, these must exist — if they do not, build them first or ask:

- alias context (scenario-scoped counter) + parameter helper (`alias` / `optional` / `optionalList`)
- driver interface + factory for runtime protocol selection
- DSL root object composing per-domain children (`dsl.user`, `dsl.todo`)

## Hard rules

- Implement ONLY behaviour the spec states. No invented scenarios, no guessed edge cases.
  Worth-adding cases go in a suggestions list for the human — not into the suite.
- Never `sleep`. Poll with a timeout.
- The SUT is the single source of truth. Verify by asking the SUT, never by trusting state
  the test layer remembers.
- Driver reaches the SUT only through the interface real consumers use. No direct function
  calls into the code, no reaching into its DB.
- Adding a driver method means adding it to the interface, not just the implementation.

## Reviewing an existing suite

Read [references/CHECKLIST.md](references/CHECKLIST.md) and report violations by layer.
Most common findings, in order: assertions in the DSL, status codes in the spec, stubbed
internal DB, per-scenario cleanup, hardcoded identifiers that break on re-run.

## Starting from a plain spec

Given a raw feature description with no scenarios, use
[references/PROMPT.md](references/PROMPT.md) as the framing to produce the four layers.

---

Synthesized from Dave Farley's four-layer acceptance testing model (*Continuous Delivery*,
[cd.training](https://courses.cd.training/)) and the isolation, naming, and phase-gate rules of
[AAID](https://github.com/dawid-dahl-umain/augmented-ai-development) by Dawid Dahl (MIT), whose
`aaid-bdd` plugin is the fuller treatment of the same ideas.
