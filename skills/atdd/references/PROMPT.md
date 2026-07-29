# Spec → four layers

Framing for turning an executable specification into a working four-layer solution. Use when
starting from scratch, or hand it to a subagent. Fill the placeholders, keep the constraints.

---

Implement this using acceptance-test-driven development and the four-layer model:

1. **Executable specification** — from the perspective of an external user, in the language of
   the problem domain. WHAT, never HOW.
2. **DSL** — shared vocabulary the specs are written in. Precise where the scenario cares,
   defaulted everywhere it does not. No assertions, no SUT knowledge.
3. **Protocol driver** — adapter between DSL and system. All assertions live here. Implements a
   driver interface so a second protocol can be added without touching the specs.
4. **System under test** — real implementation, deployed the way production is deployed.

Constraints:

- Implement ONLY tests that correspond to behaviour the specification states.
- Do NOT implement tests for unspecified behaviour.
- Do NOT assume behaviour for scenarios the specification does not cover.
- Additional tests you believe are valuable: list them as suggestions, do not write them.

Isolation is mandatory: every scenario creates its own data partition as its first step, and
every uniqueness-bearing identifier goes through the alias helper so the suite survives parallel
and repeated runs.

Work in three phases and stop for review after each: 🔴 spec + DSL (driver missing, does not
run) → 🟢 driver + SUT connection (runs) → 🧼 refactor + prove parallel and repeat runs are
deterministic.

Report per test: name, the scenario line it covers, pass/fail, and the assertion that proves it.

Specification:

```gherkin
<paste Feature / Scenario blocks here>
```

Stack: `<language, test runner, protocol>`
Existing infrastructure: `<alias helper, driver interface, DSL root — or "none, build them">`

---

## If the spec is prose, not Gherkin

Convert first, and get the scenarios accepted before writing any code. One scenario per
behaviour, `Given` = seeded state, `When` = the single action under test, `Then` = the
observable outcome. If a scenario needs two `When`s, it is two scenarios.
