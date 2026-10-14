# AI Image Metadata and Live Image-Title Alt Plan

Last updated: 2026-10-14

## Status and continuation protocol

This document is the durable source of truth for issue `#305021`. A new model
must read this document before changing any of the repositories listed below.

Checklist meaning:

- `[x]` — agreed, discovered, or completed.
- `[ ]` — not yet implemented or not yet verified.

Current checkpoint:

- [x] Read-only discovery completed.
- [x] Product/design grilling completed.
- [x] Scope and acceptance decisions agreed with the owner.
- [x] Durable implementation plan written.
- [x] Independent plan review completed; all blocking findings incorporated.
- [x] Batch 0 failing-contract work completed.
- [x] Owner superseded intermediate pauses and authorized uninterrupted
  production implementation through Batches 1-4.
- [x] Batches 1-4 production implementation and automated verification are
  complete.
- [x] Independent implementation review completed; all findings were fixed and
  the final focused follow-up verdict is APPROVE with no remaining issues.
- [x] Focused browser defect verification completed for modal loaders, manual
  alt editing, Use Image title, AI-alt generation, and saved block data; the
  broader Batch 5 matrix remains incomplete.
- [x] The owner authorized work on the remaining defects and emphasized that
  both metadata and alt generation must show a loader inside their modal.
- [x] No commit has been authorized or created by the agent.
- [x] Owner authorized a summary-only registry upgrade for the new Image AI
  settings, superseding the prior no-upgrades restriction only for this purpose.
  Legacy Image behavior cleanup remains excluded. See PAUSE 12.

Continuation rules:

1. Work through the implementation batches in order.
2. Check an item only after the corresponding edit or verification is complete.
3. At every `PAUSE` checkpoint, stop, summarize exact files and evidence, ask
   the owner whether to continue, and append the evidence to the Execution log
   below before ending the turn.
4. Every execution-log entry must contain repository HEADs, complete dirty-path
   lists, baseline-fingerprint comparison for pre-existing dirty files, files
   changed by the batch, exact commands/results, owner approval with timestamp,
   and the next authorized batch. A chat-only report is not durable evidence.
5. Do not start the next batch until the owner explicitly approves it and that
   approval is recorded in the Execution log.
6. Do not commit. The owner controls commits.
7. Do not start, stop, or restart backend/frontend processes. The owner controls
   processes.
8. Ask before any mutation of a running Plone site, including behavior changes,
   profile runs, catalog changes, content edits, or test fixture changes outside
   isolated automated tests.
9. Never read or expose secrets directly. Use `with-secrets <command>` when a
   command genuinely needs credentials.
10. For non-trivial implementation, retain a separate read-only reviewer before
    finalization.
11. Always run `git diff --check` in every changed repository before finalizing.

## Execution log

Append one entry at every pause. Never rewrite earlier entries except to correct
an explicitly noted transcription error.

### Planning checkpoint — 2026-10-07 EEST

- [x] Owner approved the plan-writing phase; implementation was not authorized.
- [x] Plan-only independent review completed with model `openai-codex/gpt-5.6-sol`.
- [x] Review findings incorporated: decompression-bomb boundary, durable pause
  evidence, transformer ordering, container addability, machine-readable API
  errors, marker scope, dirty-file fingerprints, and frontend i18n.
- [x] Repository HEADs:
  - `eea.genai.summary`: `eb355b612ce281459fbcc9a0d9f15aac96b018ac`
  - `eea.volto.policy`: `0b0574f4f2dc0282b51091b3b7df91d338343c25`
  - frontend: `b6b9d5854642571a588b887e39c3b0cdef431916`
- [x] Dirty paths after plan creation:
  - `eea.genai.summary`: `?? docs/IMAGE_METADATA_UPLOAD_PLAN.md`
  - `eea.volto.policy`: clean
  - frontend: `M jsconfig.json`, `M mrs.developer.json`, `M yarn.lock`,
    `?? cypress/e2e/nested-blocks-copypaste.cy.js`
- [x] Pre-existing unrelated frontend fingerprints (`SHA-256`):

  | Path | Content hash | `git diff --binary` hash |
  | --- | --- | --- |
  | `jsconfig.json` | `f3f4bc3350b1ffa03fcee2402ca1345006636bd5451534203d646b6b4b2c259f` | `bd8ca768c68bd1ec68a615d36e8b5a75b540683839216bea01e05cd95eac886a` |
  | `mrs.developer.json` | `58b7d517f38e8ec28216aa7aed42aa9932a3d81d6b3acb30da9f1d9cdf1b6c52` | `dd8bbe0e39fc556e78ca07bd9be04fa8b38d64d3f874c9b2f60f986f4424ab48` |
  | `yarn.lock` | `6ea71d8680e727dd3c29e5b72b0550caf5139623d184645f2c108275b052e034` | `1c4cf403a6d2434af5b9e0b29690799d749fb8d4014897655f0fd61d24f7b093` |
  | `cypress/e2e/nested-blocks-copypaste.cy.js` | `2383147c272ddabc947872541fe62f5eacf64286cb6c609c2e7f2f01bb546ace` | untracked; not applicable |

- [x] Next authorized action: none. Owner must explicitly authorize Batch 0.

Template for later entries:

```text
### PAUSE N — <timestamp>
- Owner authorization entering batch:
- Repository HEADs:
- Complete dirty paths:
- Unrelated baseline fingerprint comparison:
- Batch-owned files changed:
- Exact commands and results:
- Review/findings/risks:
- Owner approval to continue:
- Next authorized batch:
```

### PAUSE 0 — 2026-10-07 02:19 EEST

- [x] Owner authorization entering batch: owner authorized Batch 0 at
  2026-10-07 01:40 EEST.
- [x] Repository HEADs (unchanged during Batch 0):
  - `eea.genai.summary`: `eb355b612ce281459fbcc9a0d9f15aac96b018ac`
  - `eea.volto.policy`: `0b0574f4f2dc0282b51091b3b7df91d338343c25`
  - outer frontend workspace: `b6b9d5854642571a588b887e39c3b0cdef431916`
  - nested `volto-eea-website-theme`: `c582e639402f2d06df2857babad1dfeee55e9209`
- [x] Complete dirty paths:
  - `eea.genai.summary`: `M eea/genai/summary/tests/test_image.py`,
    `?? docs/IMAGE_METADATA_UPLOAD_PLAN.md`,
    `?? eea/genai/summary/tests/test_image_models.py`,
    `?? eea/genai/summary/tests/test_image_restapi.py`
  - `eea.volto.policy`:
    `?? eea/volto/policy/tests/test_image_blocks.py`
  - outer frontend workspace: `M jsconfig.json`, `M mrs.developer.json`,
    `M yarn.lock`, `?? cypress/e2e/nested-blocks-copypaste.cy.js`
  - nested theme repository:
    `?? src/customizations/volto/components/manage/Blocks/Image/imageAI.test.js`
- [x] Unrelated baseline fingerprint comparison: all four outer-workspace
  fingerprints exactly match the Planning checkpoint, including content and
  tracked-file `git diff --binary` hashes.
- [x] Batch-owned files changed: only the three summary test files, one policy
  test file, one nested-theme test file, and this plan. No production file was
  changed.
- [x] Exact commands and results:
  - Baseline before test edits:
    `../bin/zope-testrunner --test-path eea.genai.summary` equivalent baseline
    ran 98 tests with zero failures/errors/skips; policy baseline ran 57 tests
    with zero failures/errors/skips.
  - `../bin/zope-testrunner --test-path eea.genai.summary`: expected red,
    126 tests, 0 failures, 28 errors; the original 98 tests remained green and
    every error belongs to a new contract awaiting `models.py`, strict image
    APIs/constants, REST service classes, or ZCML registrations.
  - `../bin/zope-testrunner --test-path eea.volto.policy`: expected red,
    67 tests, 0 failures, 12 reported errors (including subtest errors); the
    original 57 tests remained green and errors are missing planned Image block
    transformers/resolver.
  - `CI=true yarn test .../Image/imageAI.test.js --runInBand` from the outer
    frontend workspace: expected red; Jest found the suite and failed because
    planned `./imageAI` does not exist.
  - `../../bin/ruff format --check ...` and `../../bin/ruff check ...` for all
    changed Python tests: pass after formatting.
  - `yarn prettier --check .../Image/imageAI.test.js`: pass.
  - `git diff --check` in summary, policy, outer frontend, and nested theme:
    pass.
  - Earlier `zope-testrunner -s <filesystem-path> -t ...` attempts selected zero
    tests and were discarded as invalid evidence; `--test-path` is the correct
    local invocation.
- [x] Proposed seams established by contracts:
  - summary: `models.py`, strict transient functions/constants in `image.py`,
    `restapi/image.py` service classes, and declarative service permissions;
  - policy: order-0 Image serializer, Image deserializer, and safe internal
    resolver in `restapi/blocks.py`;
  - nested theme: shared `imageAI.js` request/error/state helpers beside the
    customized Image block, with reusable UI extraction during implementation.
- [x] Review/findings/risks:
  - The relevant theme is a nested Git repository on `epanet-and-ai`; the outer
    frontend `develop` repository only supplies the workspace and unrelated
    dirty files. Future evidence must report both worktrees.
  - `plone.restapi.testing` imports unavailable `plone.app.robotframework` in
    this development environment. REST contracts therefore use focused service
    unit tests plus declarative ZCML permission checks; live permissions remain
    scheduled for Batch 5.
  - The owner then requested implementation-first focus and no further test
    expansion for now. Existing Batch 0 tests are retained; production work has
    not started.
- [x] Owner approval to continue: at 2026-10-07 after PAUSE 0, the owner chose
  option 2, explicitly superseding intermediate pauses and authorizing
  implementation through Batches 1-4 before test-focused work.
- [x] Next authorized work: Batches 1-4 production implementation. Do not expand
  or run the test matrix until implementation is complete unless a narrow
  compile/syntax check is required to unblock implementation.

### PAUSE 4 / pre-browser gate — 2026-10-07 08:56 EEST

- [x] Owner authorization entering batches: at PAUSE 0 the owner explicitly
  authorized uninterrupted Batches 1-4 before returning to test-focused work.
- [x] Repository HEADs remain unchanged:
  - `eea.genai.summary`: `eb355b612ce281459fbcc9a0d9f15aac96b018ac`
  - `eea.volto.policy`: `0b0574f4f2dc0282b51091b3b7df91d338343c25`
  - outer frontend workspace: `b6b9d5854642571a588b887e39c3b0cdef431916`
  - nested theme: `c582e639402f2d06df2857babad1dfeee55e9209`
