# AGENTS.md

## Project purpose

This repository is for designing, building, testing, and shipping reliable pyRevit tools.

Treat each tool as a small product. Build the smallest useful version first, prove that it works, and only then add features and production-quality UI.

## Communication

- The user often uses speech-to-text. Infer obvious transcription mistakes from context (for example, "told" may mean "tool").
- Do not repeatedly correct minor wording or spelling mistakes.
- Ask a concise clarification only when an ambiguity would materially change the tool's behavior, data, safety, or architecture.
- Explain Revit and programming concepts in plain language and give concrete examples when useful.
- Clearly distinguish between what has been verified locally and what still needs to be tested inside Revit.

## Required workflow for every tool

Follow these phases in order. Do not jump directly to a polished production implementation.

### Phase 1: Research and implementation proposal

Before writing the tool:

1. Understand the user problem, desired outcome, affected Revit elements, and expected workflow.
2. Inspect the repository for existing patterns or reusable code.
3. Research the relevant Revit API. Prefer [RevitAPIDocs](https://www.revitapidocs.com/) for fast API lookup and use Autodesk's official documentation or other reliable sources when additional confirmation is needed.
4. Confirm that the researched API applies to the Revit version targeted by the tool. Never assume that an API is available in every version.
5. Identify important implementation constraints, including:
   - required selections and inputs;
   - document and view requirements;
   - transaction and regeneration needs;
   - read-only, linked-model, group, design-option, and worksharing limitations when relevant;
   - cancellation, empty-result, and invalid-element behavior;
   - IronPython or CPython compatibility and external dependencies.
6. Present a short implementation proposal containing:
   - the recommended approach;
   - the main Revit API classes and methods;
   - the proposed user workflow;
   - important risks and edge cases;
   - what will be included in the basic version and what will wait for later.

If several approaches have meaningful tradeoffs, explain them and recommend one. Obtain the user's decision before implementing when the choice would materially change the result. Otherwise, proceed with the recommended approach.

### Phase 2: Build a working basic version

Create the smallest end-to-end version that demonstrates the core value of the tool.

- Keep the logic simple and readable.
- Use the project's existing pyRevit bundle conventions. If none exist yet, establish a conventional extension/tab/panel/button structure.
- Separate Revit interaction from reusable business logic when practical.
- Keep transactions as small and safe as possible.
- Handle user cancellation without showing an error.
- Avoid elaborate forms, settings, icons, telemetry, and optional features at this stage unless the core workflow requires them.
- Avoid unnecessary third-party packages, especially packages unavailable in pyRevit's selected Python engine.
- Run every useful local check available, such as syntax validation, focused unit tests for pure logic, and static inspection.

At the end of this phase, report what works, what was verified, and what requires an in-Revit test.

### Phase 3: Improve features incrementally

Only improve the tool after the basic workflow is working.

- Add one coherent feature or small feature group at a time.
- Preserve the proven core workflow while extending it.
- Prioritize features by user value, reliability, and implementation risk.
- Re-test the existing workflow after each material change.
- Do not mix a large functional rewrite with major UI polish unless necessary.
- Keep optional enhancements separate from the minimum production requirements.

Before a substantial expansion, briefly state what will change and how it affects testing.

### Phase 4: Test and make the tool error-resistant

Testing is a shared process because Revit may not be available in the development environment.

The agent must:

1. Run all relevant automated or local checks that do not require Revit.
2. Review transaction boundaries, failure behavior, cancellation paths, and partial-update risks.
3. Test pure data-processing logic separately from the Revit API where practical.
4. Never claim that a tool was tested in Revit unless it was actually executed there.
5. When the agent cannot run Revit, provide a precise manual test plan containing:
   - required model setup;
   - exact steps to run the tool;
   - expected visible results;
   - how to verify the model changes;
   - cancellation and invalid-input tests;
   - relevant edge cases;
   - undo/rollback checks;
   - the error details or pyRevit output the user should send back if a test fails.
6. Use the user's test results to diagnose and fix problems, then provide focused retest steps.

Continue the test/fix/retest cycle until known failures are resolved. Do not describe the tool as error-free; describe the tests completed and any remaining limitations.

### Phase 5: Productionize and ship

Begin this phase only after the core behavior has been validated.

Production work should include the relevant items below:

- a clear button name, tooltip, help text, and author/version metadata;
- suitable `pyrevit.forms` dialogs or a WPF interface when the workflow needs richer interaction;
- sensible defaults and validation close to each input;
- clear success, warning, empty-result, and error messages;
- progress feedback and cancellation for long-running operations;
- safe handling of no document, wrong document type, wrong view, empty selection, deleted elements, and user cancellation as applicable;
- transaction rollback or safe partial-failure behavior;
- useful logging and actionable error reporting without exposing confusing internal details;
- compatibility metadata for supported Revit and pyRevit/Python versions;
- button/icon assets and bundle configuration;
- concise usage and testing documentation;
- a final regression test of the complete workflow.

Before calling a tool ready for production, provide a release checklist and identify exactly which checks were performed locally and which were confirmed by the user in Revit.

## Coding principles

- Optimize first for correctness, model safety, and maintainability.
- Follow established repository conventions instead of introducing a new pattern for each tool.
- Prefer explicit, understandable Revit API code over clever abstractions.
- Keep Revit API objects within valid document and transaction lifetimes.
- Do not silently modify more elements than the user expects.
- Do not swallow unexpected exceptions. Give the user an actionable message and preserve diagnostic details for troubleshooting.
- Treat selections, names, parameter values, and form input as untrusted input that must be validated.
- Preserve the user's existing work and unrelated repository changes.

## Definition of done

A tool is complete only when:

- its intended behavior and supported Revit versions are documented;
- the core workflow has been tested successfully inside Revit by the agent or the user;
- relevant normal, cancellation, invalid-input, and edge-case scenarios have been checked;
- known errors found during testing have been fixed and retested;
- the interface is understandable to its intended users;
- installation and usage instructions are available;
- remaining limitations are explicitly documented.
