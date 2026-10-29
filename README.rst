=================
eea.genai.summary
=================
.. image:: https://ci.eionet.europa.eu/buildStatus/icon?job=eea/eea.genai.summary/develop
  :target: https://ci.eionet.europa.eu/job/eea/job/eea.genai.summary/job/develop/display/redirect
  :alt: Develop
.. image:: https://ci.eionet.europa.eu/buildStatus/icon?job=eea/eea.genai.summary/master
  :target: https://ci.eionet.europa.eu/job/eea/job/eea.genai.summary/job/master/display/redirect
  :alt: Master

LLM summary generation for Plone content types, built on the agentic
infrastructure of ``eea.genai.core``.

Provides an activatable behavior that adds ``allow_llm_summary`` and
``llm_summary`` fields to any Dexterity content type, automatic summary
generation via the ``summarizer`` agent on content save, and REST API
endpoints for manual and batch generation.

.. contents::

Main features
=============

1. ``ILLMSummary`` behavior with ``allow_llm_summary`` and
   ``llm_summary`` fields.
2. ``generate_summary_for(obj, request, properties=None)`` —
   single-call API that resolves the right agent for the object's
   ``portal_type`` and runs it via the core executor.
3. Content-type-specific agents via naming convention
   ``summarizer:<PortalType>`` (falls back to ``summarizer``).
4. ``generic_metadata`` enricher (``GenericMetadataProvider``) —
   contributes title, description, language, geographic coverage, and
   temporal coverage to the user prompt. Reads from in-progress
   ``properties`` if passed, so unsaved edits are reflected.
5. Event subscriber for automatic summary generation on save.
6. ``@llm-summary`` REST endpoint for single-object generation.
7. ``@llm-summary-batch`` REST endpoint for batch generation.
8. Default agent definitions shipped in ``agents.json`` —
   override via the control panel ``agents_json``.
9. ``POST <container>/@image-metadata`` for validated, stateless metadata
   generation before ordinary Image creation.
10. ``POST <image>/@image-alt`` for a validated, non-persisting block-local
    alt suggestion.
11. ``POST <object>/@image-metadata-regenerate`` for validated, non-persisting
    metadata suggestions when editing existing Dexterity content.

Image APIs
==========

``@image-metadata`` accepts a base64 image payload plus a safe language code
on a folderish container. The optional ``portal_type`` identifies the content
being added (default ``Image`` for existing callers), not its container.
The caller must have the ordinary Add portal content permission, the requested
FTI's construction permission, and satisfy local container type constraints.
It validates and bounds the image entirely in memory, calls a structured
multimodal agent, and returns plain ``title`` and ``description`` values.
It creates no content, blob, catalog record, or temporary file.

``@image-alt`` is registered for the standard Plone ``IImage`` interface and
requires Modify permission on the Image. It analyses verified Image bytes and
metadata and returns plain ``alt`` text without changing the Image.

