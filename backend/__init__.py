__all__ = ["app", "create_app"]


def __getattr__(name: str):
    if name in {"app", "create_app"}:
        from backend.app import app, create_app

        return {"app": app, "create_app": create_app}[name]
    raise AttributeError(f"module 'backend' has no attribute {name!r}")
