# Acceptance test review checklist

Language-agnostic. Applies both when designing a new test and when auditing an existing suite.
Report findings grouped by layer, most coupled first.

## Layer 1 — executable spec

- [ ] Pure business language: no HTTP verbs, status codes, selectors, table or field names
- [ ] A non-technical stakeholder could read it and agree it describes the requirement
- [ ] Self-documenting — if a step needs a comment to be understood, rewrite the step
- [ ] Each line maps to exactly one DSL call
- [ ] Seeding is visible in Given steps, never hidden inside a When or Then
- [ ] Feature has a title and a one-line statement of the value it delivers
- [ ] No logic, loops, or conditionals

## Layer 2 — DSL

- [ ] No assertions
- [ ] No network calls, no SUT knowledge (endpoints, payload shapes, status codes)
- [ ] Depends on the driver interface; the concrete driver is injected, never constructed here
- [ ] Only logic present is parameter handling, defaults, and aliasing
- [ ] Sensible defaults so a scenario specifies only what it is actually about
- [ ] Verification methods use a consistent prefix (`confirm…`) and match driver names 1:1
- [ ] Holds no state beyond bridging steps within one scenario; nothing survives the scenario
- [ ] Reuse: steps differing only by a data value share one parameterized method — unless
      merging makes the spec read unnaturally. Business readability wins over DRY

## Layer 3 — protocol driver

- [ ] Owns every assertion. None exist above it
- [ ] Pass/fail by native mechanism: returns normally = pass, raises/returns error = fail.
      No booleans, no test-framework assert APIs (keeps it portable across runners)
- [ ] Atomic: each method fully succeeds or fails with a contextual message including the data
- [ ] Multi-step flows encapsulated here (`hasAccount` = register + login + set auth)
- [ ] Implements the shared interface; new methods added to the interface too
- [ ] Reaches the SUT only through its real public protocol (HTTP/CLI/UI), using a standard
      client, independent of the SUT's internal framework or config
- [ ] Stateless, or holds only transient protocol data (session token, last response) that is
      overwritten each call
- [ ] Async handled by polling with a timeout — no fixed sleeps
- [ ] Near-identical methods differing by one parameter are merged

## Isolation

- [ ] Only third parties outside your control are stubbed. DB, cache, queues, internal services are real
- [ ] Persistent state runs on a dedicated test instance, never shared with dev or prod
- [ ] Each scenario creates all its own data and assumes no execution order
- [ ] Every uniqueness-bearing identifier is aliased; alias context is scenario-scoped
- [ ] Suite passes run in parallel
- [ ] A single scenario passes when run alone
- [ ] Re-running the same scenario gives the same result
- [ ] No per-scenario cleanup. Data is wiped once at the start of the next run

## Shared state — the one exception

- [ ] Shared only for expensive idempotent setup (e.g. a pre-registered auth token). Never domain data
- [ ] Lives in a run-scoped setup hook, guarded to run once, thread-safe if scenarios parallelize
- [ ] The spec does not reveal the sharing — steps still read as business language
- [ ] A scenario that mutates shared state is tagged to get its own private instance

## External dependencies

- [ ] Mocked by default — the default path needs no flag
- [ ] Live runs are opt-in via explicit env flag and tagged at scenario or feature level
- [ ] Prefer read-only calls for live mode; mutations only against a vendor sandbox

## Final

- [ ] The whole suite passes with the new test included
- [ ] The test verifies a meaningful behaviour, not an implementation detail
- [ ] Nothing was implemented that the specification did not ask for
