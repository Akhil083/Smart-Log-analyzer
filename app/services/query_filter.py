from __future__ import annotations

from sqlalchemy import Select

from app.db.models.log import Log
from app.schemas.log import LogFilterParams


def apply_log_filters(query: Select, filters: LogFilterParams) -> Select:
    """Apply resuable log filters to a SQLAlchemy query"""

    if filters.level:
            query = query.where(Log.level == filters.level.upper())

    if filters.service:
            query = query.where(Log.service == filters.service.strip())

    if filters.environment:
            query = query.where(Log.environment == filters.environment.strip().lower())

    if filters.trace_id:
            query = query.where(Log.trace_id == filters.trace_id.strip())

    if filters.request_id:
            query = query.where(Log.request_id == filters.request_id.strip())

    if filters.host:
            query = query.where(Log.host == filters.host.strip())

    if filters.start_time:
            query = query.where(Log.start_time >= filters.start_time)

    if filters.end_time:
            query = query.where(Log.end_time <= filters.end_time)

    if filters.keyword:
        keyword = filters.keyword.strip()
        if keyword:
                query = query.where(Log.message.ilike(f"%{keyword}%"))

    return query