from dataclasses import dataclass
from enum import Enum

from fhir_gateway.domain.helpers.normalizer import normalize_string
from fhir_gateway.domain.helpers.type_validator import type_validator
from fhir_gateway.domain.value_objects.instant import Instant
from fhir_gateway.domain.value_objects.reference import Reference
from fhir_gateway.domain.value_objects.resource_id import ResourceId


class AuditAction(str, Enum):
    READ = "read"
    SEARCH = "search"
    EXPORT = "export"


@dataclass(frozen=True, slots=True)
class AuditEvent:
    id: ResourceId
    recorded: Instant
    agent: str
    action: AuditAction
    entity: Reference

    def __post_init__(self) -> None:
        type_validator(self, "id", ResourceId, "must be a ResourceId")

        type_validator(self, "recorded", Instant, "must be an Instant")

        type_validator(self, "agent", str)
        cleaned_agent = normalize_string(self, "agent")
        object.__setattr__(self, "agent", cleaned_agent)

        type_validator(self, "action", AuditAction, "must be an AuditAction")

        type_validator(self, "entity", Reference, "must be a Reference")
