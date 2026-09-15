"""Social (entity) folders — per-run entity-type draw + entity-type resolver.

ELITEA-3208/3209/3210 (batch ``social-folders-critical``, lead decision on
#2301): each case lists six entity types; the suite draws ONE per test
instead of parametrising 3×6, and nightly runs accumulate coverage. The
four guardrails the lead set, all here:

1. **Log the draw** — ``social-folders: entity_type=<value>`` on stdout +
   an allure attachment, so a red always names its type.
2. **Pin-by-env** — ``SOCIAL_FOLDER_ENTITY_TYPE=<value>`` in ``.env.test``
   (``config.py``; the env FILE beats a shell export) forces the type.
3. **Draw once per test, at setup** — the ``social_folder_entity_type``
   fixture; nothing re-draws mid-test.
4. Re-run a red with the type pinned before classifying it.

The resolver (:class:`EntityTypeBinding`) maps the drawn value to the list
route, the folder API's ``entity_type``, the list page object + its card
locators, the disposable-entity factory/cleanup (API — **transit** per the
AFS § Fidelity Declaration; every folder observable is UI-produced), and
the type's own UI delete path (ELITEA-3210 step 2 — a CASE action, never
substituted). Handles + traffic: ``test-specs/social-folders/_surface.md``.
"""

import logging
import random
import re
import time
from collections.abc import Callable
from dataclasses import dataclass, field

import allure
import pytest
from api import AgentAPI, ArtifactAPI, CredentialAPI, PipelineAPI, SkillAPI, SocialFolderAPI, ToolkitAPI
from config import settings
from pages.agent_detail_page import AgentDetailPage
from pages.agents_list_page import AgentsListPage
from pages.base_page import BasePage
from pages.credential_detail_page import CredentialDetailPage
from pages.credentials_list_page import CredentialsListPage
from pages.mcp_form_page import McpFormPage
from pages.mcp_list_page import McpListPage
from pages.pipeline_detail_page import PipelineDetailPage
from pages.pipelines_list_page import PipelinesListPage
from pages.skill_detail_page import SkillDetailPage
from pages.skills_list_page import SkillsListPage
from pages.toolkit_detail_page import ToolkitDetailPage
from pages.toolkits_list_page import ToolkitsListPage
from playwright.sync_api import Locator, Page

logger = logging.getLogger("elitea.fixtures.social_folders")

# Exactly six — "Toolkits & Indexes" is ONE row (lead brief).
ENTITY_TYPE_POOL = ("agents", "skills", "pipelines", "toolkits_and_indexes", "mcps", "credentials")

_MCP_REMOTE_URL = "https://mcp.deepwiki.com/mcp"  # same as data_fixtures._MCP_DEEPWIKI_URL


@dataclass
class EntityTypeBinding:
    """Everything a social-folders spec needs to know about the drawn type."""

    key: str
    route: str  # list route (bare path — BasePage.navigate adds APP_PREFIX)
    folder_entity_type: str  # the folders API `entity_type`
    list_path_fragment: str  # substring of the entity list GET the folder view filters with `ids=`
    list_url_pattern: re.Pattern  # the list route URL (any query), for post-delete landing waits
    name_code: str  # short code for disposable names
    list_page_cls: type[BasePage]
    cards: Callable[[BasePage], Locator]  # the page-1 card collection
    card_names: Callable[[BasePage], Locator]  # the page-1 card-title collection
    create: Callable[[str], dict]  # API factory → {"id": int, "name": str}
    delete: Callable[[dict], None]  # API cleanup (tolerates already-deleted)
    delete_via_ui: Callable[[Page, dict], None]  # the type's normal entity delete action; ends on the list route
    known_defect_url_fragment: Callable[[dict], str] | None = None  # stale post-delete GET (console 404)
    known_defect_ref: str = ""
    _extra_cleanup: list[Callable[[], None]] = field(default_factory=list)