- [x] Complete dirty paths:
  - `eea.genai.summary`: `M README.rst`, `M docs/HISTORY.txt`,
    `M eea/genai/summary/agents.py`, `D eea/genai/summary/catalog.py`,
    `M eea/genai/summary/configure.zcml`, `M eea/genai/summary/generate.py`,
    `M eea/genai/summary/image.py`,
    `D eea/genai/summary/profiles/default/catalog.xml`,
    `M eea/genai/summary/restapi/configure.zcml`,
    `M eea/genai/summary/restapi/post.py`,
    `M eea/genai/summary/setuphandlers.py`,
    `M eea/genai/summary/subscribers.py`,
    `D eea/genai/summary/tests/test_catalog.py`,
    `M eea/genai/summary/tests/test_generate.py`,
    `M eea/genai/summary/tests/test_image.py`,
    `M eea/genai/summary/tests/test_post.py`,
    `M eea/genai/summary/tests/test_subscribers.py`,
    `?? docs/IMAGE_METADATA_UPLOAD_PLAN.md`,
    `?? eea/genai/summary/models.py`,
    `?? eea/genai/summary/restapi/image.py`,
    `?? eea/genai/summary/tests/test_image_models.py`, and
    `?? eea/genai/summary/tests/test_image_restapi.py`.
  - `eea.volto.policy`: `M docs/HISTORY.txt`,
    `M eea/volto/policy/restapi/blocks.py`,
    `M eea/volto/policy/restapi/configure.zcml`, and
    `?? eea/volto/policy/tests/test_image_blocks.py`.
  - outer frontend workspace (all unrelated/pre-existing): `M jsconfig.json`,
    `M mrs.developer.json`, `M yarn.lock`, and
    `?? cypress/e2e/nested-blocks-copypaste.cy.js`.
  - nested theme: `M CHANGELOG.md`, all five `locales/.../volto.po|pot`
    catalogs, ImageAltWidget source/test/style, customized Image Edit/test/View/
    schema, `M src/index.js`, deleted `aiSummary.js` and its test, and new
    `components/manage/ImageAI/` plus `Image/imageAI.js` and its test.
- [x] Unrelated baseline fingerprint comparison: all four outer frontend hashes
  exactly match the Planning checkpoint after tests and two production builds.
- [x] Batches 1-4 delivered:
  - strict in-memory transient image validation and structured marker-free
    `@image-metadata` / `@image-alt` services without persistence;
  - removal of undeployed Image `llm_summary` subscriber/agent/catalog coupling
    while preserving behavior-driven generic summaries;
  - order-0 permission-safe Image-title serialization, lazy provenance, and
    transient-field deserialization;
  - Image-block consent/create/retry flow, live-title/custom/decorative alt
    semantics, plain `@image-alt`, and external-image warning;
  - creation-only Add Image file-widget integration with per-selection consent,
    editable generated metadata, non-AI preservation, and regeneration.
- [x] Exact automated evidence:
  - `../../bin/zope-testrunner --test-path=. -s eea.genai.summary`: 124 tests,
    zero failures/errors/skips after final output/filename validation fixes.
  - `../../bin/zope-testrunner --test-path=. -s eea.volto.policy`: 69 tests,
    zero failures/errors/skips.
  - full nested add-on Jest command with `RAZZLE_JEST_CONFIG`: 68 suites,
    693 tests, and 21 snapshots passed.
  - summary/policy Ruff format and check: pass.
  - nested theme ESLint, Prettier, and Stylelint: pass.
  - nested theme `make i18n`: pass; all new strings extracted into POT/PO
    catalogs.
  - outer frontend `yarn build`: client and server production builds pass.
  - outer `yarn typecheck`: blocked by pre-existing malformed generated files in
    unrelated `src/addons/volto-columns-block`; no touched-file error reported.
  - `git diff --check` passed in all four worktrees before this log append and
    must be rerun after it.
- [x] Independent review and fixes:
  - initial verdict BLOCK identified marker/plain-sentence validation, empty
    custom-alt fallback, cancellability during analysis, stale AI-alt loading,
    and integration-test gaps;
  - fixes add strict plain/sentence validators, correct effective-alt fallback,
    cancellable analysis with request invalidation, request-keyed alt loading,
    positive resolver tests, all supported-format/EXIF tests, and modal tests;
  - no-permission serialization also strips any stale persisted `image_title`;
  - first follow-up found remaining label/markdown/filename-derived-title gaps;
    validators and atomic filename-title retry were hardened and retested;
  - final follow-up verdict: APPROVE, no remaining P0/P1/P2 findings; live
    browser/API verification remains pending evidence rather than a code defect.
- [x] No processes were started/stopped, no live site was mutated, no secrets
  were read, and no commit was created.
- [ ] Owner approval to continue: waiting for the owner to start/confirm services,
  authorize disposable development-site mutation, and provide the test location
  before Playwright/API verification.
- [ ] Next authorized batch: none until that confirmation.

### Remaining-defect follow-up / PAUSE 5 — 2026-10-07 15:40 EEST

- [x] Owner authorization entering work: the owner instructed the agent to
  start fixing the remaining issues and explicitly required visible progress
  inside the modal when metadata or alt generation is triggered. The prior
  disposable-site/Playwright authorization remained in effect. No commit was
  authorized.
- [x] Repository HEADs remain unchanged:
  - `eea.genai.summary`: `eb355b612ce281459fbcc9a0d9f15aac96b018ac`
  - `eea.volto.policy`: `0b0574f4f2dc0282b51091b3b7df91d338343c25`
  - outer frontend workspace: `b6b9d5854642571a588b887e39c3b0cdef431916`
  - nested theme: `c582e639402f2d06df2857babad1dfeee55e9209`
- [x] Complete dirty paths at this pause:
  - `eea.genai.summary`: `M README.rst`, `M docs/HISTORY.txt`,
    `M eea/genai/summary/agents.py`, `D eea/genai/summary/catalog.py`,
    `M eea/genai/summary/configure.zcml`, `M eea/genai/summary/generate.py`,
    `M eea/genai/summary/image.py`,
    `D eea/genai/summary/profiles/default/catalog.xml`,
    `M eea/genai/summary/profiles/default/metadata.xml`,
    `M eea/genai/summary/restapi/configure.zcml`,
    `M eea/genai/summary/restapi/post.py`,
    `M eea/genai/summary/setuphandlers.py`,
    `M eea/genai/summary/subscribers.py`,
    `D eea/genai/summary/tests/test_catalog.py`,
    `M eea/genai/summary/tests/test_generate.py`,
    `M eea/genai/summary/tests/test_image.py`,
    `M eea/genai/summary/tests/test_post.py`,
    `M eea/genai/summary/tests/test_subscribers.py`,
    `?? docs/IMAGE_METADATA_UPLOAD_PLAN.md`,
    `?? eea/genai/summary/models.py`,
    `?? eea/genai/summary/restapi/image.py`,
    `?? eea/genai/summary/tests/test_image_models.py`,
    `?? eea/genai/summary/tests/test_image_restapi.py`,
    `?? eea/genai/summary/tests/test_upgrades.py`, and
    `?? eea/genai/summary/upgrades/`.
  - `eea.volto.policy`: `M docs/HISTORY.txt`,
    `M eea/volto/policy/restapi/blocks.py`,
    `M eea/volto/policy/restapi/configure.zcml`, and
    `?? eea/volto/policy/tests/test_image_blocks.py`.
  - outer frontend workspace, all unrelated/pre-existing: `M jsconfig.json`,
    `M mrs.developer.json`, `M yarn.lock`, and
    `?? cypress/e2e/nested-blocks-copypaste.cy.js`.
  - nested theme: `M CHANGELOG.md`,
    `M locales/de/LC_MESSAGES/volto.po`,
    `M locales/en/LC_MESSAGES/volto.po`,
    `M locales/it/LC_MESSAGES/volto.po`,
    `M locales/ro/LC_MESSAGES/volto.po`, `M locales/volto.pot`,
    `M src/components/theme/Widgets/ImageAltWidget.jsx`,
    `M src/components/theme/Widgets/ImageAltWidget.test.jsx`,
    `M src/components/theme/Widgets/imageAltWidget.less`,
    `M src/customizations/volto/components/manage/Blocks/Image/Edit.jsx`,
    `M src/customizations/volto/components/manage/Blocks/Image/Edit.test.jsx`,
    `M src/customizations/volto/components/manage/Blocks/Image/View.jsx`,
    deleted `Image/aiSummary.js` and `Image/aiSummary.test.js`,
    `M src/customizations/volto/components/manage/Blocks/Image/schema.js`,
    `M src/index.js`, `?? src/components/manage/ImageAI/`,
    `?? Image/ImageSidebar.jsx`, `?? Image/ImageSidebar.test.jsx`,
    `?? Image/imageAI.js`, `?? Image/imageAI.test.js`, and
    `?? Image/schema.test.js`, where the abbreviated `Image/` paths are under
    `src/customizations/volto/components/manage/Blocks/Image/`.
- [x] Unrelated outer-workspace fingerprint comparison: all four fingerprints
  remain byte-for-byte identical to the Planning checkpoint. No unrelated
  frontend file was altered.
- [x] Root-cause evidence before editing:
  - metadata-modal loader pseudo-elements were white on a white modal
    (`::before rgba(255,255,255,0.15)`, `::after rgb(255,255,255)`);
  - entering `Custom bird alt` immediately reverted to the Image title;
  - `@image-alt` returned HTTP 200 with a valid `alt`, but the field remained
    unchanged;
  - the stock ImageSidebar spread render-time `data` for each field write, so
    the same-tick `alt_source` write replaced the preceding `alt` write;
  - the browser reported the invalid JSX `description` passed to
    `TextareaWidget`;
  - the live Image schema still exposed `allow_llm_summary` and `llm_summary`.
- [x] Defect fixes implemented:
  - shared high-contrast `image-ai-progress-modal` loader styling is scoped to
    the metadata consent modal and the AI-alt confirmation modal;
  - initial Generate AI alt opens a progress modal immediately; custom-alt
    Regenerate keeps its confirmation open and switches it to
    `Generating AI alt…` until the request finishes;
  - a theme ImageSidebar override accumulates consecutive field updates through
    a current-data ref before invoking `onChangeBlock`;
  - the alt hint is now translated plain text, satisfying TextareaWidget's
    string prop contract;
  - profile 1.0 -> 2.0 adds an idempotent GenericSetup upgrade that removes only
    `eea.genai.summary` from the Image FTI, retains every other behavior, emits
    the Dexterity FTI modification event, and intentionally leaves old object
    attributes intact but inactive.
- [x] Exact automated evidence:
  - focused red/green tests demonstrated the modal style hook, consecutive
    sidebar updates, string schema description, alt-modal progress state, and
    profile upgrade contracts;
  - full summary suite:
    `../../bin/zope-testrunner --test-path=. -s eea.genai.summary ...` —
    129 tests, zero failures/errors/skips;
  - full policy suite:
    `../../bin/zope-testrunner --test-path=. -s eea.volto.policy ...` —
    69 tests, zero failures/errors/skips;
  - full nested-theme suite with `RAZZLE_JEST_CONFIG` — 70 suites, 697 tests,
    and 21 snapshots passed;
  - nested-theme `make i18n`, `make lint`, `make prettier`, and
    `make stylelint` passed;
  - summary Ruff format/check passed for 27 Python files;
  - outer frontend `yarn build` compiled both production bundles successfully;
  - `git diff --check` passed in summary, policy, outer frontend, and nested
    theme after the final plan update; unrelated fingerprints remained exact.
