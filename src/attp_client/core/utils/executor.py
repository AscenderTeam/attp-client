import inspect
from typing import Any, Mapping, get_args, get_origin

from pydantic import BaseModel, TypeAdapter

from attp_client.misc.fixed_basemodel import FixedBaseModel
from attp_core.rs_api import PyAttpMessage


async def execute_validated(callback: Any, payload: Any, *, frame: PyAttpMessage | None = None):
    """Thx GPT-5 for the call validator!"""
    sig = inspect.signature(callback)
    params = list(sig.parameters.values())

    # If it's a bound method, drop the first "self"
    if inspect.ismethod(callback) and callback.__self__ is not None:
        params = params[1:]
        sig = sig.replace(parameters=params)

    def wants_frame(param: inspect.Parameter) -> bool:
        if frame is None:
            return False

        ann = param.annotation
        if ann is PyAttpMessage:
            return True

        origin = get_origin(ann)
        if origin is not None and PyAttpMessage in get_args(ann):
            return True

        return ann is inspect._empty and param.name in ("message", "frame")

    # --- Case 1: single-param message frame ---
    if len(params) == 1:
        param = params[0]
        if wants_frame(param):
            if inspect.iscoroutinefunction(callback):
                return await callback(frame)
            return callback(frame)

        # --- Case 2: single-param model ---
        ann = param.annotation

        if ann is not inspect._empty and (issubclass_safe(ann, FixedBaseModel) or issubclass_safe(ann, BaseModel)):
            model = ann.model_validate(payload) if hasattr(ann, "model_validate") else ann(**payload)
            if inspect.iscoroutinefunction(callback):
                return await callback(model)
            return callback(model)

    # --- Case 3: normal kwargs mapping ---
    bound_args = {}
    for name, param in sig.parameters.items():
        if name not in payload and wants_frame(param):
            bound_args[name] = frame
            continue

        if name not in payload and param.default is inspect.Parameter.empty:
            raise TypeError(f"Missing required argument: {name}")

        value = payload.get(name, param.default)

        if param.annotation is not inspect._empty:
            adapter = TypeAdapter(param.annotation)
            value = adapter.validate_python(value)

        bound_args[name] = value

    if inspect.iscoroutinefunction(callback):
        return await callback(**bound_args)
    return callback(**bound_args)


def issubclass_safe(obj: Any, cls: type) -> bool:
    try:
        return inspect.isclass(obj) and issubclass(obj, cls)
    except Exception:
        return False