# ----------------------------------------------------------------------
# The draw
# ----------------------------------------------------------------------
@pytest.fixture
def social_folder_entity_type() -> str:
    """Draw the entity type ONCE per test — or honour the env pin."""
    pinned = (settings.social_folder_entity_type or "").strip()
    if pinned:
        assert pinned in ENTITY_TYPE_POOL, (
            f"SOCIAL_FOLDER_ENTITY_TYPE={pinned!r} is not one of {ENTITY_TYPE_POOL}"
        )
        drawn, how = pinned, "pinned via SOCIAL_FOLDER_ENTITY_TYPE"
    else:
        drawn, how = random.choice(ENTITY_TYPE_POOL), "random draw"
    line = f"social-folders: entity_type={drawn} ({how})"
    print(f"\n{line}")  # stdout — guardrail 1
    logger.info(line)
    allure.attach(line, name="social-folders entity_type", attachment_type=allure.attachment_type.TEXT)
    return drawn


# ----------------------------------------------------------------------
# The resolver
# ----------------------------------------------------------------------
def _stamp() -> str:
    return str(int(time.time() * 1000))[-7:]


def disposable_name(case: str, binding: "EntityTypeBinding", n: int) -> str:
    """``sf-<case>-<code>-<n>-<stamp>`` — lowercase/digits/hyphens, ≤ 32 chars
    (the Skill name format is the strictest of the six)."""
    name = f"sf-{case}-{binding.name_code}-{n}-{_stamp()}"
    assert len(name) <= 32 and re.fullmatch(r"[a-z0-9-]+", name), name
    return name


def disposable_folder_name(case: str, binding: "EntityTypeBinding") -> str:
    """``sf-<case>-<code>-<stamp>`` — the disposable folder's name."""
    return f"sf-{case}-{binding.name_code}-{_stamp()}"


def _wait_for_list_route(page: Page, binding: "EntityTypeBinding", timeout: int = 20000) -> None:
    page.wait_for_url(binding.list_url_pattern, timeout=timeout)


