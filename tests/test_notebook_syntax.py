import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = sorted((ROOT / "notebooks").glob("*.ipynb"))


@pytest.mark.parametrize("notebook_path", NOTEBOOKS, ids=lambda path: path.name)
def test_notebook_code_cells_are_valid_python(notebook_path):
    notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    assert notebook.get("nbformat", 0) == 4
    for cell_number, cell in enumerate(notebook.get("cells", [])):
        if cell.get("cell_type") != "code":
            continue
        source = "".join(cell.get("source", []))
        # Remove IPython line magics; the remaining cell body must parse as Python.
        python_source = "\n".join(
            line for line in source.splitlines()
            if not line.lstrip().startswith("%") and not line.lstrip().startswith("!")
        )
        try:
            compile(python_source, f"{notebook_path.name}:cell-{cell_number}", "exec")
        except SyntaxError as exc:
            pytest.fail(f"Invalid Python in {notebook_path.name}, cell {cell_number}: {exc}")


def test_notebooks_use_the_shared_risk_kit_alias():
    for notebook_path in NOTEBOOKS:
        notebook_text = notebook_path.read_text(encoding="utf-8")
        assert "edhec_risk_kit" not in notebook_text
        assert "import risk_kit as erk" not in notebook_text
        assert "import risk_kit as rk" in notebook_text
