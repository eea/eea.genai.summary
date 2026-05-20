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