@pytest.fixture
def social_folder_binding(
    social_folder_entity_type: str,
    _browser_cookies,
    skill_api: SkillAPI,
    agent_api: AgentAPI,
    pipeline_api: PipelineAPI,
    credential_api: CredentialAPI,
    toolkit_api: ToolkitAPI,
    artifact_api: ArtifactAPI,
) -> EntityTypeBinding:
    """Resolve the drawn type to routes, page objects, factories and delete paths."""
    key = social_folder_entity_type
    pid = str(settings.elitea_project_id)

    if key == "skills":

        def delete_via_ui(page: Page, entity: dict) -> None:
            SkillsListPage(page).click_skill_card(entity["name"])
            detail = SkillDetailPage(page)
            detail.wait_for_page_load()
            detail.delete_skill_via_menu(entity["name"])  # waits for /skills/all

        return EntityTypeBinding(
            key=key,
            route="/skills/all?viewMode=owner",
            folder_entity_type="skill",
            list_path_fragment=f"/skills/prompt_lib/{pid}",
            list_url_pattern=re.compile(r".*/skills/all/?(\?.*)?$"),
            name_code="sk",
            list_page_cls=SkillsListPage,
            cards=lambda lp: lp.skill_card,
            card_names=lambda lp: lp.skill_card_name,
            create=lambda name: skill_api.create_skill(name, "social-folders disposable", "Reply with OK."),
            delete=lambda e: _tolerant(lambda: skill_api.delete_skill(e["id"])),
            delete_via_ui=delete_via_ui,
            known_defect_url_fragment=lambda e: f"/elitea_core/skill/prompt_lib/{pid}/{e['id']}",
            known_defect_ref="#2303",
        )

    if key == "agents":

        def delete_via_ui(page: Page, entity: dict) -> None:
            AgentsListPage(page).open_card_by_name(entity["name"])
            detail = AgentDetailPage(page)
            detail.wait_for_page_load()
            detail.delete_agent_via_menu()
            _wait_for_list_route(page, binding)

        binding = EntityTypeBinding(
            key=key,
            route="/agents/all?viewMode=owner",
            folder_entity_type="agent",
            list_path_fragment=f"/applications/prompt_lib/{pid}",
            list_url_pattern=re.compile(r".*/agents/all/?(\?.*)?$"),
            name_code="ag",
            list_page_cls=AgentsListPage,
            cards=lambda lp: lp.entity_card,
            card_names=lambda lp: lp.entity_card_name,
            create=lambda name: agent_api.create_agent(name, "social-folders disposable", "Reply with OK."),
            delete=lambda e: _tolerant(lambda: agent_api.delete_agent(e["id"])),
            delete_via_ui=delete_via_ui,
        )
        return binding

    if key == "pipelines":

        def delete_via_ui(page: Page, entity: dict) -> None:
            PipelinesListPage(page).open_pipeline_by_name(entity["name"])
            detail = PipelineDetailPage(page)
            detail.wait_for_detail_page_load()
            detail.delete_pipeline_via_menu()  # product redirect = navigate(-1) → the list we came from
            _wait_for_list_route(page, binding)

        binding = EntityTypeBinding(
            key=key,
            route="/pipelines/all?viewMode=owner",
            folder_entity_type="pipeline",
            list_path_fragment=f"/applications/prompt_lib/{pid}",
            list_url_pattern=re.compile(r".*/pipelines/all/?(\?.*)?$"),
            name_code="pl",
            list_page_cls=PipelinesListPage,
            cards=lambda lp: lp.entity_card,
            card_names=lambda lp: lp.entity_card_name,
            create=lambda name: pipeline_api.create_pipeline(name, "social-folders disposable"),
            delete=lambda e: _tolerant(lambda: pipeline_api.delete_pipeline(e["id"])),
            delete_via_ui=delete_via_ui,
        )
        return binding

    if key == "mcps":

        def delete_via_ui(page: Page, entity: dict) -> None:
            McpListPage(page).open_card_by_name(entity["name"])
            form = McpFormPage(page)
            form.wait_for_page_load()
            form.open_controls_menu()
            form.click_delete_menu_item()
            form.fill_delete_confirm_name(entity["name"])
            form.confirm_delete(pid, entity["id"])  # waits for the DELETE 204 + /mcps/all

        return EntityTypeBinding(
            key=key,
            route="/mcps/all?viewMode=owner",
            folder_entity_type="mcp",
            list_path_fragment=f"/tools/prompt_lib/{pid}",
            list_url_pattern=re.compile(r".*/mcps/all/?(\?.*)?$"),
            name_code="mc",
            list_page_cls=McpListPage,
            cards=lambda lp: lp.mcp_card,
            card_names=lambda lp: lp.mcp_card_name,
            create=lambda name: toolkit_api.create_remote_mcp_toolkit(
                name=name, description="social-folders disposable", url=_MCP_REMOTE_URL, tools=[]
            ),
            delete=lambda e: _tolerant(lambda: toolkit_api.delete_toolkit(e["id"])),
            delete_via_ui=delete_via_ui,
        )

    if key == "toolkits_and_indexes":
        buckets: dict[int, str] = {}

        def create(name: str) -> dict:
            # An Artifact toolkit needs a real bucket (same as data_fixtures.artifact_toolkit).
            artifact_api.create_bucket(name)
            toolkit = toolkit_api.create_artifact_toolkit(name, "social-folders disposable", bucket_name=name)
            buckets[int(toolkit["id"])] = name
            return toolkit

        def delete(entity: dict) -> None:
            _tolerant(lambda: toolkit_api.delete_toolkit(entity["id"]))
            bucket = buckets.pop(int(entity["id"]), None) or entity.get("name")
            _tolerant(lambda: artifact_api.delete_bucket(bucket))

        def delete_via_ui(page: Page, entity: dict) -> None:
            ToolkitsListPage(page).open_card_by_name(entity["name"])
            detail = ToolkitDetailPage(page)
            detail.wait_for_page_load()
            detail.delete_toolkit_via_menu(entity["name"], entity["id"])  # navigate(-1) → the list
            _wait_for_list_route(page, binding)

        binding = EntityTypeBinding(
            key=key,
            route="/toolkits/all",
            folder_entity_type="toolkit",
            list_path_fragment=f"/tools/prompt_lib/{pid}",
            list_url_pattern=re.compile(r".*/toolkits/all/?(\?.*)?$"),
            name_code="tk",
            list_page_cls=ToolkitsListPage,
            cards=lambda lp: lp.entity_card,
            card_names=lambda lp: lp.entity_card_name,
            create=create,
            delete=delete,
            delete_via_ui=delete_via_ui,
        )
        return binding

    if key == "credentials":

        def create(name: str) -> dict:
            # Same shape as data_fixtures.invalid_github_credential — no real
            # secret is needed; the card shows `label`.
            cred = credential_api.create_credential(
                {
                    "type": "github",
                    "elitea_title": f"{name}-title",
                    "label": name,
                    "data": {
                        "base_url": "https://api.github.com",
                        "access_token": "ghp_socialfolders0000000000000000000",
                    },
                    "shared": False,
                }
            )
            return {"id": cred["id"], "name": name}

        def delete_via_ui(page: Page, entity: dict) -> None:
            CredentialsListPage(page).click_credential_card(entity["name"])
            detail = CredentialDetailPage(page)
            detail.wait_for_page_load()
            detail.open_controls_menu()
            detail.open_delete_dialog()
            detail.fill_delete_confirm_name(entity["name"])
            detail.confirm_delete(str(entity["id"]))
            _wait_for_list_route(page, binding)

        binding = EntityTypeBinding(
            key=key,
            route="/credentials/all",
            folder_entity_type="configuration",
            list_path_fragment="/configurations/configurations/",
            list_url_pattern=re.compile(r".*/credentials/all/?(\?.*)?$"),
            name_code="cr",
            list_page_cls=CredentialsListPage,
            cards=lambda lp: lp.entity_card,
            card_names=lambda lp: lp.entity_card_name,
            create=create,
            delete=lambda e: _tolerant(lambda: credential_api.delete_credential(e["id"])),
            delete_via_ui=delete_via_ui,
            known_defect_url_fragment=lambda e: f"/configurations/configuration/{pid}/{e['id']}",
            known_defect_ref="#1666",
        )
        return binding

    raise AssertionError(f"unknown social-folders entity type {key!r}")


