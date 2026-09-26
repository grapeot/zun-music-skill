import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def load_example(name):
    spec = importlib.util.spec_from_file_location(f"examples.{name}", ROOT / "examples" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


EXAMPLES = sorted(p.stem for p in (ROOT / "examples").glob("*.py"))


@pytest.fixture(params=EXAMPLES)
def example(request):
    return load_example(request.param)
