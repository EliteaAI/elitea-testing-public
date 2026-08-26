"""Regression test for the ``project_context_seed`` fixture and its three
callers (ELITEA-2266 / ELITEA-2267 / ELITEA-2276, review round 1, fix round 1).

Guards the defect a fresh-session reviewer flagged: the fixture's ``PUT``
carries BOTH ``content`` and the ``enabled`` flag, but only the content seed
was declared as a transit substitution. The flag is not incidental — three
case elements read it as product state or as a user action:

* ELITEA-2266 step 6 — "An ON/OFF toggle (enabled by default)"
* ELITEA-2267 step 2 — "Verify the toggle is ON by default"
* ELITEA-2276 step 6 — "Turn the Project Context toggle ON" (an ACTION)

Seeding ``enabled=True`` and then asserting the switch is checked reads the
case's own observable off a value the test authored — a **terminal**
substitution under ``.agents/testing.md`` § Fidelity policy, and (for
ELITEA-2276 step 6) a user action replaced by an API write. The shipped fix is
threefold and each part is pinned below:

1. ``_seed``'s ``enabled`` parameter defaults to ``None``, meaning "carry the
   product's own flag forward" — the callable ``GET``s the resource and echoes
   its value, mirroring ``serverData?.enabled ?? true``.
2. The three "default ON" callers pass no ``enabled`` at all.
3. ELITEA-2276 performs BOTH of its toggle steps (2 and 6) as real clicks on
   the real switch, waited on the product's own ``PUT``.

A future edit that re-introduces ``enabled=True`` as the way to reach an
asserted toggle state fails here instead of shipping a green tautology.
"""

import ast
import re
from pathlib import Path

import pytest

TESTS_UNIT_DIR = Path(__file__).resolve().parent
AUTOMATION_DIR = TESTS_UNIT_DIR.parent.parent  # .../automation

FIXTURES_PATH = AUTOMATION_DIR / "fixtures" / "data_fixtures.py"
ADMIN_TESTS_DIR = AUTOMATION_DIR / "tests" / "ui" / "admin"

FIXTURE_NAME = "project_context_seed"
SEED_CALLABLE_NAME = "_seed"

SPEC_2276 = ADMIN_TESTS_DIR / "test_project_context_empty_save_toggle_off_on.py"
#: ELITEA-2276 case steps 2 and 6 are both toggle ACTIONS — one real click each.
EXPECTED_TOGGLE_CLICKS_2276 = 2
TOGGLE_CLICK_CALL = "click_enable_toggle_and_wait_for_put"

#: Callers whose case text makes the enable flag an OBSERVABLE ("ON by default"),
#: so they must not author it at all.
DEFAULT_ON_SPECS = (
    ADMIN_TESTS_DIR / "test_project_context_page_layout.py",  # ELITEA-2266 step 6
    ADMIN_TESTS_DIR / "test_project_context_toggle_enable_disable.py",  # ELITEA-2267 step 2
)


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


@pytest.fixture(scope="module")
def seed_callable_def() -> ast.FunctionDef:
    """The nested ``_seed`` callable the ``project_context_seed`` fixture yields."""
    for node in ast.walk(_parse(FIXTURES_PATH)):
        if isinstance(node, ast.FunctionDef) and node.name == FIXTURE_NAME:
            for inner in ast.walk(node):
                if isinstance(inner, ast.FunctionDef) and inner.name == SEED_CALLABLE_NAME:
                    return inner
    pytest.fail(f"{FIXTURE_NAME}.{SEED_CALLABLE_NAME} not found in {FIXTURES_PATH}")


def _seed_calls(path: Path) -> list[ast.Call]:
    return [
        node
        for node in ast.walk(_parse(path))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == FIXTURE_NAME
    ]


def _enabled_kwarg(call: ast.Call) -> ast.keyword | None:
    return next((kw for kw in call.keywords if kw.arg == "enabled"), None)


