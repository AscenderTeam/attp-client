import asyncio
from typing import Any, Callable, Mapping


def trigger_callable(
    callable: Callable[..., Any], 
    args: tuple[Any] | None = None, 
    kwargs: Mapping[str, Any] | None = None
):
    asyncio.create_task(callable(*(args or tuple()), **(kwargs or {})))