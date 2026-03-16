=================
eea.genai.summary
=================
.. image:: https://ci.eionet.europa.eu/buildStatus/icon?job=volto/eea.genai.summary/develop
  :target: https://ci.eionet.europa.eu/job/volto/job/eea.genai.summary/job/develop/display/redirect
  :alt: Develop
.. image:: https://ci.eionet.europa.eu/buildStatus/icon?job=volto/eea.genai.summary/master
  :target: https://ci.eionet.europa.eu/job/volto/job/eea.genai.summary/job/master/display/redirect
  :alt: Master

LLM Summary behavior for Plone content types.

Provides an activatable behavior that adds ``allow_llm_summary`` and
``llm_summary`` fields to any Dexterity content type, with automatic
summary generation on save and REST API endpoints for manual/batch
generation.

.. contents::

Main features
=============

1. ``ILLMSummary`` behavior with ``allow_llm_summary`` and ``llm_summary`` fields
2. Default prompt builder using common EEA metadata (title, description, geo/temporal coverage)
3. Event subscriber for automatic summary generation on content save
4. ``@llm-summary`` REST API endpoint for single-object generation
5. ``@llm-summary-batch`` REST API endpoint for batch generation
6. Extensible via custom ``ILLMPromptBuilder`` adapters per content type

Install
=======

- Add ``eea.genai.summary`` to your ``requirements.txt``
- Activate the ``eea.genai.summary`` behavior on desired content types

Extension
=========

To provide content-type-specific prompts, register a more specific
``ILLMPromptBuilder`` adapter in your addon::

    @implementer(ILLMPromptBuilder)
    @adapter(IMyContentType, Interface)
    class MyPromptBuilder:
        def __init__(self, context, request):
            self.context = context
            self.request = request

        def system_prompt(self):
            return "Your specialized system prompt..."

        def user_prompt(self):
            return "Content-specific data..."

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
