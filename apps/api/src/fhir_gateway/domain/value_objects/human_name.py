from __future__ import annotations

from dataclasses import dataclass, field

from fhir_gateway.domain.errors import DomainValidationError


@dataclass(frozen=True, slots=True)
class HumanName:
    """
    MVP HumanName supporting two valid representations:

    - Unstructured: text is present (non-empty after trim)
    - Structured: given (>= 1) and family (non-empty) when text is missing

    Normalization:
    - text: trim; if empty -> None
    - family: trim; if empty -> None
    - given: must be list/tuple of strings; trim each; drop empties; stored as tuple for immutability
    """

    given: list[str] | tuple[str, ...] = field(default_factory=list)
    family: str | None = None
    text: str | None = None

    def __post_init__(self) -> None:
        # 1) Normalize each field (no invariants yet)
        normalized_text = self._normalize_optional_str("text", self.text)
        normalized_family = self._normalize_optional_str("family", self.family)
        normalized_given = self._normalize_given(self.given)

        # 2) Freeze normalized values into the frozen dataclass
        object.__setattr__(self, "text", normalized_text)
        object.__setattr__(self, "family", normalized_family)
        object.__setattr__(self, "given", normalized_given)

        # 3) Invariant (two-mode validation):
        # If text is missing -> require structured name: given + family
        if normalized_text is None:
            if not normalized_given:
                raise DomainValidationError(
                    "given", "cannot be empty when text is missing"
                )
            if normalized_family is None:
                raise DomainValidationError(
                    "family", "cannot be empty when text is missing"
                )

    @staticmethod
    def _normalize_optional_str(field_name: str, value: str | None) -> str | None:
        """
        Accepts None or str.
        - If None -> None
        - If str -> trim; if empty -> None; else cleaned str
        """
        if value is None:
            return None
        if not isinstance(value, str):
            raise DomainValidationError(field_name, "must be a string")
        cleaned = value.strip()
        return cleaned if cleaned != "" else None

    @staticmethod
    def _normalize_given(value: object) -> tuple[str, ...]:
        """
        given must be list/tuple of strings (NOT a plain string).
        - trims each element
        - drops empty elements
        - returns an immutable tuple
        """
        if isinstance(value, str):
            # Avoid the classic bug: "Ana" is iterable -> ["A","n","a"]
            raise DomainValidationError("given", "must be a list/tuple of strings")

        if not isinstance(value, (list, tuple)):
            raise DomainValidationError("given", "must be a list or a tuple")

        if not all(isinstance(s, str) for s in value):
            raise DomainValidationError("given", "must be a list/tuple of strings")

        cleaned_items = [s.strip() for s in value]
        cleaned_items = [s for s in cleaned_items if s != ""]  # drop empties

        return tuple(cleaned_items)
