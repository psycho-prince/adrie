"""Request ID context — extracted from middleware/request_id.py to break circular import."""
from contextvars import ContextVar
request_id_ctx: ContextVar = ContextVar("request_id", default=None)
