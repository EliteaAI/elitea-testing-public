"""Guard: the modules-dropdown spec/page object never pick rows positionally or use raw locators in the spec."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_spec_has_no_raw_locator_calls():
    spec = (ROOT / "tests/ui/agents/test_agent_modules_dropdown.py").read_text()
    assert not re.search(r"\.locator\(|\.nth\(|get_by_", spec)


def test_modules_menu_item_box_is_not_positional():
    src = (ROOT / "pages/agent_detail_page.py").read_text()
    body = src.split("def modules_menu_item_box", 1)[1].split("def ", 1)[0]
    assert ".nth(" not in body
