import ast
from pathlib import Path


API_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = API_ROOT / "src" / "fhir_gateway"

PROTECTED_PACKAGES = (
    SRC_ROOT / "domain",
    SRC_ROOT / "application",
)

FORBIDDEN_TOP_LEVEL_MODULES = (
    "fastapi",
    "jwt",
)


def _find_forbidden_imports(file_path: Path) -> tuple[str, ...]:
    tree = ast.parse(
        file_path.read_text(encoding="utf-8-sig"),
        filename=str(file_path),
    )

    forbidden_imports: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules = tuple(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_modules = (node.module,) if node.module is not None else ()
        else:
            continue

        for imported_module in imported_modules:
            top_level_module = imported_module.split(".", maxsplit=1)[0]

            if top_level_module in FORBIDDEN_TOP_LEVEL_MODULES:
                forbidden_imports.add(imported_module)

    return tuple(sorted(forbidden_imports))


def test_domain_and_application_do_not_import_fastapi_or_pyjwt():
    violating_imports: list[str] = []

    for package_path in PROTECTED_PACKAGES:
        for file_path in package_path.rglob("*.py"):
            for imported_module in _find_forbidden_imports(file_path):
                relative_path = file_path.relative_to(API_ROOT)
                violating_imports.append(
                    f"{relative_path}: imports {imported_module}",
                )

    assert sorted(violating_imports) == []
