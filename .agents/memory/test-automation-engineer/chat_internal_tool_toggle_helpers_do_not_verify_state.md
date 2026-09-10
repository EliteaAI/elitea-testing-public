---
name: ChatPage internal-tool toggle helpers do not verify the resulting state
description: enable_/disable_image_creation click and immediately Escape; assert with is_image_creation_enabled() if the case's expected result is the toggle state
type: reference
---

Read live 2026-09-09 (`automation/pages/chat_page.py`, branch
`fix/2112-image-creation-default-model`, on `main`).

`enable_image_creation(timeout)` (line ~3439) and `disable_image_creation`:

```python
image_switch.wait_for(state="visible", timeout=timeout)
is_checked = image_switch.is_checked()
if not is_checked:
    image_switch.click()
    logger.info("Image creation enabled")
self.page.keyboard.press("Escape")
self.page.wait_for_timeout(300)
```

It reads state **before** clicking, then presses Escape. There is **no
post-click re-read, wait, or raise** — so calling it proves the switch was
found and clicked, never that it landed checked. A test whose case step has the
expected result *"tool is toggled ON"* is exercising it but not asserting it.

`is_image_creation_enabled(timeout) -> bool` (line ~3496) is the verification
helper. It reopens the Modules menu when the switch is not already in the DOM
(the menu is closed by the preceding Escape), reads `is_checked()`, Escapes
again. Cost: one extra menu open/close, measured negligible against a ~60s
image-generation step.

The only thing `enable_image_creation` *raises* is
`FeatureNotAvailableError`, and only from `open_internal_tools_menu` when the
plus-menu button is not visible — a feature-absence signal, not a state check.
Do not catch it into a `pytest.skip`: that is defect masking, and it is
precisely the UI-drift condition the suite exists to surface (removed from
`test_image_creation.py` in #2112 by lead ruling).

Both helpers still use the pre-existing raw handle
`get_by_role("switch", name="Image creation")` — tracked tech debt (#25/#42).
The switch already carries testid `modules-toggle-image_generation`; migrating
these helpers is available but separate work.
