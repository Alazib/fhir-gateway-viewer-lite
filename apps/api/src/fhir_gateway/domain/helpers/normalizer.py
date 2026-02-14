from fhir_gateway.domain.errors import DomainValidationError


def normalize_string(
    instance: object, attribute_name: str, attribute_required: bool = True
) -> str | None:

    value = instance.__getattribute__(attribute_name)
    value_cleaned = value.strip() if value else ""
    attribute_empty_and_required = not value_cleaned and attribute_required
    attribute_empty_and_not_required = not value_cleaned and not attribute_required

    if attribute_empty_and_required:
        class_name = instance.__class__.__name__
        raise DomainValidationError(f"{class_name}.{attribute_name}", "cannot be empty")
    elif attribute_empty_and_not_required:
        return None
    else:
        return value_cleaned