- [x] Browser evidence:
  - metadata modal loader: visible and animated, text
    `rgba(0,0,0,0.87)`, track `rgba(0,0,0,0.1)`, spinner `rgb(118,118,118)`;
  - initial Generate AI alt opened a modal headed `Generate AI alt` and showed
    the same visible high-contrast `Generating AI alt…` spinner while the
    request ran; custom-alt Regenerate retained its confirmation modal and then
    showed the same progress state;
  - manual input remained `Custom bird alt`; Use Image title changed it to the
    live title;
  - a real `@image-alt` HTTP 200 result populated the field and, after Save,
    persisted block JSON containing the generated `alt`,
    `alt_source: "custom"`, `decorative: false`, and the expected Image URL and
    title;
  - a fresh browser tab no longer reported the TextareaWidget description
    warning. Unrelated pre-existing Route, CSP/Matomo, TextWidget, Redux local
    storage, and lifecycle warnings remain.
- [x] Live-site notes: timing verification created the disposable child
  `/en/image-ai-verification/test-sunset-bird-1.jpg`; it was left untouched.
  The verification page now contains the saved generated-alt image block. The
  live Image FTI was not changed and the new profile upgrade was not run.
- [x] Independent fresh-context review verdict: APPROVE. The reviewer
  confirmed both modal loaders, accumulating block updates, saved-alt path,
  string description, and the scoped idempotent FTI upgrade. Browser
  save/reload was listed as a missing automated test but was covered manually.
  A final focused review of initial Generate versus confirmed Regenerate also
  returned APPROVE with no functional issue. Its only P2 test-coverage note was
  addressed by asserting that the progress modal closes after success, error,
  and stale-source cancellation; the focused 11-test suite remained green.
- [x] No process was started/stopped or restarted, no secrets were read, and no
  commit was created.
- [ ] Owner action still required: after deployment/restart, run the
  `eea.genai.summary` 1.0 -> 2.0 profile upgrade. Decide whether to delete the
  disposable `test-sunset-bird-1.jpg` child.

### Upgrade-step correction / PAUSE 6 — 2026-10-07

- [x] The owner reiterated the existing explicit constraint: do not add an
  `eea.genai.summary` upgrade step.
- [x] The agent had incorrectly treated the stale behavior on the running
  development Image FTI as authorization to add a migration, despite this plan
  already stating both "no GenericSetup upgrade step" and "add no profile
  upgrade." That inference was wrong.
- [x] The unauthorized upgrade work was removed completely:
  - deleted `eea/genai/summary/upgrades/` and
    `eea/genai/summary/tests/test_upgrades.py`;
  - removed the upgrades ZCML include;
  - restored the default profile version to `1.0`;
  - removed the upgrade entry from `docs/HISTORY.txt`.
- [x] No replacement migration or live FTI mutation was added. Current source
  does not assign the summary behavior to Image; the pre-existing assignment on
  the running development site remains untouched and out of scope.
- [x] Post-correction verification: all 124 `eea.genai.summary` tests passed;
  Ruff format and lint passed for 24 Python files; no upgrade source/reference
  remains outside this historical/correction log.
- [x] This entry supersedes every upgrade implementation or owner-action claim
  in PAUSE 5. No commit was created.

### Metadata-request cancellation fix / PAUSE 7 — 2026-10-07

- [x] Owner-reported defect: closing the metadata progress modal hid the modal
  but left the browser's `@image-metadata` request pending.
- [x] Deterministic red tests reproduced the exact defect in both production
  consumers: Add Image's `ImageAddFileWidget` and the Image block upload flow.
  In each case the modal close icon invoked cancellation but the mocked
  transport's `abort()` call count remained zero across repeated runs.
- [x] Root cause: cancellation only invalidated request IDs and reset UI state.
  Volto's `Api.post()` returns a Promise carrying its SuperAgent request as
  `.request`, but `requestImageMetadata()` was declared `async`; that wrapper
  Promise discarded the transport handle, so consumers could not abort it.
- [x] Fix:
  - `requestImageMetadata()` now returns the original API Promise unchanged;
  - `abortImageAIRequest()` encapsulates the transport abort operation;
  - both metadata consumers retain the active request and abort it when the
    modal is canceled or the component unmounts;
  - request identity guards prevent an abort rejection or stale response from
    changing state after cancellation.
- [x] Regression evidence:
  - focused Add Image suite: 9 tests passed;
  - focused Image Edit suite: 19 tests passed;
  - full nested-theme suite: 70 suites, 699 tests, 21 snapshots passed;
  - nested-theme lint, Prettier, and Stylelint passed;
  - production client/server build passed;
  - outer and nested-theme `git diff --check` passed; unrelated frontend
    fingerprints remained exact.
- [x] Browser evidence: Playwright paused a real browser
  `/@image-metadata` request, clicked the modal close icon during
  `Analyzing image…`, and observed `requestfailed` with
  `net::ERR_ABORTED`; the modal closed and the Add Image form was canceled
  without creating content.
- [x] Scope note: this guarantees termination of the browser-side pending HTTP
  request. If a provider call has already started server-side, cancellation of
  that separate upstream operation depends on server/provider disconnect
  propagation and is not claimed here.
- [x] No commit was created.

### Initial AI-alt generation UX / PAUSE 8 — 2026-10-07

- [x] Owner clarified the desired split between the two AI-alt actions:
  - initial **Generate AI alt** must run immediately, show loading in its own
    button, and disable the Alt field;
  - the confirmation/progress modal is reserved for **Regenerate AI alt**,
    where existing custom alt text would be overwritten.
- [x] A regression test was changed first and failed against the old behavior:
  initial generation rendered two `Generate AI alt` controls because the
  progress modal opened while the action button was also loading.
- [x] `ImageAltWidget` now calls initial generation directly without opening
  the modal and includes `loading` in the Alt field's disabled state.
  Regeneration still opens the confirmation modal, sends no request before
  confirmation, shows its existing centered modal loader after confirmation,
  and closes on completion/error/stale-image handling as previously tested.
- [x] Focused ImageAltWidget suite: 11 tests passed.
- [x] Full nested-theme suite: 70 suites, 699 tests, 21 snapshots passed.
- [x] Nested-theme lint, Prettier, and Stylelint passed; the production
  client/server build passed; tracked and untracked plan whitespace checks
  passed.
- [x] Browser evidence with a deliberately paused `@image-alt` request:
  - initial Generate showed Semantic UI's `loading` and `disabled` button
    states, disabled the Alt textarea, and rendered zero AI-alt modals;
  - entering temporary custom alt text changed the action to Regenerate;
    pressing it displayed `Regenerate AI alt?`, sent zero requests before
    confirmation, and Cancel closed the modal;
  - the edit session was canceled, so temporary browser data was not saved.
- [x] Unrelated frontend dirty-file fingerprints remained exact.
- [x] No commit was created.

### Volto Toast integration correction / PAUSE 9 — 2026-10-07

- [x] Owner identified that the new AI notifications passed plain strings to
  React Toastify instead of rendering Volto's standard Toast component.
- [x] Upstream source verification in the installed Volto package confirmed
  the contract:
  - callers import `Toast` from
    `@plone/volto/components/manage/Toast/Toast`;
  - `toast.success/error/...` receives `<Toast ... />` with a semantic status
    prop plus localized `title` and required `content`;
  - the Toast component supplies the matching icon and accessible type label.
- [x] Red tests first proved that the success, warning, and error calls in both
  AI widgets received strings (`notification.type` was undefined).
- [x] Corrected every raw AI toast in:
  - `volto-eea-website-theme` `ImageAltWidget`;
  - `volto-genai-blocks` `LLMSummaryWidget`.
  Success, warning, and error notifications now use Volto Toast with localized
  `Success`/`Warning`/`Error` titles and the existing localized result message
  as content.
- [x] A complete source scan confirmed that every toast call in both add-ons
  now receives `<Toast ... />`; pre-existing theme toast calls already followed
  the upstream pattern.
- [x] i18n extraction succeeded in both add-ons, updating POT and all existing
  de/en/it/ro PO catalogs. The theme extraction also captured the complete set
  of previously added Image AI messages from the current uncommitted work.
- [x] Verification:
  - focused ImageAltWidget: 12 tests passed;
  - full theme: 70 suites, 700 tests, 21 snapshots passed;
  - focused LLMSummaryWidget: 6 tests passed;
  - full volto-genai-blocks: 3 suites, 18 tests passed;
  - lint, Prettier, and Stylelint passed in both add-ons;
  - the combined production client/server build passed;
  - outer frontend, nested theme, and volto-genai-blocks `git diff --check`
    passed.
- [x] Browser evidence: a mocked successful `@image-alt` response rendered a
  visible `Toastify__toast--success` containing title `Success`, content
  `AI alt generated`, and the generated Alt value; the edit session was then
  canceled without saving the temporary value.
- [x] Unrelated outer frontend dirty-file fingerprints remained exact.
- [x] No commit was created.

### Import and customization cleanup / PAUSE 10 — 2026-10-14 10:56 EEST

- Owner authorization: the current request approved the proposed cleanup with
  one exception: delete `schema.test.js` entirely instead of relocating it.
  Sibling `./...` imports remain permitted; upward-relative imports do not.
- Batch changes in `volto-eea-website-theme`:
  - moved `imageAI.js` and `imageAI.test.js` from the Image customization
    directory into `src/helpers/`;
  - updated the helper's `toApiPath` import to sibling `./toApiPath`;
  - changed the cross-directory imports in ImageAltWidget, its test mock,
    ImageAddFileWidget, Image Edit, and Image View to the theme alias;
  - renamed the Image schema from `schema.js` to `schema.jsx`, matching the
    installed Volto core file;
  - deleted the untracked Image `schema.test.js` as requested.
- No functional logic was changed by this batch. No changes were required in
  `volto-genai-blocks` because its affected files only use permitted sibling
  imports.
- Exact validation and results:
  - outer workspace command:
    `RAZZLE_JEST_CONFIG=src/addons/volto-eea-website-theme/jest-addon.config.js CI=true yarn test src/addons/volto-eea-website-theme/src --watchAll=false --runInBand --silent`:
    **not green**, 68 suites passed, 1 failed; 697 tests passed, 1 failed;
    21 snapshots passed. The failing ImageAltWidget test expects decorative
    mode to disable the textarea, while the current widget no longer applies
    decorative-mode behavior. This separate mismatch was left untouched.
    Log: `/tmp/image-ai-import-tests.log`.
  - theme `make lint && make prettier && make stylelint`: passed;
  - outer workspace `yarn build`: client/server build passed;
    log: `/tmp/image-ai-import-build.log`;
  - source scan of the Image AI files: zero upward-relative imports, both
    helper files present under helpers, and no Image schema test remaining;
  - outer frontend and theme `git diff --check`: passed;
  - all four unrelated outer frontend content hashes exactly matched the
    recorded baseline. No commits, process changes, or live-site edits.
