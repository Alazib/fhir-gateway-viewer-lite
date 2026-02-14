from datetime import datetime
from fhir_gateway.domain.errors import DomainValidationError


def type_validator(
    instance: object,
    attribute_name: str,
    expected_type: type | tuple[type, ...],
    optional_error_message: (
        str | None
    ) = None,  # All the validations with "expected_type: tuple[type,...]" require an optional_error_message in order to avoid a final
    # error message such as "...must be a None"
) -> None:
    class_name = instance.__class__.__name__
    value = instance.__getattribute__(attribute_name)

    if not isinstance(value, expected_type):

        type_names_map = {
            str: "string",
            int: "number",
            float: "number",
            list: "list",
            dict: "dictionary",
            tuple: "tuple",
            bool: "boolean",
            datetime: "datetime",
        }

        expected_type_name = type_names_map.get(expected_type)

        error_message = (
            f"must be a {expected_type_name}"
            if optional_error_message is None
            else optional_error_message
        )

        raise DomainValidationError(
            f"{class_name}.{attribute_name}",
            error_message,
        )
