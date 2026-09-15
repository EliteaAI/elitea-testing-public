"""Social (entity) folders — the FOLDERS panel on the private entity lists.

Reusable component object for ``EliteaUI/src/[fsd]/entities/folder/``
(``FolderSection.jsx`` + its dialogs, menus and the folder-view header),
which mounts on six lists: agents, skills, pipelines, toolkits & indexes,
MCPs, credentials. It is a SEPARATE implementation from chat folders
(``chat-folder-*`` testids, ``chat_page.py`` helpers) — never mix the two.

Built for ELITEA-3208/3209/3210 (batch ``social-folders-critical``, lead
brief § Framework work). Handles + traffic: ``test-specs/social-folders/
_surface.md``. Locators are class-level ``LocatorDescriptor(testid=…)``
fields or UPPER_CASE ``[data-testid="…-{}"]`` template constants for the
id-keyed (dynamic) testids — never built in method bodies.

Folder-view state lives in the URL (``?folder=<id>``, ``useFolderView``):
open = param set, close/delete = param removed. Every method that changes
that state waits on the product's own network signal, never on a sleep.
"""

import logging
import re
from urllib.parse import parse_qs, urlparse

from config import settings
from pages.locator_descriptor import LocatorDescriptor
from playwright.sync_api import Locator, Page, Response, expect
from utils.actions import action

logger = logging.getLogger("elitea.components.folder_section")

UI_ELEMENT_TIMEOUT = 10000
RESPONSE_TIMEOUT = 15000