- Repository HEADs remained unchanged:
  - summary: `eb355b612ce281459fbcc9a0d9f15aac96b018ac`;
  - policy: `0b0574f4f2dc0282b51091b3b7df91d338343c25`;
  - outer frontend: `b6b9d5854642571a588b887e39c3b0cdef431916`;
  - theme: `c582e639402f2d06df2857babad1dfeee55e9209`;
  - genai-blocks: `16e215613c362d0a025cbfb26834eec705d8d3f4`.
- Theme dirty paths at this checkpoint:
  `CHANGELOG.md`, `locales/{de,en,it,ro}/LC_MESSAGES/volto.po`,
  `locales/volto.pot`,
  `src/components/theme/Widgets/{ImageAltWidget.jsx,ImageAltWidget.test.jsx,imageAltWidget.less}`,
  `src/customizations/volto/components/manage/Blocks/Image/{Edit.jsx,Edit.test.jsx,View.jsx}`,
  deleted `src/customizations/volto/components/manage/Blocks/Image/{aiSummary.js,aiSummary.test.js,schema.js}`,
  `src/index.js`, new `src/components/manage/ImageAI/`,
  new `src/customizations/volto/components/manage/Blocks/Image/{ImageSidebar.jsx,ImageSidebar.test.jsx,schema.jsx}`,
  new `src/helpers/{imageAI.js,imageAI.test.js}`.
- Next authorized batch: none. Owner should clarify the separate
  decorative-mode implementation/test mismatch before any behavior change.

### GenAI settings and SSR capability gating / PAUSE 11 — 2026-10-14 13:24 EEST

- Owner authorization: approved implementation after agreeing that Image AI
  defaults disabled; title and alt share a maximum of 64 characters; description
  retains 500; oversized output retries once, then fails without truncation.
  Owner explicitly required the header-settings SSR extender pattern and accepted
  full page loads for frontend settings refresh. No live-site or process mutation
  was authorized. The decorative toggle was removed by the owner.
- Implemented:
  - core `IGenAISettingsSection` named utilities registered through ordinary ZCML;
    both controlpanels compose package schemas using the existing core registry
    prefix, preserve existing keys, and reject duplicate field names;
  - summary contributes the Image AI fieldset and installs its own records in
    `registry.xml`; runtime fallback values are disabled, 64, and 500;
  - public root `GET @genai-settings` exposes only the master flag and explicit
    package feature payloads, not administrative model/prompt/MCP configuration;
  - theme action and `genAISettingsExtender` load flags before SSR rendering into
    `state.reduxAsyncConnect.genAISettings`, reused by Image Add, Image block upload,
    and Image Alt widgets. No dedicated reducer, per-widget fetching, client
    refresh, or process-global configuration writes;
  - both switches gate generation; ordinary upload, manual fields, linked-title
    inheritance and Use Image title remain available. Missing/error flags fail
    closed. Request handlers protect against stale application after disabling;
  - REST and direct Image generation enforce current backend settings and return
    stable HTTP 403 `image_ai_disabled` errors when disabled;
  - runtime character limits affect prompts and returned trimmed text. Metadata
    retries atomically; filename-title and length failures share one retry budget.
    Invalid second results fail without truncation. Structural models retain
    plain-text/sentence checks without overriding configurable lengths;
  - removed the stale decorative widget test and leftover decorative schema
    checkbox/messages. `schema.test.js` remains deleted; no toggle was restored;
  - README/HISTORY/architecture/changelog documentation and core ADR 001 added.
- Complete dirty paths at checkpoint (including pre-existing work):
  - core: `M ARCHITECTURE.md`, `M README.rst`, `M docs/HISTORY.txt`,
    `M eea/genai/core/browser/controlpanel.py`, `M eea/genai/core/interfaces.py`,
    `M eea/genai/core/restapi/configure.zcml`,
    `M eea/genai/core/restapi/controlpanel.py`, `M eea/genai/core/settings.py`,
    `?? docs/ADR-001-settings-sections.md`, `?? eea/genai/core/restapi/settings.py`,
    `?? eea/genai/core/tests/test_settings_sections.py`;
  - summary: `M README.rst`, `M docs/HISTORY.txt`,
    `M eea/genai/summary/{agents.py,configure.zcml,generate.py,image.py,interfaces.py,setuphandlers.py,subscribers.py}`,
    `D eea/genai/summary/catalog.py`, `D eea/genai/summary/profiles/default/catalog.xml`,
    `M eea/genai/summary/restapi/{configure.zcml,post.py}`,
    `D eea/genai/summary/tests/test_catalog.py`,
    `M eea/genai/summary/tests/{test_generate.py,test_image.py,test_post.py,test_subscribers.py}`,
    `?? docs/IMAGE_METADATA_UPLOAD_PLAN.md`, `?? eea/genai/summary/models.py`,
    `?? eea/genai/summary/profiles/default/registry.xml`,
    `?? eea/genai/summary/restapi/image.py`, `?? eea/genai/summary/settings.py`,
    `?? eea/genai/summary/tests/{test_image_generation_limits.py,test_image_models.py,test_image_restapi.py,test_image_settings.py}`;
  - policy (untouched by this batch): `M docs/HISTORY.txt`,
    `M eea/volto/policy/restapi/{blocks.py,configure.zcml}`,
    `?? eea/volto/policy/tests/test_image_blocks.py`;
  - outer frontend (untouched): `M jsconfig.json`, `M mrs.developer.json`,
    `M yarn.lock`, `?? cypress/e2e/nested-blocks-copypaste.cy.js`;
  - theme: `M CHANGELOG.md`, `M locales/{de,en,it,ro}/LC_MESSAGES/volto.po`,
    `M locales/volto.pot`, `M src/actions/index.js`,
    `M src/components/theme/Widgets/{ImageAltWidget.jsx,ImageAltWidget.test.jsx,imageAltWidget.less}`,
    `M src/constants/ActionTypes.js`,
    `M src/customizations/volto/components/manage/Blocks/Image/{Edit.jsx,Edit.test.jsx,View.jsx}`,
    `D src/customizations/volto/components/manage/Blocks/Image/{aiSummary.js,aiSummary.test.js,schema.js}`,
    `M src/index.js`, `?? src/actions/genai-settings.js`,
    `?? src/components/manage/ImageAI/{ImageAddFileWidget.jsx,ImageAddFileWidget.test.jsx,ImageMetadataConsentModal.jsx,ImageMetadataConsentModal.test.jsx,imageAIModal.less}`,
    `?? src/customizations/volto/components/manage/Blocks/Image/{ImageSidebar.jsx,ImageSidebar.test.jsx,schema.jsx}`,
    `?? src/helpers/{genAISettings.js,genAISettingsExtender.js,genAISettingsExtender.test.js,imageAI.js,imageAI.test.js}`;
  - genai-blocks (untouched): `M locales/{de,en,it,ro}/LC_MESSAGES/volto.po`,
    `M locales/volto.pot`, `M src/{LLMSummaryWidget.jsx,LLMSummaryWidget.test.jsx}`;
  - chatbot unrelated dirty files untouched:
    `jest-addon.config.js`, `src/ChatBlock/chat/AIMessage.tsx`,
    `src/ChatBlock/components/markdown/{Citation.jsx,index.jsx}`,
    `src/ChatBlock/packets/renderers/{MessageTextRenderer.tsx,ReasoningRenderer.tsx}`,
    `src/ChatBlock/tests/{Citation.test.jsx,citations.test.js,markdownComponents.test.jsx}`,
    `src/ChatBlock/utils/citations.ts`.
- Batch-owned files are the new core extension/public service/tests/docs,
  summary settings/schema/registry/generation/service/tests/docs listed above,
  and theme action/constants/extender/selector/index, affected widget/Edit tests,
  Image schema checkbox removal, catalogs and changelog. Other dirty paths were
  not changed by this batch.
- Exact validation and results:
  - red tests established separately for core settings contribution, summary
    defaults, disabled endpoint guards, runtime limits, SSR loading, and all
    three frontend consumers before their respective implementations;
  - from each backend package:
    `../../bin/zope-testrunner --test-path=. -s <package> --no-color --no-progress`:
    core **26 passed**, summary **134 passed**, zero failures/errors/skips;
  - outer frontend:
    `RAZZLE_JEST_CONFIG=src/addons/volto-eea-website-theme/jest-addon.config.js CI=true yarn test src/addons/volto-eea-website-theme/src --watchAll=false --runInBand --silent`:
    **70 suites / 713 tests / 21 snapshots passed**;
  - SSR regression exercises real Volto `loadOnServer`, asyncConnect reducer and
    server markup rendering, confirms loaded flags before render, preservation
    on client navigation without refetching, and safe SSR behavior on GET failure;
  - summary regression exercises real Plone autoform grouping for the contributed
    Image AI fieldset;
  - theme `make lint`, `make prettier`, `make stylelint`, and `make i18n`: passed;
    initial Prettier-only findings were corrected with the explicit binary from
    theme cwd. Formatter-only changes outside the changelog's Unreleased entry
    were reversed, preserving the existing release history;
  - `../bin/ruff check` and `../bin/ruff format --check` on both backend package
    trees: passed, **46 files formatted**;
  - outer frontend `yarn build`: client and server compiled successfully;
  - tracked `git diff --check` in all recorded repositories and no-index whitespace
    checks for all untracked files in changed repositories: passed;
  - all four unrelated outer frontend content hashes match both the start of this
    batch and the Planning checkpoint. No claim is made about historical diff
    hashes from different Git invocation/configuration contexts.
- Evidence logs: `/tmp/genai-settings-{core-tests,summary-final,theme-final,build,i18n}.log`.
- Independent fresh-context read-only reviewer: **APPROVE, no issues found**.
  Artifact: `/tmp/genai-image-settings-review.md`; run
  `5a26a2eb-0fb3-45b7-8c21-f92d183d39b8`. It inspected installed registry,
  autoform and REST semantics; tests were run by the parent. Nested-repository
  attribution used explicit diffs because watchdog_diff targeted a different root.
- Repository HEADs unchanged during this batch:
  - core: `ac7caf31db52c894df53e1aa89d06b6b19a66e4c`;
  - summary: `eb355b612ce281459fbcc9a0d9f15aac96b018ac`;
  - policy: `0b0574f4f2dc0282b51091b3b7df91d338343c25`;
  - outer frontend: `b6b9d5854642571a588b887e39c3b0cdef431916`;
  - theme: `c582e639402f2d06df2857babad1dfeee55e9209`;
  - genai-blocks: `16e215613c362d0a025cbfb26834eec705d8d3f4`.
