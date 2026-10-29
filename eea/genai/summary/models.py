"""Structured output models for Image-specific AI operations."""

import re
import unicodedata

from pydantic import BaseModel, Field, field_validator


_IMAGE_MARKERS = (
    "[ai generated description]",
    "[end of ai generated description]",
)
_LABEL_PREFIX_RE = re.compile(
    r"^(?:ai(?:[- ]generated)?|image|photo|picture|title|description|"
    r"alt(?: text)?|caption)\s*[:\-]\s*",
    re.IGNORECASE,
)
_MARKDOWN_PATTERNS = (
    re.compile(r"^\s{0,3}(?:#{1,6}|[-*>])\s"),
    re.compile(r"[`*_]|~~|<\/?[A-Za-z][^>]*>"),
    re.compile(r"\[[^\]]+\]\([^)]+\)"),
)
_SENTENCE_END_RE = re.compile(r"[.!?](?:[\"')\]]*)$")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])(?:[\"')\]]*)\s+")


def _validate_plain_text(value: str) -> str:
    """Reject markers, labels, markdown, multiline, and control text."""
    folded = value.casefold()
    if any(marker in folded for marker in _IMAGE_MARKERS):
        raise ValueError("Image API output must not contain AI markers")
    if _LABEL_PREFIX_RE.match(value):
        raise ValueError("Image API output must not contain field labels")
    if any(char in "\r\n\t" or unicodedata.category(char) == "Cc" for char in value):
        raise ValueError("Image API output must be single-line plain text")
    if any(pattern.search(value) for pattern in _MARKDOWN_PATTERNS):
        raise ValueError("Image API output must not contain markdown")
    return value


def _validate_sentence_count(value: str, maximum: int) -> str:
    if not _SENTENCE_END_RE.search(value):
        raise ValueError("text must end with sentence punctuation")
    sentences = [part for part in _SENTENCE_SPLIT_RE.split(value) if part.strip()]
    if not 1 <= len(sentences) <= maximum:
        raise ValueError(f"text must contain at most {maximum} sentences")
    return value


class ImageMetadataResult(BaseModel):
    """Validated metadata generated for an Image before it is created."""

    # Runtime lengths are enforced by generation using the controlpanel values.
    # Keep structural validation independent of registry state.
    title: str = Field(
        min_length=1,
        description=(
            "Concise factual descriptive phrase, without a filename, label, "
            "markdown, or trailing period."
        ),
    )
    description: str = Field(
        min_length=1,
        description="One or two factual complete sentences describing the image.",
    )

    @field_validator("title", "description", mode="before")
    @classmethod
    def strip_text(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("title", "description")
    @classmethod
    def validate_plain_text(cls, value):
        return _validate_plain_text(value)

    @field_validator("title")
    @classmethod
    def validate_title_phrase(cls, value):
        if value.endswith("."):
            raise ValueError("title must not end with a period")
        if value.casefold().startswith(("image of ", "this image")):
            raise ValueError("title must not start with an image label")
        return value

    @field_validator("description")
    @classmethod
    def validate_description_sentences(cls, value):
        return _validate_sentence_count(value, maximum=2)


class ImageAltResult(BaseModel):
    """Validated block-local alt suggestion for an existing Image."""

    alt: str = Field(
        min_length=1,
        description="One concise factual sentence describing visible content.",
    )

    @field_validator("alt", mode="before")
    @classmethod
    def strip_text(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("alt")
    @classmethod
    def validate_plain_alt(cls, value):
        value = _validate_plain_text(value)
        if value.casefold().startswith(("image of ", "this image")):
            raise ValueError("alt must not start with an image label")
        return _validate_sentence_count(value, maximum=1)