``@image-metadata-regenerate`` requires Modify permission on the existing object
(guarded by ``cmf.ModifyPortalContent``). It accepts ``field`` (the schema image
field's name) and an optional ``language``. With no ``image`` payload it reads the
stored field; a supplied base64 ``image`` takes precedence and is validated as an
unsaved replacement, never persisted. Download descriptors and URLs are not fetched.
The field must be a named-image schema field on the object or one of its behaviors.
The endpoint returns plain ``title`` and ``description`` suggestions through the
same generation pipeline as Add without mutating the object.

The form widget supports both Add and Edit for the explicitly registered
``image`` and ``preview_image`` fields. On Edit it uses the loaded object's
content type, confirms replacement of existing metadata, and sends any unsaved
replacement bytes instead of asking for the stored source. Stored regeneration
changes only unsaved title/description; the file remains unchanged. Normal
form Save persists edits; form cancellation discards them. Late results are
ignored after source/context changes or cancellation, and metadata edited
during analysis is preserved with an explicit retry message.

None of the Image endpoints uses AI markers or depends on the ``ILLMSummary``
behavior. Generic summary behavior remains opt-in and behavior-driven.

Image AI is disabled by default. In the shared GenAI controlpanel, enable
both the global GenAI switch and ``Enable Image AI features`` to allow Image
metadata and alt generation. Disabled requests return HTTP 403 with the
``image_ai_disabled`` error code; ordinary uploads and manual editing remain
available.

``Allowed content types`` defaults to ``Image`` only. An explicitly empty
list allows all types; it does not bypass permissions or add support for
otherwise unsupported image sources. All Image endpoints enforce this policy and
return HTTP 403 with ``image_ai_not_allowed`` for an excluded target type.
Add metadata generation checks the requested new object's type; regeneration
checks the existing object's actual type. Alt generation checks the linked
Image's actual type, never a submitted type or the containing
page's type. The public Image settings include ``allowed_content_types``;
frontend controls fail closed when this policy is missing or failed to load.

The Image AI section defines positive character limits: a shared title/alt
maximum (default 40) and a description maximum (default 500). Limits apply to
trimmed generated text, not manually edited metadata. They are supplied in
prompts and enforced on returned values. Oversized output is retried once;
if it still exceeds a limit, generation fails without truncation. Metadata
fields are retried together; filename-derived titles share the same single
retry budget.

The section is contributed through a named ``IGenAISettingsSection`` utility
in ``configure.zcml``. Its records are installed by this package's
``registry.xml`` using the core settings prefix. On existing sites, the owner
must run the ``eea.genai.summary`` profile upgrades to 2.1 after
deploying/restarting the backend, before using the extended controlpanel.
The 1.0 to 2.0 step installs Image AI settings; the 2.0 to 2.1 step adds the
content-type policy on sites that already have those settings.
The upgrade imports only the registry step, without purging records or running
import dependencies. It preserves existing settings and is safe to repeat.
No ``eea.genai.core`` upgrade or legacy Image behavior cleanup is included.
Missing Image records use safe runtime defaults and do not enable generation.

The theme loads allowlisted flags from ``@genai-settings`` during SSR into
``state.reduxAsyncConnect.genAISettings``, just like header settings. Changes
take effect in frontend controls on the next full page load; generation
requests always check current backend settings.

Install
=======

- Add ``eea.genai.summary`` to your ``requirements.txt``.
- Install the GenericSetup profile.
- Activate the ``eea.genai.summary`` behavior on the desired content
  types (Site Setup → Dexterity Content Types → *Type* → Behaviors).

Customization
=============

Override the default ``summarizer`` agent for a content type by
registering a more specific agent in either ZCML or the control
panel ``agents_json``::

    <genai:agent
        name="summarizer:EEAFigure"
        class=".agents.FigureSummarizerAgent"
    />

To inject extra prompt fragments (e.g. dataset-specific instructions),
write an ``IEnricher`` in your own package and reference it from the
agent's ``enrichers`` list — no need to subclass anything in
``eea.genai.summary``.

Copyright and license
=====================

The Initial Owner of the Original Code is European Environment Agency (EEA).
All Rights Reserved.

All contributions to this package are property of their respective authors,
and are covered by the same license.

The eea.genai.summary is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by the Free
Software Foundation, either version 2 of the License, or (at your option) any
later version.

Secret Scanning
===============

This repository uses the Betterleaks GitHub Action to scan the current
repository content on every push and pull request. The scan uses the rules in
``.gitleaks.toml`` and uploads a ``betterleaks-report`` artifact when a finding
is detected.

If the optional SMTP secrets are configured, failed scans also send an email to
the last commit committer. The workflow expects these repository or
organization secrets:

- ``SMTP_URL``
- ``SMTP_PORT`` (optional, defaults to ``25``)
- ``SMTP_EMAIL``
- ``SMTP_PASSWORD`` (optional if the SMTP server does not require authentication)

Port ``465`` is sent with direct TLS; other ports use the default SMTP
handshake. The email includes a short finding summary from the redacted
Betterleaks report, including the redacted matched line from each finding.

There are three common outcomes:

1. Everything is OK. The ``Betterleaks / Scan for secrets`` check is green and
   no action is needed. Regular references to runtime values are OK, for example::

     token_from_cookie = request.cookies.get("auth_token")

2. A real secret was found. The check is red and the workflow log asks you to
   download the ``betterleaks-report`` artifact. Open the artifact from the
   GitHub Actions run and check the reported file, line and rule. Remove the
   committed value, move it to the proper secret store, and rotate it if it was
   exposed. A report entry looks like this::

     {
       "RuleID": "secret-literal-assignment",
       "File": "src/config.py",
       "StartLine": 12,
       "Secret": "[REDACTED]"
     }

3. The finding is a false positive. Keep the value only if it is clearly not
   sensitive, such as a test fixture, placeholder, or public example. Add
   ``betterleaks:allow`` on the same line and include a short explanation in the
   pull request::

     test_password = "admin"  #betterleaks:allow

Do not add ``betterleaks:allow`` to real credentials.
