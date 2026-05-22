import ast
from pathlib import Path


API_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = API_ROOT / "src" / "fhir_gateway"

PROTECTED_PACKAGES = (
    SRC_ROOT / "domain",
    SRC_ROOT / "application",
)


def _imports_sqlalchemy(file_path: Path) -> bool:
    tree = ast.parse(
        file_path.read_text(encoding="utf-8-sig"),
        filename=str(file_path),
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "sqlalchemy" or alias.name.startswith("sqlalchemy."):
                    return True

        if isinstance(node, ast.ImportFrom):
            if node.module == "sqlalchemy" or (
                node.module is not None and node.module.startswith("sqlalchemy.")
            ):
                return True

    return False


def test_domain_and_application_do_not_import_sqlalchemy():
    # This test protects the architectural boundary between the core layers and
    # infrastructure. Domain and application code must not import SQLAlchemy,
    # because persistence is an implementation detail that belongs only to the
    # infrastructure layer.
    violating_files = []

    for package_path in PROTECTED_PACKAGES:
        for file_path in package_path.rglob("*.py"):
            if _imports_sqlalchemy(file_path):
                violating_files.append(file_path.relative_to(API_ROOT))

    assert violating_files == []
