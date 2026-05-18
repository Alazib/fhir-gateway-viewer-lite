import logging
from typing import Any

from fhir_gateway.infrastructure.logging import configure_logging


def test_configure_logging_uses_expected_level_and_format(
    monkeypatch,
):
    captured_config: dict[str, Any] = {}

    def fake_basic_config(**kwargs: Any) -> None:
        captured_config.update(kwargs)

    monkeypatch.setattr(logging, "basicConfig", fake_basic_config)

    configure_logging("DEBUG")

    assert captured_config["level"] == "DEBUG"
    assert (
        captured_config["format"] == "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    )