- Remaining owner action: deploy/restart backend and import the **registry step**
  of `profile-eea.genai.summary:default` before opening the expanded controlpanel.
  New records are required by the standard registry controlpanel proxy. Enable
  both switches and fully reload the frontend for live verification. No live
  verification of this feature batch was performed against stale processes.
- No upgrades, profile version bumps, live-site changes, process restarts or
  commits were performed. Next authorized batch: none beyond completed work;
  deployment and live verification require owner approval.

### Summary-only Image settings upgrade / PAUSE 12 — 2026-10-14 EEST

- Owner approval: explicitly authorized adding the missing-record upgrade and
  confirmed it belongs only in `eea.genai.summary`, not `eea.genai.core`.
  This supersedes the earlier no-upgrades restriction **only** for installing
  Image AI registry records. It does not authorize legacy Image FTI cleanup,
  commits, process changes, or execution of an upgrade on the running site.
- Baseline changed since PAUSE 11: owner committed the previous implementation.
  Summary was clean at `025b386fe7395ddbb0a355b7457cf156114833c4`; core was clean
  at `ad5a1fde20727ca21257c39c0d832d17d7108fad`. Both HEADs remain unchanged during
  this upgrade task. There were no pre-existing dirty summary paths to preserve.
  Core remains completely clean; frontend and policy repositories were untouched.
- Implemented a GenericSetup summary profile **1.0 → 2.0** upgrade named
  “Install Image AI settings”. Handler imports only `plone.app.registry` from
  `profile-eea.genai.summary:default`, explicitly setting `run_dependencies=False`
  and `purge_old=False`. Existing `registry.xml` registers the package-owned schema
  under the shared prefix without value overrides, preserving valid configured
  values and filling missing records. No core upgrade is required because core's
  existing registry fields and keys are unchanged.
- Complete dirty paths, all owned by this task, within `eea.genai.summary`:
  - `M README.rst`;
  - `M docs/HISTORY.txt`;
  - `M docs/IMAGE_METADATA_UPLOAD_PLAN.md`;
  - `M eea/genai/summary/configure.zcml`;
  - `M eea/genai/summary/profiles/default/metadata.xml`;
  - `?? eea/genai/summary/tests/test_upgrades.py`;
  - `?? eea/genai/summary/upgrades/__init__.py`;
  - `?? eea/genai/summary/upgrades/configure.zcml`.
- Verification:
  - dependency-free red/green wiring harness:
    `python3 /tmp/test-summary-upgrade-contract.py` initially failed with one
    missing-handler error and one missing-include assertion, then passed both
    tests after implementation. This was a narrow wiring check, not a substitute
    for Plone verification;
  - the backend environment initially could not import `zope`, later could load
    Plone but lacked `pydantic`/`pydantic_ai` and editable package discovery. No
    dependency installation was performed by the agent. The environment became
    available again during this task, and verification was completed;
  - from `eea.genai.summary`, with explicit source paths:
    `PYTHONPATH="$PWD:$PWD/../eea.genai.core${PYTHONPATH:+:$PYTHONPATH}" ../../bin/zope-testrunner --test-path=. -s eea.genai.summary -m test_upgrades --no-color --no-progress`:
    **6 passed**, zero failures/errors/skips. Covers actual registry import,
    disabled/64/500 defaults, preservation of core and Image settings,
    idempotence, partial-record repair, the composed proxy's original missing
    `image_ai_enabled` error before upgrade and successful access after upgrade,
    profile-version/include consistency, and actual executable ZCML registration
    in isolated GenericSetup upgrade storage;
  - same command without `-m test_upgrades`: full summary package
    **140 passed**, zero failures/errors/skips;
  - `ruff check eea.genai.summary/eea/genai/summary` and
    `ruff format --check eea.genai.summary/eea/genai/summary`: passed,
    **27 Python files**;
  - tracked and untracked whitespace checks passed. Core status remains clean.
- Independent fresh-context reviewer: **APPROVE, no issues found**, run
  `8f2b3583-fc43-46d1-9153-a6671a9c208e`, artifact
  `/tmp/genai-summary-registry-upgrade-review.md`. Its initial runtime-blocker
  notes were subsequently resolved by the parent with the focused/full passing
  runs above. A test-only executable ZCML check was added after review; no
  production code was changed after that review.
- Evidence: `/tmp/genai-summary-upgrade-{focused,full}.log`,
  `/tmp/genai-summary-upgrade-unittest.log`,
  `/tmp/genai-summary-registry-upgrade-review.diff`.
- Remaining owner action: deploy/restart and run the summary profile upgrade
  **1.0 → 2.0**, then reload the GenAI controlpanel. This replaces PAUSE 11's
  manual registry-import workaround; no core profile upgrade is needed.
- No running-site mutation, process restart, dependency installation, or commit
  was performed. Next authorized batch: none beyond the completed summary
  upgrade; live execution requires owner approval.

## Repository scope and baseline

### 1. `eea.genai.summary`

Path:

```text
/Users/razvan/Work/eea-website-backend/develop/sources/eea.genai.summary
```

Baseline at planning time:

- [x] Branch `develop`, tracking `origin/develop`.
- [x] Planning HEAD: `eb355b612ce281459fbcc9a0d9f15aac96b018ac`.
- [x] Clean worktree before this plan was added.
- [x] Current baseline includes commit `c540a46`, the previous automatic Image
  `llm_summary` implementation.

Responsibilities after this change:

- generic `ILLMSummary` behavior and summary workflows;
- stateless pre-creation `@image-metadata` endpoint;
- non-persisting existing-Image `@image-alt` endpoint;
- multimodal image normalization and model input;
- structured output validation for Image metadata and alt text.

### 2. `eea.volto.policy`

Path:

```text
/Users/razvan/Work/eea-website-backend/develop/sources/eea.volto.policy
```

Baseline at planning time:

- [x] Branch `develop`, tracking `origin/develop`.
- [x] Planning HEAD: `0b0574f4f2dc0282b51091b3b7df91d338343c25`.
- [x] Clean worktree.
- [x] Existing block serializer/deserializer policy is in
  `eea/volto/policy/restapi/blocks.py` and registered from
  `eea/volto/policy/restapi/configure.zcml`.

Responsibilities after this change:

- resolve the linked internal Image for an image block;
- expose the permission-safe live Image title as transient `image_title`;
- infer/normalize legacy `alt_source` values;
- remove transient `image_title` before block persistence.

### 3. frontend workspace and nested theme repository

Paths:

```text
/Users/razvan/Work/eea-website-frontend
/Users/razvan/Work/eea-website-frontend/src/addons/volto-eea-website-theme
```

Baseline confirmed during Batch 0:

- [x] The outer workspace is branch `develop`, tracking `origin/develop`, at
  `b6b9d5854642571a588b887e39c3b0cdef431916`.
- [x] The implementation target is a nested Git repository on branch
  `epanet-and-ai`, tracking `origin/epanet-and-ai`, at
  `c582e639402f2d06df2857babad1dfeee55e9209`.
- [x] Existing AI-alt feature commit `631999c` is in the nested theme ancestry
  through merge `c582e63`.
- [x] The following outer-workspace changes were already present and are
  unrelated to this plan; do not alter, revert, stage, or include them
  accidentally:
  - `jsconfig.json`
  - `mrs.developer.json`
  - `yarn.lock`
  - `cypress/e2e/nested-blocks-copypaste.cy.js` (untracked)
- [x] Report status, HEAD, and diffs for both frontend Git worktrees at every
  pause; theme implementation files belong to the nested repository.

Responsibilities after this change:

- shared opt-in modal and image-analysis client;
- Image block upload orchestration;
- Add Image form file-selection orchestration;
- live-title/custom/decorative block alt state;
- Generate/Regenerate block-local AI alt controls;
- accessibility warnings and translated UI strings.

### 4. Out of scope

- [x] `eea.genai.core` will not own Image-specific endpoints or workflows.
- [x] No new `eea.genai.image` distribution will be introduced.
- [x] No persistent temporary upload object, blob, filesystem file, or cache will
  be introduced for metadata preflight.
- [x] No Image `llm_summary` data migration or cleanup will be implemented.
- [x] No block content migration or GenericSetup upgrade step will be
  implemented.
- [x] No AI metadata UI will be added to editing an already-created Image in
  this iteration.
- [x] No AI opt-in flow will be added to bulk folder upload, Contents drag/drop,
  TUS clients, or arbitrary API clients.
- [x] No page/block context text will be sent to `@image-alt`; only an explicit
  page language code may accompany the request.

## Problem statement

The previous implementation made Image content objects participate in
`ILLMSummary`, generated a marker-wrapped short `llm_summary` automatically on
Image creation, exposed it through a catalog metadata column, and copied that
value into Image block alt text.

The agreed replacement separates three concerns:

1. **Image metadata at creation** — an editor explicitly opts in before an
   Image is created. The browser asks the backend to interpret the unpersisted
   image, receives a title and description, and sends those values in the
   ordinary Plone Image creation payload.
2. **Default Image block alt** — an internal Image block follows the linked
   Image object's current title at REST serialization time, without copying the
   title into persistent block `alt` data and without a browser GET per image.
3. **Optional block-local AI alt** — an editor may explicitly call
   `@image-alt`; the result is stored only as a block-local custom alt override.

## Agreed invariants

### Image metadata generation

- [x] Metadata generation is opt-in for every selected image; the choice is
  never remembered.
- [x] The popup explicitly discloses that the configured AI service will
  analyse the image.
- [x] Popup actions are Generate with AI, Upload/Use without AI, and Cancel.
- [x] Dismissing with Escape, close, or backdrop is equivalent to Cancel.
- [x] AI analysis happens before content creation.
- [x] There is no Image creation subscriber.
- [x] The frontend places generated title and description directly into the
  normal Plone creation payload.
- [x] In the Image block flow, the generated title therefore determines the
  new Image ID/URL.
- [x] In the Add Image form, AI values populate the form immediately and remain
  editable; the final title at Save determines the URL.
- [x] There is no separate AI-result review dialog.
- [x] Both title and description must validate; partial results are rejected.
- [x] Title is a concise factual descriptive phrase, suitable as default alt,
  with no filename, `Image of`, AI label, markdown, or trailing period.
- [x] Title maximum is 125 characters after normalization.
- [x] Description is one or two complete factual sentences with a maximum of
  500 characters after normalization.
- [x] Output language follows the page currently being edited, falling back to
  English.
- [x] Invalid, empty, or overlong output is retried through structured model
  validation and ultimately fails rather than being blindly truncated.
- [x] Supported AI input types are JPEG, PNG, WebP, GIF, and BMP.
- [x] For other formats, explain that AI is unavailable and offer the ordinary
  non-AI path or Cancel; do not block a format Plone otherwise accepts.
- [x] AI failure does not silently degrade. Offer Retry, continue without AI,
  or Cancel.
