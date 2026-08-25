"""Helper functions for API operations."""
import time
import logging
from requests.exceptions import HTTPError

logger = logging.getLogger(__name__)


def sync_mcp_tools_with_retry(toolkit_api, url, max_retries=3, initial_delay=5, timeout=60):
    """
    Sync MCP tools with automatic retry on pool saturation (503).

    When the backend's worker pool is saturated, it returns 503 with
    'temporarily_unavailable' error and a retry_after hint. This function
    implements exponential backoff retry for such transient errors.

    Args:
        toolkit_api: ToolkitAPI instance with sync_mcp_tools method
        url: MCP endpoint URL (e.g. "https://mcp.deepwiki.com/mcp")
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds (default: 5)
        timeout: Request timeout in seconds (default: 60)

    Returns:
        list: Tools from MCP endpoint

    Raises:
        HTTPError: If all retries exhausted or non-retriable error

    Example:
        >>> tools = sync_mcp_tools_with_retry(
        ...     toolkit_api,
        ...     "https://mcp.deepwiki.com/mcp",
        ...     max_retries=3,
        ...     initial_delay=5
        ... )
    """
    delay = initial_delay

    for attempt in range(max_retries + 1):
        try:
            logger.info(
                f"MCP sync attempt {attempt + 1}/{max_retries + 1}: url={url}, timeout={timeout}s"
            )
            tools = toolkit_api.sync_mcp_tools(url, timeout=timeout)

            if attempt > 0:
                logger.info(
                    f"MCP sync succeeded on attempt {attempt + 1} after {sum([initial_delay * (2**i) for i in range(attempt)])}s total delay"
                )

            return tools

        except HTTPError as e:
            # Check if it's a 503 pool saturation error
            if e.response.status_code == 503:
                try:
                    error_body = e.response.json() if e.response.text else {}
                except Exception:
                    error_body = {}

                error_type = error_body.get('error')

                if error_type == 'temporarily_unavailable':
                    # Pool saturated - retry is worthwhile
                    if attempt < max_retries:
                        retry_after = error_body.get('retry_after', delay)
                        logger.warning(
                            f"Pool saturated (attempt {attempt + 1}/{max_retries + 1}). "
                            f"Backend suggests retry_after={retry_after}s. "
                            f"Waiting {retry_after}s before retry..."
                        )
                        time.sleep(retry_after)
                        # Exponential backoff for next attempt, max 30s
                        delay = min(delay * 2, 30)
                        continue
                    else:
                        # All retries exhausted
                        logger.error(
                            f"Pool saturated after {max_retries + 1} attempts "
                            f"(total delay: ~{sum([initial_delay * (2**i) for i in range(max_retries)])}s). "
                            f"Giving up."
                        )
                        raise
                else:
                    # 503 but not pool saturation (different error) - don't retry
                    logger.error(f"503 error but not pool saturation (error={error_type}). Not retrying.")
                    raise
            else:
                # Non-503 error (400, 401, 404, network timeout, etc.) - don't retry
                logger.error(
                    f"Non-retriable error (HTTP {e.response.status_code}). Not retrying."
                )
                raise

        except Exception as e:
            # Non-HTTP error (network issues, etc.) - don't retry
            logger.error(f"Non-HTTP exception: {type(e).__name__}: {e}. Not retrying.")
            raise

    # Should never reach here, but just in case
    raise RuntimeError("Unexpected retry loop exit")
