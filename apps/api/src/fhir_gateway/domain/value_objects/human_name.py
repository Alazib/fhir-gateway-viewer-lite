from __future__ import annotations
from dataclasses import dataclass, field
from fhir_gateway.domain.errors import DomainValidationError
from fhir_gateway.domain.helpers.normalizer import normalize_string
from fhir_gateway.domain.helpers.type_validator import type_validator


@dataclass(frozen=True, slots=True)
class HumanName:
    """
    MVP HumanName supporting two valid representations:

    - Unstructured: text is present (non-empty after trim)
    - Structured: given (>= 1) and family (non-empty) when text is missing

    """

    given: list[str] | tuple[str, ...] = field(default_factory=list)
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

        if isinstance(self.given, str):
            raise DomainValidationError("given", "must be a list/tuple of strings")

        type_validator(self, "given", (list, tuple), "must be a list or a tuple")

        if not all(isinstance(s, str) for s in self.given):
            raise DomainValidationError("given", "must be a list/tuple of strings")

        cleaned_items = [string.strip() for string in self.given]
        cleaned_items_and_no_empties = [
            string for string in cleaned_items if string != ""
        ]

        list_to_tuple = tuple(cleaned_items_and_no_empties)
        object.__setattr__(self, "given", list_to_tuple)

        if self.text is None:
            if not self.given:
                raise DomainValidationError(
                    "given", "cannot be empty when text is missing"
                )
            if self.family is None:
                raise DomainValidationError(
                    "family", "cannot be empty when text is missing"
                )