- [x] If analysis succeeded but Image creation failed, creation retry reuses
  the existing metadata result and does not call the model again.
- [x] `@image-metadata` handles bytes in memory, uses existing downscaling/size
  safeguards, persists nothing, and discards request data after responding.

### Add Image form

- [x] Prompt when the Image file is selected, not when Save is clicked.
- [x] Generate with AI replaces both current title and current description;
  the disclosure warns about replacement.
- [x] Use without AI preserves existing title and description, including when
  replacing a previously selected file.
- [x] If title is empty and AI is declined, leave it empty and let normal Add
  form validation require an editor-authored title; do not insert a filename.
- [x] Cancel discards the new selection and retains any previously selected
  file and form values.
- [x] After declining AI, expose a Generate metadata with AI action next to the
  selected file.
- [x] After successful generation, label the action Regenerate metadata with
  AI and confirm before replacing current title and description.
- [x] Generated values are ordinary form data and may be edited before Save.
- [x] Do not add the metadata action to the existing-Image edit form yet.

### Image block upload

- [x] Prompt for both drag/drop and file-picker uploads.
- [x] Generate with AI calls `@image-metadata`, then creates the Image with the
  returned title and description in the ordinary creation request.
- [x] Upload without AI retains existing block-upload behavior: filename as
  Image title and empty description.
- [x] Cancel creates no Image.
- [x] Changing the selected file while a request is active must invalidate or
  ignore stale responses.

### Live title and alt state

Persistent block fields:

```json
{
  "alt": "optional custom override",
  "alt_source": "image-title | custom",
  "decorative": false
}
```

Transient serialized field:

```json
{
  "image_title": "Current title of the linked internal Image"
}
```

Effective rendered alt precedence:

1. `decorative === true` -> `alt=""`;
2. `alt_source === "custom"` and non-empty custom `alt` -> custom `alt`;
3. permission-safe `image_title` -> live Image title;
4. empty string.

Agreed behavior:

- [x] New internal Image upload/selection starts with
  `alt_source: "image-title"`, clears any prior custom alt, and resets
  decorative to false.
- [x] Re-selecting the identical internal Image preserves custom alt and
  decorative state.
- [x] Replacing with a different internal Image clears the old alt, uses the
  new live title, and resets decorative to false.
- [x] Switching to an external URL clears the prior alt, sets custom mode,
  resets decorative to false, and shows an accessibility warning until custom
  alt or decorative intent is supplied.
- [x] External-image validation warns but does not block page saving.
- [x] Manually changing inherited title text switches to custom mode.
- [x] Clearing custom alt resumes live Image-title mode.
- [x] Text equal to the current Image title normalizes to Image-title mode and
  is not stored as a duplicate custom value.
- [x] Equality trims leading/trailing whitespace and collapses repeated
  internal whitespace, but remains case-sensitive and punctuation-sensitive.
- [x] The alt editor displays the effective live title and labels it as using
  the Image title; it does not appear blank.
- [x] Use Image title is shown only for a non-decorative internal image whose
  effective alt differs from its resolved title.
- [x] Use Image title clears the custom alt and sets Image-title mode.
- [x] Generate AI alt is shown in Image-title mode without overwrite
  confirmation.
- [x] Regenerate AI alt is shown for non-empty custom mode and requires
  confirmation.
- [x] Invalid AI-alt output preserves the current source and value.
- [x] Decorative defaults to false. Legacy blocks without the field therefore
  are not treated as decorative.
- [x] Enabling decorative preserves custom alt and source internally, renders
  an empty alt, shows the preserved alt disabled with an explanation, and
  hides Generate/Regenerate and Use Image title.
- [x] Disabling decorative restores the preserved source/value behavior.

### Legacy blocks without `alt_source`

No migration is allowed. Serialization performs best-effort lazy
classification:

- [x] Empty legacy alt -> Image-title mode.
- [x] Legacy alt equal to current Image title under the agreed whitespace
  normalization -> return `alt_source: "image-title"`, clear duplicate `alt`
  in the serialized response, and expose live `image_title`.
- [x] Other non-empty legacy alt -> custom mode and preserve it.
- [x] If the containing page is later saved, the inferred source becomes
  durable through ordinary block persistence.
- [x] Accepted limitation: if a legacy title-derived alt is not saved with its
  inferred source before the linked Image title changes, it becomes
  indistinguishable from a genuine custom legacy alt and will be preserved.
- [x] Editors can resolve ambiguous cases with Use Image title.

### Live-title meaning and security

- [x] Live means resolved when the containing page REST representation is
  serialized; normal page/API caching may delay visibility.
- [x] No browser GET per Image is added.
- [x] `image_title` is exposed only when the current principal can view the
  linked Image; otherwise custom alt or empty fallback is used.
- [x] `image_title` is never persisted.
- [x] Resolver must support stored `resolveuid` values and supported legacy
  internal URLs; external URLs are never traversed as internal content.

### `llm_summary` and marker policy

- [x] Production never received the previous Image `llm_summary` feature.
- [x] Image does not need the `ILLMSummary` behavior for either new endpoint.
- [x] Do not add a hardcoded Image exclusion to generic summary subscribers or
  REST services. Behavior assignment remains authoritative.
- [x] Remove the Image-specific automatic creation-summary implementation.
- [x] Preserve generic summary behavior for content types that provide
  `ILLMSummary`.
- [x] Remove the `llm_summary` portal_catalog metadata column declaration and
  runtime column helper because no remaining code consumes summary values from
  catalog brains.
- [x] Keep the actual `llm_summary` behavior field for summary-oriented content
  types.
- [x] Add no profile upgrade and no catalog-removal migration. A development
  site may retain a harmless pre-existing catalog column until manually
  rebuilt or adjusted by the owner.
- [x] Image metadata and Image alt API responses contain plain text and no AI
  markers.
- [x] Remove Image-specific frontend marker stripping and marker assumptions.
- [x] Leave generic opt-in summary-marker capability intact for any other agent
  configuration that may use it.

## REST contracts

### `POST <container>/@image-metadata`

Purpose: analyse an unpersisted image before ordinary Image creation.

Registration and security:

- [ ] Register on site/folder container contexts used by both requested UI
  flows; verify both Plone site root and Dexterity Folder traversal.
- [x] Require `plone.app.contenttypes.addImage` on the target container.
- [x] Before invoking the model, also verify at runtime that the Image FTI is
  constructible in that exact container under its local content-type
  constraints; otherwise return `image_not_addable`.
- [x] Do not create, modify, catalog, index, or commit content.

Request:

```json
{
  "image": {
    "data": "<base64>",
    "encoding": "base64",
    "content-type": "image/jpeg",
    "filename": "IMG_1234.jpg"
  },
  "language": "en"
}
```

Successful response:

```json
{
  "title": "Grey heron standing among wetland reeds",
  "description": "A grey heron stands in shallow water surrounded by dense green reeds."
}
```

Validation requirements:

- [x] Validate JSON shape, base64 encoding, decoded non-empty bytes, declared
  media type, supported media type, and configured request/image size limits.
- [x] Before decoding base64, enforce an encoded-size ceiling derived from the
  decoded-byte limit so an oversized request is rejected before allocation.
- [x] Verify decoded image content rather than trusting filename or MIME alone.
- [x] Read the image header before `Image.load()` and enforce finite maximum
  width, height, and total pixel count. Treat Pillow
  `DecompressionBombWarning` and `DecompressionBombError` as invalid input.
- [x] Normalize EXIF orientation before model input where applicable.
- [x] Reuse/downscale through a hardened bounded image preparation path. The
  strict Image-AI endpoint path fails closed on decode/preparation errors and
  never forwards original unverified bytes to the provider.
- [x] Validate language against a safe language-code format; fall back to
  English when absent/invalid rather than inserting arbitrary prompt text.
- [x] Return a stable JSON error body such as
  `{"error":{"code":"<code>","message":"<safe message>"}}`.
- [x] Support and test machine-readable codes at minimum:
  `invalid_request`, `unsupported_media_type`, `image_too_large`,
  `invalid_image`, `image_not_addable`, and `generation_failed`.
- [x] Never include raw image data, credentials, or provider internals in logs
  or error responses.

### `POST <image>/@image-alt`

Purpose: generate a block-local alt suggestion for an existing Image without
persisting it on the Image object.

Registration and security:

- [x] Register for `plone.app.contenttypes.interfaces.IImage`.
- [x] Require `cmf.ModifyPortalContent` on the Image.
- [x] Accept only an optional safe language code; do not accept surrounding page
  text in this iteration.
- [x] Do not mutate the Image, block, catalog, transaction, or workflow state.

Request:

```json
{
  "language": "en"
}
```

Successful response:

```json
{
  "alt": "A grey heron stands in shallow water among dense reeds."
}
```

Validation requirements:

- [x] Result is one factual plain-text sentence, non-empty, no marker/label,
  and no more than 125 characters.
- [x] Reject invalid output after structured validation/retry; never return an
  overlong suggestion for the frontend to truncate.
- [x] Use the same stable JSON error envelope and relevant machine-readable
  codes as `@image-metadata`; the frontend does not parse human message text.

## Planned backend model and agent design

- [x] Add a structured Pydantic result model for Image metadata with required,
  normalized `title` and `description` and the agreed limits.
- [x] Add a strict structured Image alt result with required plain-text `alt`
  and the 125-character limit.
- [x] Register a dedicated `image_metadata` agent using the dotted
  `output_type` facility already provided by `eea.genai.core`.
- [x] Register a dedicated `image_alt` agent.
- [x] Reuse `ImageContentProvider` and the useful normalization logic in
  `prepare_image_bytes`; persisted and transient image contexts share bounded
  preparation without persistent storage.
- [x] Do not inherit the unsafe fallback for endpoint calls; new Image AI calls
  use the strict fail-closed path and pixel/decompression-bomb limits.
- [ ] Keep prompts separate:
  - metadata prompt returns title plus description;
  - alt prompt returns only concise alt text.
- [ ] Require factual visible content only; prohibit unsupported identity,
  intent, emotion, invisible facts, markdown, labels, and AI disclaimers.
- [ ] Treat filename as optional context only, never as the generated title.
- [ ] Include requested output language in a controlled prompt fragment.
- [ ] Keep provider/model errors fail-closed at the endpoint while allowing the
  frontend to offer the explicit non-AI creation path.

## Implementation batches

### Batch 0 — Reconfirm baselines and write failing contracts

Goal: establish exact seams and tests before production edits.

- [x] Re-read this plan and verify no decision has been superseded.
- [x] Record HEAD and `git status --short --branch` for every relevant Git
  worktree, including the newly confirmed nested theme repository.
- [x] Recompute both content and `git diff --binary` SHA-256 fingerprints for
  the unrelated frontend paths and compare them with the Planning checkpoint.
  Stop and report any mismatch before changing frontend files.
- [x] Save every later pause comparison in the Execution log.
- [x] Confirm current installed Plone/Volto versions and the service/container
  interfaces available in this checkout.
