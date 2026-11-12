# Test Case: Chat - Context window mode (Balanced/Full) set in personal settings reflects in a new chat's Context Management widget

## Metadata
- **TMS ID**: ELITEA-3744
- **Priority**: l1 (case: high)
- **Environment Explored**: DEV `https://dev.elitea.ai/app` (scratch pytest + CDP-free headless Playwright with framework auth), project Private; frontend source EliteaUI `origin/main` (#6898)
- **User set**: `${TEST_USER}`
- **Status**: ready-for-automation (adjusted existing test, in place)
- **surface_key**: `chat-context-management`
- **Triage class**: A (intent preserved, mechanism changed: numeric Max Context Tokens field -> Balanced/Full radio, product change elitea_issues#6898)

## Preconditions
- Logged in. Test records the user's original mode, restores it in `finally`, deletes its conversation via `conversation_api`.

## Steps (observed live)
1. `/settings/memory` shows "Context window" radio group: Balanced ("Up to 272,000 tokens. Keeps costs down.") / Full. Default Balanced.
2. Click Full -> autosave (`PUT /social/author/`, `PUT /social/module_settings/<project>`); after reload Full is still checked. Same for Balanced.
3. New chat; send message; AI answers.
4. Expand Participants panel: Context management widget shows `Balanced · 272K` / `Full · 400K` toggle tabs (selected tab `aria-pressed=true`) and "of N tokens" (N = window - safety margin; Balanced/Haiku 5.5 -> 269 280).
5. Selected mode matches the personal setting for both values; window = model window (Full) or min(272000, model window) (Balanced).

## Handles Reference
| rung | handle | suggested_testid | provenance |
|---|---|---|---|
| 1 | `memory-context-window-mode` | - | testid on DEV ✓ |
| 1 | `context-window-mode-balanced` / `-full` (settings label AND widget button; scope separates them) | - | testid on DEV ✓ |
| ladder | `input[type="radio"]` within settings option label (checked state) | `memory-context-window-mode-radio` | css, scoped (ScopedLocator `context_window_option_radio`) - no testid on DEV |
| 1 | `context-budget-panel`, `context-budget-tokens`, `chat-participants-panel-toggle-button`, `model-selector-name`, `chat-copy-text-button` | - | testid on DEV ✓ |

## Coverage Map
| Case element | Expected | Covered by | Disposition |
|---|---|---|---|
| Step 1 Settings -> Memory radio | group with Balanced/Full | `context_window_mode_group` visible | asserted |
| Step 2 select + autosave + reload | persisted | `select_context_window_mode` (waits on PUT) then reload and `get_context_window_mode() == mode` | asserted |
| Step 3 new conversation | fresh chat | `click_create_conversation` | setup |
| Step 4 send message, widget visible | widget appears | send, wait for answer, `context-budget-panel` visible | asserted |
| Step 5 Window mode shown | Full / Balanced | widget `aria-pressed` selected tab == mode | asserted |
| Step 5/6 Total window | Full = model window; Balanced = min(272000, model window) | tab label `<Mode> · <size>` == values from model catalog API (independent oracle); "of N tokens" within [0.9, 1.0] x window | asserted |
| Step 6 repeat with other mode, no stale cache | updated mode shows | second parametrized run (balanced_mode after full_mode) | asserted |

## Adjustment
- **What changed**: old test set a numeric Max Context Tokens (10k/32k) and read "N / M tokens" from a "Context Budget" panel; both removed by #6898. Now Balanced/Full radio and a "Context management" widget with window-size tabs.
- **Params**: `10k_tokens`/`32k_tokens` -> `full_mode`/`balanced_mode`; skip removed.
- **Expected-result changes**: legitimate, from the rewritten TMS case: "panel shows exact profile max tokens" -> "widget shows matching Window mode and the model's window (Full) / min(272000, window) (Balanced)". No assertion was weakened; the "Total window" is verified against the model catalog API, not read back from the widget.
- **Clarification**: DEV renders no literal "Total window" label; the window size is the mode tab's suffix (`Full · 400K`) and the "of N tokens" line. Sizes are rounded to K/M by the UI, so equality is on the rounded label plus the 10% usable-margin band on N.
