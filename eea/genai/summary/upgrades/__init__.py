"""GenericSetup upgrades for eea.genai.summary."""


def install_image_ai_settings(context):
    """Add Image AI records without purging settings or importing other steps."""
    context.runImportStepFromProfile(
        "profile-eea.genai.summary:default",
        "plone.app.registry",
        run_dependencies=False,
        purge_old=False,
    )