- [x] Confirm existing package test commands from Jenkins/buildout rather than
  inventing commands.
- [x] Add or adjust focused failing backend tests for:
  - structured metadata output validation;
  - `@image-metadata` permission and request contract;
  - no persistence during metadata preflight;
  - `@image-alt` permission, response, and non-persistence;
  - unsupported/corrupt input and model failure;
  - encoded-size rejection before decode;
  - excessive width/height/pixel count and Pillow decompression-bomb handling;
  - strict failure without forwarding original unverified bytes;
  - container permission plus local Image addability;
  - every machine-readable error code used by frontend branching.
- [x] Add focused failing policy tests for live title serialization,
  permission checks, legacy classification, and transient-field removal.
- [x] Add focused failing frontend unit tests for the shared modal/client state
  without changing behavior yet.

**PAUSE 0**

- [x] Stop after failing contracts are demonstrated.
- [x] Append a PAUSE 0 Execution-log entry with exact test names, failure
  reasons, dirty files, fingerprints, proposed seams, and conflicts.
- [x] Ask the owner before continuing and record the response before Batch 1;
  the owner authorized uninterrupted production implementation through
  Batches 1-4.

### Batch 1 — `eea.genai.summary` endpoint foundation

Goal: deliver both stateless Image AI APIs while removing obsolete Image
summary/catalog coupling.

Expected files (adjust only if repository evidence requires it):

```text
eea/genai/summary/agents.py
eea/genai/summary/image.py
eea/genai/summary/generate.py
eea/genai/summary/configure.zcml
eea/genai/summary/restapi/configure.zcml
eea/genai/summary/restapi/post.py
new focused model/service module(s)
eea/genai/summary/tests/...
docs/HISTORY.txt
README.rst
```

Removal/cleanup candidates:

```text
eea/genai/summary/catalog.py
eea/genai/summary/profiles/default/catalog.xml
eea/genai/summary/tests/test_catalog.py
Image-specific creation subscriber and tests
summarizer:Image registration/configuration if it exists only for the removed flow
obsolete Image marker assumptions
```

Tasks:

- [x] Implement validated transient image decoding and context construction.
- [x] Implement structured metadata and alt models.
- [x] Implement/register `image_metadata` and `image_alt` agents.
- [x] Implement `@image-metadata` with Image-add permission plus runtime Image
  FTI/local-container addability enforcement.
- [x] Implement the stable machine-readable error contract and frontend-relevant
  codes defined above.
- [x] Harden image preparation against encoded/decoded size exhaustion and
  decompression bombs; fail closed before model invocation.
- [x] Implement `@image-alt` for `IImage` with Modify permission.
- [x] Verify neither endpoint mutates content or commits transactions.
- [x] Remove the ObjectCreatedEvent Image auto-summary route while preserving
  generic modified-event behavior for `ILLMSummary` content.
- [x] Do not add a hardcoded Image skip to generic summary paths.
- [x] Remove catalog-column declaration/helper/runtime calls/tests.
- [x] Update setup/uninstall comments that still claim the column is needed.
- [x] Remove Image-specific marker usage but retain generic marker capability.
- [x] Preserve generic `@llm-summary` and batch contracts.
- [x] Add regression tests proving generic summary behavior remains intact.
- [x] Run focused and package-level backend tests.
- [x] Run formatting/lint checks documented by the repository.
- [x] Run `git diff --check`.

**PAUSE 1**

- [ ] Stop with only `eea.genai.summary` production implementation complete;
  retain and separately list approved Batch 0 test-only changes in policy and
  frontend.
- [ ] Append a PAUSE 1 Execution-log entry with API examples, tests, complete
  dirty paths, fingerprint comparison, diff summary, and residual risks.
- [ ] Do not mutate a live site or begin policy/frontend production
  implementation without approval recorded in the Execution log.

### Batch 2 — `eea.volto.policy` live Image-title transformer

Goal: enrich internal Image blocks with permission-safe live title and lazy alt
source classification.

Expected files:

```text
eea/volto/policy/restapi/blocks.py
eea/volto/policy/restapi/configure.zcml
eea/volto/policy/tests/test_image_blocks.py  # preferred focused test module
```

Tasks:

- [x] Add an image-block serialization transformer using a deep copy; never
  mutate stored block dictionaries during GET serialization.
- [x] Run the Image-title serializer at `order = 0`, before Plone RESTAPI's
  generic order-1 resolveuid serializer, so it can inspect stored references.
- [x] Resolve stored `resolveuid` URLs to an Image brain/object.
- [x] Resolve only relative portal paths or absolute URLs matching the portal or
  explicitly configured internal prefixes. Never traverse an arbitrary host
  and never perform network access.
- [x] Check current-principal View permission before exposing title.
- [x] Always expose `image_title` for a resolvable/viewable internal Image,
  including when custom alt exists, because editor actions need the comparison.
- [x] Apply normalized legacy classification:
  - empty alt -> Image-title source;
  - normalized exact title match -> Image-title source and serialized alt empty;
  - other non-empty alt -> custom source.
- [x] Preserve already-persisted valid `alt_source` rather than reclassifying it.
- [x] Do not allow inferred/custom source logic to override decorative state.
- [x] Add an image-block deserialization transformer that strips only transient
  `image_title` while preserving `alt_source`, `alt`, and `decorative`.
- [x] Leave the existing URL-prefix output normalization at order 10000 and
  assert the new order-0, Plone order-1, and policy order-10000 relationship in
  tests/comments.
- [x] Cover missing/deleted/private/non-Image/external targets without leaking
  metadata or raising serialization errors.
- [x] Cover nested block traversal through the standard block transformer
  machinery rather than custom page-wide recursion.
- [x] Run focused policy tests and repository lint/test commands.
- [x] Run `git diff --check`.

**PAUSE 2**

- [ ] Stop after backend serialization/deserialization is verified.
- [ ] Report representative stored input and serialized output fixtures,
  permission evidence, tests, and ordering decisions.
- [ ] Ask the owner before frontend changes.

### Batch 3 — shared frontend client/modal and Image block flow

Goal: replace Image-block `llm_summary` behavior with explicit metadata
preflight, live title state, decorative semantics, and `@image-alt`.

Likely existing files:

```text
src/addons/volto-eea-website-theme/src/customizations/volto/components/manage/Blocks/Image/Edit.jsx
src/addons/volto-eea-website-theme/src/customizations/volto/components/manage/Blocks/Image/View.jsx
src/addons/volto-eea-website-theme/src/customizations/volto/components/manage/Blocks/Image/schema.js
src/addons/volto-eea-website-theme/src/components/theme/Widgets/ImageAltWidget.jsx
src/addons/volto-eea-website-theme/src/index.js
```

Likely new shared modules (final names follow local conventions):

```text
components/manage/ImageAI/ImageMetadataConsentModal.jsx
components/manage/ImageAI/imageAIClient.js
components/manage/ImageAI/imageAltState.js
focused *.test.jsx / *.test.js files
```

Tasks:

- [x] Replace/remove `aiSummary.js` marker and `pickAlt` semantics with focused
  plain-response helpers and explicit alt-state helpers.
- [x] Implement one reusable accessible three-action consent modal with the
  agreed AI disclosure.
- [x] Implement request helpers for `@image-metadata` and `@image-alt` using the
  project's API/path conventions.
- [x] Branch UI behavior only on HTTP status and machine-readable `error.code`,
  never by parsing localized/human error messages.
- [x] Add state for analysing, creating, retrying, cancelling, and stale-response
  invalidation.
- [x] Prompt before both drag/drop and file-picker Image block uploads.
- [x] AI path: analyse bytes, then create with generated title/description.
- [x] Non-AI path: create with filename title and empty description.
- [x] Retry creation with cached analysis after creation-only failure.
- [x] Unsupported type path: explain and offer ordinary upload or Cancel.
- [x] On successful creation, link the new Image and initialize Image-title
  source using the create response title for immediate editor display.
- [x] On existing Image selection, clear custom alt/reset decorative only when
  the URL actually changes; preserve state on same-Image re-selection.
- [x] On external replacement, clear stale alt/reset decorative/use custom mode.
- [x] Add `alt_source` and `decorative` schema/UI.
- [x] Render with agreed effective-alt precedence in Edit and View.
- [x] Show live title in the alt editor with a Using Image title indication.
- [x] Add Use Image title only under the agreed comparison conditions.
- [x] Implement whitespace-normalized, case/punctuation-sensitive equality.
- [x] Implement reversible decorative behavior and disabled preserved-alt UI.
- [x] Implement Generate/Regenerate AI alt against `@image-alt`, passing only
  the page language code.
- [x] Normalize AI alt equal to Image title back to Image-title mode.
- [x] Preserve current state on AI-alt error or invalid response.
- [x] Add non-blocking accessibility warning for unresolved external alt.
- [x] Wrap every new user-facing modal, failure, accessibility, decorative, and
  Generate/Regenerate string in the repository's `react-intl` pattern; update
  or extract locale catalogs according to project convention.
- [x] Remove all Image marker stripping, Image `llm_summary`, and search-brain
  summary dependencies.
- [x] Add/update component and helper tests for implemented state transitions.
- [x] Run focused Jest tests, lint touched files, and `git diff --check`.

**PAUSE 3**

- [ ] Stop after unit-tested Image block behavior.
- [ ] Report the state machine, API calls, tests, and any UX deviations.
- [ ] Ask the owner before Add form integration.

### Batch 4 — Add Image form integration

Goal: apply the same explicit pre-creation metadata analysis to
Add content -> Image without copying/forking the full Volto Add component unless
repository evidence proves unavoidable.

Preferred seam:

- a focused Image-file widget wrapper or Add-Image integration that receives
  normal `formData` and `onChange`;
- delegate normal file rendering/validation to Volto's existing FileWidget;
- activate only for the Image add route/form, not every image field and not the
  existing-Image edit form.

Tasks:

- [x] Confirm the narrowest stable Volto extension seam with installed source
  before editing.
- [x] Avoid a wholesale customization copy of `Add.jsx` by registering a
  creation-only Image file-widget wrapper.
- [x] Prompt immediately after a valid new file selection.
- [x] Hold the pending file client-side until Generate, Use without AI, or
  Cancel resolves.
- [x] On Cancel, retain the previous selected file/form values.
- [x] Generate path calls `@image-metadata`, then updates `image`, `title`, and
  `description` form fields atomically.
- [x] Warn that generation replaces both title and description.
- [x] Non-AI path changes only the selected file and preserves metadata.
- [x] Leave empty title empty for normal required-field validation.
- [x] Provide Generate metadata with AI after a non-AI choice.
- [x] Provide confirmed Regenerate metadata with AI after generation.
- [x] Keep generated-status provenance in client state only; persist no marker
  or AI flag on the Image.
- [x] Preserve successful analysis in editable form state across an ordinary
  creation-request retry.