class TestSeedDoesNotAuthorTheEnableFlag:
    """The fixture must not author ``enabled`` unless a caller explicitly asks."""

    def test_enabled_parameter_defaults_to_none(self, seed_callable_def):
        """``None`` is what makes "carry the product's flag forward" the default.

        A ``True`` default silently re-authors the flag for every caller — the
        exact shape the reviewer blocked.
        """
        args = seed_callable_def.args
        assert "enabled" in [a.arg for a in args.args], "_seed lost its 'enabled' parameter"

        index = [a.arg for a in args.args].index("enabled")
        # Defaults align to the TAIL of args.args.
        offset = index - (len(args.args) - len(args.defaults))
        assert offset >= 0, "'enabled' must carry a default"
        default = args.defaults[offset]

        assert isinstance(default, ast.Constant) and default.value is None, (
            "_seed's 'enabled' must default to None ('carry the product's own flag "
            "forward'), never to a literal the test authors — ELITEA-2266/2267/2276 "
            "read that flag as the case's own observable."
        )

    def test_default_path_reads_the_flag_from_the_product(self, seed_callable_def):
        """With no explicit flag the callable must GET before it PUTs."""
        source = ast.unparse(seed_callable_def)
        assert "_current_enabled" in source, (
            "_seed no longer carries the product's own enable flag forward. The "
            "default path must read the flag off the API (mirroring the product's "
            "`serverData?.enabled ?? true`) rather than inventing one."
        )


class TestDefaultOnSpecsAuthorNothing:
    """ELITEA-2266 / ELITEA-2267 assert "ON by default" — so they must not seed it."""

    @pytest.mark.parametrize("spec_path", DEFAULT_ON_SPECS, ids=lambda p: p.stem)
    def test_spec_passes_no_enabled_argument(self, spec_path):
        calls = _seed_calls(spec_path)
        assert calls, f"{spec_path.name} no longer calls {FIXTURE_NAME}"

        authored = [call for call in calls if _enabled_kwarg(call) is not None]
        assert not authored, (
            f"{spec_path.name} passes an explicit 'enabled' to {FIXTURE_NAME}. Its case "
            f"asserts the toggle is ON BY DEFAULT, so the flag is the observable — "
            f"seeding it makes that assertion a tautology (terminal substitution, "
            f".agents/testing.md § Fidelity policy)."
        )


class TestEmptySaveSpecPerformsBothToggleActions:
    """ELITEA-2276 steps 2 and 6 are ACTIONS — a real click each, never a re-seed."""

    def test_both_toggle_steps_are_real_clicks(self):
        source = SPEC_2276.read_text(encoding="utf-8")
        clicks = len(re.findall(rf"\b{TOGGLE_CLICK_CALL}\(", source))
        assert clicks == EXPECTED_TOGGLE_CLICKS_2276, (
            f"ELITEA-2276 must turn the toggle OFF (case step 2) and back ON (case step 6) "
            f"by real clicks on the real switch — expected {EXPECTED_TOGGLE_CLICKS_2276} "
            f"{TOGGLE_CLICK_CALL}() calls, found {clicks}. Satisfying step 6 by re-seeding "
            f"'enabled=True' replaces a user ACTION with an API write and then reads the "
            f"step's observable off it."
        )

    def test_the_on_state_is_never_seeded(self):
        """Any explicit flag in this spec must be the OFF precondition, not ON."""
        for call in _seed_calls(SPEC_2276):
            kwarg = _enabled_kwarg(call)
            if kwarg is None:
                continue
            assert isinstance(kwarg.value, ast.Constant) and kwarg.value.value is False, (
                "ELITEA-2276 may seed 'enabled=False' (restoring the OFF precondition its "
                "own real click produced, so case step 6 has a control to act on) — never "
                "'enabled=True', which would author case step 6's observable."
            )

    def test_the_off_precondition_is_asserted_before_the_on_click(self):
        """The pre-click assertion is what makes the ON state a product-produced change."""
        source = SPEC_2276.read_text(encoding="utf-8")
        assert "not_to_be_checked()" in source and "to_be_checked()" in source, (
            "ELITEA-2276 must assert the switch is UNCHECKED before case step 6's click and "
            "CHECKED after it — otherwise a regression back to a seeded ON state passes "
            "silently."
        )
