"""Semantic action decorator for step logging.

Usage::

    from utils.actions import action

    class MyPage(BasePage):

        @action("Send message to chat")
        def send_message(self, text: str, use_enter: bool = False):
            ...

Each decorated method call logs ``→ description(params)`` / ``← description``
at INFO level via the ``elitea.steps`` logger.
On failure a full-page screenshot is attached to the log before the exception
is re-raised.
"""

import functools
import inspect
import logging

logger = logging.getLogger("elitea.steps")


def _build_params(func, bound_args) -> dict:
    """Extract call params, excluding ``self``, ``timeout*``, and ``_*``.

    Note: VAR_KEYWORD (``**kwargs``) params are included as a single dict
    and their internal keys are not filtered. If a page object method accepts
    ``**kwargs`` containing a ``timeout`` key, that key will not be stripped.
    """
    return {
        k: v
        for k, v in bound_args.arguments.items()
        if k != "self"
        and not k.startswith("timeout")
        and not k.startswith("_")
    }


def _capture_failure(page, step_description: str, func_name: str, exc: Exception) -> None:
    """Attach a screenshot to the log on action failure."""
    if page is None:
        logger.error("Step failed: %s — %s", step_description, exc)
        return
    try:
        screenshot_bytes = page.screenshot(full_page=True)
        logger.error(
            "Step failed: %s — %s",
            step_description,
            exc,
            extra={
                "attachment": {
                    "name": f"{func_name}_fail.png",
                    "data": screenshot_bytes,
                    "mime": "image/png",
                }
            },
        )
    except Exception:
        logger.error("Step failed (screenshot unavailable): %s — %s", step_description, exc)


def action(description: str | None = None):
    """Mark a page object method as a semantic step for logging.

    Args:
        description: Human-readable step name.
                     Defaults to the method name when omitted.
    """
    if callable(description):
        raise TypeError(
            "@action must be called: use @action() or @action('desc'), not @action"
        )

    def decorator(func):
        step_description = description or func.__name__

        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            sig = inspect.signature(func)
            bound = sig.bind(self, *args, **kwargs)
            bound.apply_defaults()
            params = _build_params(func, bound)

            def _run():
                try:
                    return func(self, *args, **kwargs)
                except Exception as exc:
                    _capture_failure(
                        getattr(self, "page", None),
                        step_description,
                        func.__name__,
                        exc,
                    )
                    raise

            params_str = ", ".join(f"{k}={repr(v)}" for k, v in params.items())
            label = f"{step_description}({params_str})" if params_str else step_description
            logger.info("→ %s", label)
            result = _run()
            logger.info("← %s", step_description)
            return result

        return wrapper
    return decorator