- [x] Pass Add form/current translation language safely.
- [x] Reuse shared modal/client/error behavior from Batch 3.
- [x] Add focused tests for first selection, cancellation, unsupported format,
  generation failure, overwrite confirmation, non-AI preservation, language,
  and non-Add delegation; final submit remains for browser verification.
- [x] Verify existing Image edit form delegates to the stock file widget and has
  no metadata-generation action.
- [x] Run focused/full Jest tests, lint, production build, and `git diff --check`.

**PAUSE 4**

- [ ] Stop after Add Image form unit tests pass.
- [ ] Report the chosen extension seam and prove other file/image fields and the
  edit form are unaffected.
- [ ] Ask before integration/browser verification.

### Batch 5 — integration verification and independent review

Goal: validate the complete workflow with objective evidence and no unapproved
site mutation.

Preparation:

- [ ] Ask the owner to start/confirm the backend and frontend processes.
- [ ] Ask explicit permission before creating/editing content on a running
  development site.
- [ ] Confirm a disposable test location and test account/permissions.
- [ ] Do not alter the owner's process configuration or unrelated content.

Backend/API verification:

- [ ] `@image-metadata` rejects anonymous/unauthorized use.
- [ ] `@image-metadata` succeeds for an Image-authorized container and returns
  plain validated title/description.
- [ ] Preflight leaves no object, blob, catalog record, or transaction-side
  content mutation.
- [ ] `@image-alt` requires Modify on the Image, returns plain alt, and does not
  persist it.
- [ ] Generic non-Image summary generation still works.
- [ ] New/default installs do not add `llm_summary` catalog metadata.

Playwright/browser verification — Image block:

- [ ] File picker and drag/drop both show disclosure and three actions.
- [ ] Dismiss/Cancel creates nothing.
- [ ] Non-AI upload uses filename title.
- [ ] AI upload creates one Image with generated title/description and a slug
  derived from title.
- [ ] Analysis failure offers Retry / without AI / Cancel.
- [ ] Creation retry does not repeat successful analysis.
- [ ] New block renders linked Image title as alt without an extra Image GET.
- [ ] Existing Image selection and replacement follow state rules.
- [ ] Same Image re-selection preserves state.
- [ ] Manual/custom/clear/Use title transitions work.
- [ ] Generate and Regenerate AI alt confirmation rules work.
- [ ] Decorative mode renders empty alt and restores preserved data.
- [ ] External URL replacement warns without blocking save.

Playwright/browser verification — Add Image form:

- [ ] File selection shows the opt-in popup.
- [ ] AI generation immediately fills editable title/description fields.
- [ ] Existing metadata replacement is disclosed and confirmed.
- [ ] Non-AI selection preserves current metadata and empty title remains empty.
- [ ] Cancel preserves previous file and metadata.
- [ ] Generate/Regenerate metadata action works after selection.
- [ ] Final Save uses current edited title/description and correct slug.
- [ ] Existing Image edit form has no metadata generation action.

Live-title verification:

- [ ] Old empty-alt block renders linked Image title.
- [ ] Old alt exactly equal to title serializes as Image-title source.
- [ ] Old differing alt remains custom.
- [ ] Saving a lazily classified page persists source but not `image_title`.
- [ ] Editing linked Image title changes Image-title-mode alt after fresh page
  serialization, subject to accepted cache behavior.
- [ ] Custom and decorative modes remain unchanged when Image title changes.
- [ ] Restricted Image title is not leaked to an unauthorized page viewer.

Final quality gates:

- [ ] Run complete relevant package tests for `eea.genai.summary`.
- [ ] Run complete relevant package tests for `eea.volto.policy`.
- [ ] Run focused frontend tests plus project lint/type/build commands required
  by Jenkins for touched code.
- [ ] Run `git diff --check` in all changed repositories.
- [ ] Inspect `git status`, recompute recorded content/diff hashes, and prove
  unrelated frontend changes match the Planning checkpoint or an explicitly
  owner-approved later baseline.
- [ ] Append all final evidence to the PAUSE 5 Execution-log entry.
- [x] Obtain fresh-context independent review covering spec, security/privacy,
  accessibility, REST permissions, transformer mutation/order, stale async
  responses, and tests.
- [x] Address all review findings, rerun affected checks, and obtain final
  APPROVE verdict with no remaining issues.
- [ ] Update README/HISTORY and this checklist with final evidence.
- [ ] Do not commit; hand the final diff and evidence to the owner.

**PAUSE 5 / FINAL OWNER GATE**

- [ ] Present changed-file lists per repository.
- [ ] Present exact commands and pass/fail evidence.
- [ ] Present browser/API evidence and known residual risks.
- [ ] Present reviewer findings and resolutions.
- [ ] Ask the owner to decide whether and how to commit/deploy.

## Test matrix

### `eea.genai.summary`

- [ ] Metadata result accepts normalized valid title/description.
- [ ] Metadata result rejects missing, blank, overlong, partial, or malformed
  output.
- [ ] Alt result rejects blank/overlong output.
- [ ] Valid JPEG/PNG/WebP/GIF/BMP reaches the multimodal agent.
- [ ] Unsupported MIME, corrupt base64, empty bytes, MIME/content mismatch, and
  oversized payload produce stable machine-readable errors.
- [ ] Encoded-size limit is enforced before base64 decoding.
- [ ] Excessive dimensions/pixel counts and Pillow decompression-bomb warning or
  error fail before `Image.load()`/model invocation.
- [ ] Strict preparation errors never fall back to original unverified bytes.
- [ ] EXIF orientation and max-side preparation are covered.
- [ ] Metadata endpoint permission and runtime Image addability are enforced at
  site root and folder.
- [ ] Metadata endpoint does not add content or mutate a transaction object.
- [ ] Alt endpoint is available for `IImage` without `ILLMSummary`.
- [ ] Alt endpoint Modify permission is retained.
- [ ] Alt endpoint does not persist.
- [ ] Requested/fallback language reaches a controlled prompt.
- [ ] Provider failure does not expose internals.
- [ ] Generic summary modified-event, single endpoint, and batch behavior remain
  green.
- [ ] No Image-specific ObjectCreatedEvent auto-generation remains.
- [ ] No new install path adds the catalog column.

### `eea.volto.policy`

- [ ] Serializer does not mutate input/stored block.
- [ ] Viewable internal Image adds `image_title`.
- [ ] Private Image title is omitted for unauthorized principal.
- [ ] Resolveuid and supported legacy internal URL work.
- [ ] External/non-Image/missing targets fail safely.
- [ ] Existing explicit `alt_source` is preserved.
- [ ] Empty legacy alt infers Image-title source.
- [ ] Whitespace-equivalent title alt infers Image-title source and serialized
  duplicate is empty.
- [ ] Case or punctuation difference remains custom.
- [ ] Deserializer removes `image_title` and preserves durable fields.
- [ ] Transformer ordering remains compatible with URL normalization and
  Plone RESTAPI block resolution.

### Frontend helpers/components

- [ ] Consent popup action and dismissal semantics.
- [ ] Disclosure text and keyboard accessibility.
- [ ] Supported/unsupported media branching.
- [ ] Metadata request/creation request payloads and language.
- [ ] Every relevant machine-readable API error code reaches the intended UI
  branch without parsing the error message.
- [ ] Retry uses cached metadata after creation failure.
- [ ] Stale request ignored after file/source change or unmount.
- [ ] Effective alt state table.
- [ ] Equality normalization.
- [ ] Legacy inferred values received from serializer.
- [ ] Same versus different Image replacement.
- [ ] External image warning.
- [ ] Decorative reversible state.
- [ ] Generate versus Regenerate labels and confirmation.
- [ ] Plain `alt` response with no marker helpers.
- [ ] Add Image form first selection/replacement/cancel/generate/regenerate.
- [ ] Existing edit form and unrelated file widgets unaffected.
- [ ] Every new user-facing string uses `react-intl`; verify extraction/catalog
  handling and at least one non-English locale or message-ID snapshot.

## Acceptance criteria

The feature is done only when all are true:

- [ ] An editor can opt into AI metadata for a new Image from either requested
  UI flow.
- [ ] Opt-in happens before creation and is disclosed for every image.
- [ ] The created Image receives generated title and description through the
  normal creation payload, with no subscriber or follow-up PATCH.
- [ ] The title used at creation determines the Image slug.
- [ ] Declining AI retains the agreed ordinary behavior for each workflow.
- [ ] AI failures never create silently partial metadata.
- [ ] Image block default alt follows the permission-safe live linked Image
  title without per-image browser GETs.
- [ ] Custom alt and decorative intent are explicit, reversible, and protected
  during title changes.
- [ ] Legacy blocks improve lazily without content migration and without
  destroying differing non-empty alts.
- [ ] `@image-alt` remains explicitly available and non-persisting.
- [ ] Neither `@image-metadata`, `@image-alt`, the Image-block workflows, nor
  the Add Image workflow emits or persists AI markers. Generic
  `@llm-summary` marker behavior remains unchanged for any content object
  explicitly providing `ILLMSummary`.
- [ ] Image no longer depends on an `llm_summary` field or catalog metadata.
- [ ] Generic behavior-driven summary functionality remains operational.
- [ ] Both backend packages and frontend checks pass.
- [ ] Browser verification covers both creation entry points and accessibility
  state transitions.
- [ ] Independent review has no unresolved high-severity finding.
- [ ] No unrelated worktree file content or diff fingerprint changes without
  explicit owner acknowledgement recorded in the Execution log.
- [ ] No agent-created commit exists.

## Known trade-offs and residual risks

- [x] The image bytes are sent twice on the AI path: once to
  `@image-metadata`, then in the ordinary creation request. Avoiding this would
  require heavier temporary storage or a create-and-analyse endpoint.
- [x] Serializer-time live title is subject to normal REST/page caching.
- [x] Legacy non-empty alt provenance cannot be reconstructed perfectly without
  migration; the accepted heuristic is conservative.
- [x] An editor who can modify a page but cannot modify a shared Image cannot
  invoke `@image-alt` for that Image under the retained permission contract.
- [x] Image-title fallback for a non-AI block upload may initially be a filename
  until the Image title is edited or a custom/AI alt is supplied.
- [x] Existing development catalog columns and behavior assignments are not
  removed automatically. Per owner instruction, this work adds no migration or
  profile upgrade; any live-site cleanup is separate and out of scope.
- [x] GIF interpretation may depend on provider/image normalization behavior;
  automated tests must document the actual frame handling rather than imply
  unsupported temporal understanding.

## Handoff summary

As of the PAUSE 6 correction, modal loaders, block alt updates, AI-alt
persistence, and the alt-description warning are fixed and browser verified.
The mistakenly added upgrade step has been removed completely: the profile
remains at version 1.0 and no migration or live FTI cleanup is included. Full
backend/frontend tests, frontend lint/i18n/style/build checks, Ruff, browser
computed-style checks, saved block JSON inspection, and independent review are
green. No agent-created commit exists.
