"""
Asyncio task utilities for safe task creation and exception handling.

This module provides utilities to properly handle exceptions in async tasks
that would otherwise be silently lost in fire-and-forget patterns.
"""
import asyncio
from typing import Coroutine, Optional, Callable, Any

from jam.log_setup import logger


def create_safe_task(
    coro: Coroutine,
    name: Optional[str] = None,
    on_error: Optional[Callable[[Exception], None]] = None
) -> asyncio.Task:
    """
    Create an asyncio task with automatic exception handling.
    
    Unlike plain asyncio.create_task(), this ensures exceptions are
    logged properly instead of producing "Task exception was never retrieved".
    
    Args:
        coro: The coroutine to run as a task
        name: Optional name for the task (shown in logs)
        on_error: Optional callback to invoke when an exception occurs
        
    Returns:
        The created asyncio.Task
        
    Example:
        # Instead of:
        asyncio.create_task(some_async_function())
        
        # Use:
        create_safe_task(some_async_function(), name="my_task")
    """
    try:
        task = asyncio.create_task(coro, name=name)
    except RuntimeError as e:
        # No running event loop - this shouldn't happen but log it
        logger.error(f"Failed to create task '{name}': {e}")
        # Close the coroutine to avoid warning
        coro.close()
        raise
    
    def handle_exception(t: asyncio.Task) -> None:
        try:
            # Only check for exception if task wasn't cancelled
            if not t.cancelled():
                exc = t.exception()
                if exc is not None:
                    task_name = t.get_name() or "unnamed_task"
                    logger.error(
                        f"Task '{task_name}' failed",
                        exc_info=(type(exc), exc, exc.__traceback__)
                    )
                    if on_error:
                        on_error(exc)
        except asyncio.CancelledError:
            # Task was cancelled, this is expected behavior
            pass
        except asyncio.InvalidStateError:
            # Task is still pending (shouldn't happen in done callback)
            pass
    
    task.add_done_callback(handle_exception)
    return task


async def safe_gather(*coros: Coroutine, return_exceptions: bool = False) -> list[Any]:
    """
    Wrapper around asyncio.gather that logs exceptions properly.
    
    Args:
        *coros: Coroutines to run concurrently
        return_exceptions: If True, exceptions are returned as results
                          If False, first exception is raised
                          
    Returns:
        List of results from the coroutines
    """
    results = await asyncio.gather(*coros, return_exceptions=True)
    
    processed_results = []
    for i, res in enumerate(results):
        if isinstance(res, Exception):
            logger.error(
                f"Task {i} in gather failed",
                exc_info=(type(res), res, res.__traceback__)
            )
            if not return_exceptions:
                raise res
        processed_results.append(res)
    
    return processed_results
