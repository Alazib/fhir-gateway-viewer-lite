from __future__ import annotations

from dataclasses import dataclass

from fhir_gateway.domain.errors import DomainValidationError
from fhir_gateway.domain.helpers.normalizer import normalize_string
from fhir_gateway.domain.helpers.type_validator import type_validator


@dataclass(frozen=True, slots=True)
class HumanName:
    """
    MVP HumanName supporting two valid representations:

    - Unstructured: "text" is present (non-empty after trim)
    - Structured: "given" (>= 1) and "family" (non-empty) when "text" is missing
    """

    given: tuple[str, ...] = ()
    family: str | None = None
    text: str | None = None

    def __post_init__(self) -> None:

        if self.family is not None:
            type_validator(self, "family", str)
            cleaned_family = normalize_string(self, "family", False)
            object.__setattr__(self, "family", cleaned_family)

        if self.text is not None:
            type_validator(self, "text", str)
            cleaned_text = normalize_string(self, "text", False)
            object.__setattr__(self, "text", cleaned_text)

        g = self.given
        if isinstance(g, list):
            g = tuple(g)
        elif not isinstance(g, tuple):
            raise DomainValidationError("HumanName.given", "must be a list or a tuple")

        if not all(isinstance(s, str) for s in g):
            raise DomainValidationError(
                "HumanName.given", "must be a list/tuple of strings"
            )

        cleaned_items = tuple(s.strip() for s in g if s.strip() != "")
        object.__setattr__(self, "given", cleaned_items)

        # Representation rule: if text is missing, require structured fields
        if self.text is None:
            if not self.given:
                raise DomainValidationError(
                    "HumanName.given", "cannot be empty when text is missing"
                )
            if self.family is None:
                raise DomainValidationError(
                    "HumanName.family", "cannot be empty when text is missing"
                )