def _tolerant(call: Callable[[], None]) -> None:
    """Run a cleanup call; log (never raise) when the resource is already gone."""
    try:
        call()
    except Exception as exc:  # noqa: BLE001 — teardown must keep going
        logger.warning("social-folders cleanup: %s", exc)


# ----------------------------------------------------------------------
# Disposable entities + folder teardown
# ----------------------------------------------------------------------
@pytest.fixture
def social_folder_api(_browser_cookies) -> SocialFolderAPI:
    api = SocialFolderAPI(browser_cookies=_browser_cookies)
    yield api
    api.close()


@pytest.fixture
def social_folder_cleanup(social_folder_api: SocialFolderAPI, social_folder_binding: EntityTypeBinding):
    """Loud teardown registry. Register ids the MOMENT they exist (the 201
    arrives → register → then act), per testing.md § Teardown-guard ordering.

    ``register_folder(folder_id)`` / ``register_entity(entity)``; teardown
    deletes entities first (API), then the folder (API, 404 tolerated when
    the case itself deleted it). A leaked folder pushes the panel toward
    ``VISIBLE_FOLDER_COUNT = 6`` — never skip this."""
    folders: list[int] = []
    entities: list[dict] = []

    class _Registry:
        def register_folder(self, folder_id: int) -> None:
            folders.append(int(folder_id))

        def register_entity(self, entity: dict) -> dict:
            entities.append(entity)
            return entity

    yield _Registry()

    for entity in entities:
        social_folder_binding.delete(entity)
    for folder_id in folders:
        status = social_folder_api.delete_folder(folder_id)
        logger.info("teardown: DELETE folder %s → %s", folder_id, status)


def create_disposable_entities(
    binding: EntityTypeBinding, cleanup, case: str, count: int
) -> list[dict]:
    """Seed *count* unfiled entities of the drawn type via the API (transit —
    AFS § Fidelity Declaration) and register each for teardown."""
    created: list[dict] = []
    for n in range(1, count + 1):
        name = disposable_name(case, binding, n)
        raw = binding.create(name)
        entity = cleanup.register_entity({"id": int(raw["id"]), "name": raw.get("name", name)})
        logger.info("seeded %s entity %s (%s)", binding.key, entity["id"], entity["name"])
        created.append(entity)
    return created