class FolderSection:
    """The FOLDERS panel, its dialogs/menus, and the open-folder header."""

    # ------------------------------------------------------------------
    # Panel + create dialog (FolderSection.jsx / CreateFolderDialog.jsx)
    # ------------------------------------------------------------------
    create_button = LocatorDescriptor(
        testid="folders-panel-create-btn",
        description="'+' in the FOLDERS panel header — opens the create dialog",
    )
    create_dialog = LocatorDescriptor(
        testid="create-folder-dialog",
        description="Create/Edit folder dialog (Modal.BaseModal)",
    )
    # `create-folder-name-input` lands on the MUI TextField ROOT <div>; the
    # <input> is a descendant. Same scoped-descendant shape as
    # oauth_auth_modal_page.py:91 (testid parent + `input`).
    CREATE_FOLDER_NAME_INPUT_FIELD = '[data-testid="create-folder-name-input"] input'
    create_submit_button = LocatorDescriptor(
        testid="create-folder-submit-btn",
        description="Create dialog — Save (disabled while the name is empty)",
    )
    create_cancel_button = LocatorDescriptor(
        testid="create-folder-cancel-btn",
        description="Create dialog — Cancel",
    )

    # ------------------------------------------------------------------
    # Folder rows (FolderItem.jsx) — keyed by the folder's numeric id, which
    # the caller reads from the POST 201 body (never from DOM text).
    # ------------------------------------------------------------------
    FOLDER_ITEM = '[data-testid="folder-item-{}"]'
    FOLDER_ITEM_COUNT = '[data-testid="folder-item-count-{}"]'
    # opacity 0 until the row is hovered — hover the row first
    FOLDER_ITEM_MENU_BTN = '[data-testid="folder-item-menu-btn-{}"]'

    # Folder actions menu (FolderActionsMenu.jsx)
    menu_delete_item = LocatorDescriptor(
        testid="folder-menu-delete",
        description="Folder ⋮ menu — Delete",
    )
    # Shared Modal.DeleteEntityModal (the `delete-folder-dialog` testid that
    # DeleteFolderDialog.jsx passes is dead at runtime — the modal hardcodes
    # its own ids). Folder delete needs NO type-to-confirm.
    delete_confirm_dialog = LocatorDescriptor(
        testid="delete-confirm-dialog",
        description="Shared delete-confirmation modal",
    )
    delete_confirm_button = LocatorDescriptor(
        testid="delete-confirm-button",
        description="Shared delete-confirmation modal — Delete",
    )

    # ------------------------------------------------------------------
    # Open-folder header (FolderViewHeader.jsx) + list empty state
    # ------------------------------------------------------------------
    header_name = LocatorDescriptor(
        testid="folder-view-header-name",
        description="Open-folder header — folder name",
    )
    header_count = LocatorDescriptor(
        testid="folder-view-header-count",
        description="Open-folder header — '(N)' count",
    )
    close_button = LocatorDescriptor(
        testid="folder-view-close-btn",
        description="Open-folder header — Close folder",
    )
    empty_state = LocatorDescriptor(
        testid="folder-empty-state",
        description="'No items in this folder yet' (all 5 list components)",
    )

    # ------------------------------------------------------------------
    # Card-level move-to-folder (MoveToFolderButton.jsx / FolderMenuContent.jsx)
    # ------------------------------------------------------------------
    MOVE_TO_FOLDER_BTN = '[data-testid="move-to-folder-btn-{}"]'  # {} = entity id; opacity 0 until hover
    MOVE_TO_FOLDER_MENU_FOLDER = '[data-testid="move-to-folder-menu-folder-{}"]'  # {} = folder id
    move_menu_remove_item = LocatorDescriptor(
        testid="move-to-folder-menu-remove-item",
        description="Move-to-folder menu — 'Remove from folder' (renders only for a FILED entity)",
    )

    def __init__(self, page: Page, entity_type: str):
        """
        Args:
            page: Playwright page, already on one of the six entity lists.
            entity_type: the folder API's ``entity_type`` for that list
                (``skill`` / ``agent`` / ``pipeline`` / ``toolkit`` / ``mcp`` /
                ``configuration``) — used to match the folders refetch.
        """
        self.page = page
        self.entity_type = entity_type
        self.project_id = str(settings.elitea_project_id)

    # ------------------------------------------------------------------
    # Locator accessors for the id-keyed testids
    # ------------------------------------------------------------------
    def folder_item(self, folder_id: int) -> Locator:
        return self.page.locator(self.FOLDER_ITEM.format(folder_id))

    def folder_item_count(self, folder_id: int) -> Locator:
        return self.page.locator(self.FOLDER_ITEM_COUNT.format(folder_id))

    def folder_item_menu_button(self, folder_id: int) -> Locator:
        return self.page.locator(self.FOLDER_ITEM_MENU_BTN.format(folder_id))

    def create_name_input(self) -> Locator:
        return self.create_dialog.locator(self.CREATE_FOLDER_NAME_INPUT_FIELD)

    def move_to_folder_button(self, entity_id: int) -> Locator:
        return self.page.locator(self.MOVE_TO_FOLDER_BTN.format(entity_id))

    def move_menu_folder_item(self, folder_id: int) -> Locator:
        return self.page.locator(self.MOVE_TO_FOLDER_MENU_FOLDER.format(folder_id))

    # ------------------------------------------------------------------
    # URL state
    # ------------------------------------------------------------------
    def url_folder_param(self) -> str | None:
        """The ``folder`` search param of the current URL (``None`` when closed)."""
        values = parse_qs(urlparse(self.page.url).query).get("folder")
        return values[0] if values else None

    def expect_folder_param(self, folder_id: int | None, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Auto-retrying assertion on the URL's ``folder`` param.

        ``folder_id=None`` asserts the param is ABSENT (folder closed).
        """
        if folder_id is None:
            expect(self.page).not_to_have_url(re.compile(r"[?&]folder="), timeout=timeout)
        else:
            expect(self.page).to_have_url(re.compile(rf"[?&]folder={folder_id}(&|$)"), timeout=timeout)

    # ------------------------------------------------------------------
    # Response predicates (all under /api/v2 — `_surface.md` § Backend traffic)
    # ------------------------------------------------------------------
    def _is_folders_count_refetch(self, r: Response) -> bool:
        return (
            r.request.method == "GET"
            and f"/social/folders/prompt_lib/{self.project_id}" in r.url
            and f"entity_type={self.entity_type}" in r.url
            and "include_counts=true" in r.url
        )

    def _is_folder_items_get(self, r: Response, folder_id: int) -> bool:
        return (
            r.request.method == "GET"
            and f"/social/folder_items/prompt_lib/{self.project_id}/{folder_id}" in r.url
        )

    @staticmethod
    def is_entity_list_get(r: Response, list_path_fragment: str, filtered: bool) -> bool:
        """Match the entity list GET — ``filtered=True`` requires an ``ids=``
        param (folder view), ``False`` requires its ABSENCE (complete list)."""
        if r.request.method != "GET" or list_path_fragment not in r.url:
            return False
        has_ids = "ids=" in urlparse(r.url).query
        return has_ids if filtered else not has_ids

    @staticmethod
    def list_get_ids(r: Response) -> set[str]:
        """The ``ids`` param of a folder-filtered list GET, as a set of strings."""
        values = parse_qs(urlparse(r.url).query).get("ids", [])
        return {v for csv in values for v in csv.split(",") if v}

    def wait_for_count_refetch(self, timeout: int = RESPONSE_TIMEOUT) -> Response:
        """Block until the NEXT ``include_counts=true`` folders GET resolves."""
        return self.page.wait_for_event(
            "response", self._is_folders_count_refetch, timeout=timeout
        )

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    @action("Create a folder via the panel dialog")
    def create_folder(self, name: str, timeout: int = RESPONSE_TIMEOUT) -> tuple[int, Response]:
        """Create *name* through the UI; return ``(folder_id, POST response)``.

        The id comes from the ``POST /social/folders/prompt_lib/{pid}`` 201
        body — it keys every ``folder-item-{id}`` locator.
        """
        self.create_button.click()
        self.create_dialog.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        self.create_name_input().fill(name)
        with self.page.expect_response(
            lambda r: r.request.method == "POST"
            and r.url.rstrip("/").endswith(f"/social/folders/prompt_lib/{self.project_id}"),
            timeout=timeout,
        ) as post_info:
            self.create_submit_button.click()
        response = post_info.value
        assert response.status == 201, f"Create folder returned HTTP {response.status}: {response.text()[:300]}"
        folder_id = int(response.json()["id"])
        self.create_dialog.wait_for(state="hidden", timeout=UI_ELEMENT_TIMEOUT)
        logger.info("Created folder %r id=%s (entity_type=%s)", name, folder_id, self.entity_type)
        return folder_id, response

    @action("Open a folder from the panel")
    def open_folder(
        self,
        folder_id: int,
        list_path_fragment: str,
        expected_ids: set[str] | None = None,
        timeout: int = RESPONSE_TIMEOUT,
    ) -> Response | None:
        """Click the folder row and wait until the folder view is open.

        With *expected_ids* (the FIRST open of a folder whose membership just
        changed): also wait for the ``folder_items`` GET and for the
        folder-FILTERED entity list GET whose ``ids`` set == *expected_ids*
        (``{"0"}`` for an empty folder — the product's sentinel), and return
        that list response. Why the ids are matched, not just ``ids=``
        presence: ``useFolderItems`` (``useFolderEntities.hooks.js``) returns
        ``idsQueryParam='0'`` while the folder_items query is still LOADING,
        so a non-empty folder first fires a transient ``ids=0`` list GET and
        then the real one (observed live on the MCP list, ELITEA-3209).

        Without *expected_ids* (a RE-open): RTK Query serves ``folder_items``
        — and often the list query itself — from cache, so no request is
        guaranteed to fire (observed live on skills, ELITEA-3210 step 3:
        3/3 timeouts when the reopen waited on the network). The open state
        is then taken from the product's own signals — the URL ``folder``
        param and the header rendering — and callers assert counts/cards
        through auto-retrying expectations. Returns ``None``."""
        if expected_ids is None:
            self.folder_item(folder_id).click()
            self.expect_folder_param(folder_id, timeout=timeout)
            self.header_count.wait_for(state="visible", timeout=timeout)
            return None
        with self.page.expect_response(
            lambda r: self.is_entity_list_get(r, list_path_fragment, filtered=True)
            and self.list_get_ids(r) == expected_ids,
            timeout=timeout,
        ) as list_info, self.page.expect_response(
            lambda r: self._is_folder_items_get(r, folder_id), timeout=timeout
        ):
            self.folder_item(folder_id).click()
        return list_info.value

    @action("Close the open folder via the header")
    def close_folder(
        self, list_path_fragment: str, wait_for_list: bool = True, timeout: int = RESPONSE_TIMEOUT
    ) -> Response | None:
        """Click the header's close button.

        ``wait_for_list=True`` (the case's own "complete list" observable —
        ELITEA-3208 step 3): wait for the UNFILTERED list GET (no ``ids=``)
        and return it. ``False`` (a repeat close inside one mount, where RTK
        Query may serve the unfiltered list from cache and fire nothing):
        wait on the URL ``folder`` param being removed instead."""
        if not wait_for_list:
            self.close_button.click()
            self.expect_folder_param(None, timeout=timeout)
            self._wait_until_closed_committed(timeout)
            return None
        with self.page.expect_response(
            lambda r: self.is_entity_list_get(r, list_path_fragment, filtered=False), timeout=timeout
        ) as list_info:
            self.close_button.click()
        self._wait_until_closed_committed(timeout)
        return list_info.value

    def _wait_until_closed_committed(self, timeout: int) -> None:
        """The folder-view state is derived from the URL (``useFolderView``),
        but the row's click handler closes over the LAST RENDERED
        ``selectedFolderId``: a click that lands after the URL param is gone
        yet before React re-renders is treated as "same folder → toggle
        closed" (observed live, ELITEA-3210 step 3 — the reopen click no-oped).
        The header is rendered only while a folder is selected, so its
        disappearance is the commit signal."""
        self.header_count.wait_for(state="hidden", timeout=timeout)

    @action("Delete a folder via its ⋮ menu")
    def delete_folder(self, folder_id: int, timeout: int = RESPONSE_TIMEOUT) -> Response:
        """Hover the row, open ⋮ → Delete, confirm; wait for the DELETE 204.
        Asserts NO dialog/toast copy (EliteaAI/elitea_issues#6480 is open)."""
        row = self.folder_item(folder_id)
        row.hover()
        self.folder_item_menu_button(folder_id).click()
        self.menu_delete_item.click()
        self.delete_confirm_dialog.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        with self.page.expect_response(
            lambda r: r.request.method == "DELETE"
            and r.url.rstrip("/").endswith(f"/social/folder/prompt_lib/{self.project_id}/{folder_id}"),
            timeout=timeout,
        ) as delete_info:
            self.delete_confirm_button.click()
        response = delete_info.value
        assert response.status == 204, f"Delete folder returned HTTP {response.status}"
        return response

    def open_move_menu(self, entity_id: int) -> None:
        """Hover the card's move-to-folder button (opacity 0 until hover) and click it."""
        button = self.move_to_folder_button(entity_id)
        button.hover()
        button.click()

    def close_move_menu(self) -> None:
        self.page.keyboard.press("Escape")

    def _expect_move_put(self, timeout: int):
        return self.page.expect_response(
            lambda r: r.request.method == "PUT"
            and r.url.rstrip("/").endswith(f"/social/move_to_folder/prompt_lib/{self.project_id}"),
            timeout=timeout,
        )

    @action("Move an entity into a folder via the card menu")
    def move_entity_to_folder(
        self, entity_id: int, folder_id: int, timeout: int = RESPONSE_TIMEOUT
    ) -> tuple[dict, Response]:
        """Card ⋯ → the folder's menu row; wait for the PUT 200 and the
        ``include_counts=true`` folders refetch that updates the panel count.
        Returns ``(PUT body, refetch response)`` — the PUT body's ``folder_id``
        echoes the target; the refetch body carries ``entities_count``."""
        self.open_move_menu(entity_id)
        with self.page.expect_response(
            self._is_folders_count_refetch, timeout=timeout
        ) as refetch_info, self._expect_move_put(timeout) as put_info:
            self.move_menu_folder_item(folder_id).click()
        response = put_info.value
        assert response.status == 200, f"move_to_folder returned HTTP {response.status}: {response.text()[:300]}"
        body = response.json()
        assert body.get("folder_id") == folder_id, (
            f"move_to_folder echoed folder_id={body.get('folder_id')!r}, expected {folder_id}"
        )
        return body, refetch_info.value

    @action("Remove an entity from its folder via the card menu")
    def remove_entity_from_folder(self, entity_id: int, timeout: int = RESPONSE_TIMEOUT) -> tuple[dict, Response]:
        """Card ⋯ → 'Remove from folder'; wait for the PUT 200 (``folder_id``
        null) and the counts refetch. Returns ``(PUT body, refetch response)``."""
        self.open_move_menu(entity_id)
        with self.page.expect_response(
            self._is_folders_count_refetch, timeout=timeout
        ) as refetch_info, self._expect_move_put(timeout) as put_info:
            self.move_menu_remove_item.click()
        response = put_info.value
        assert response.status == 200, f"move_to_folder(remove) returned HTTP {response.status}"
        body = response.json()
        assert body.get("folder_id") is None, f"remove-from-folder echoed folder_id={body.get('folder_id')!r}"
        return body, refetch_info.value

    @staticmethod
    def entities_count_from_refetch(refetch: Response, folder_id: int) -> int | None:
        """``entities_count`` of *folder_id* in an ``include_counts=true`` folders body."""
        for folder in refetch.json().get("folders", []):
            if int(folder.get("id", -1)) == int(folder_id):
                return folder.get("entities_count")
        return None
