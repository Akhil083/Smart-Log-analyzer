from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import Query
from app.schemas.log import LogFilterParams





def get_log_filter(
        level: Annotated[str | None, Query(max_length= 20)] = None,
        service: Annotated[str | None, Query( max_length= 100)] = None,
        environment: Annotated[str | None, Query( max_length= 50)] = None,
        trace_id: Annotated[str | None, Query( max_length= 128)] = None,
        request_id: Annotated[str | None, Query( max_length= 128)] = None,
        host: Annotated[str | None, Query( max_length= 255)] = None,
        keyword: Annotated[str | None, Query()] = None,
        start_time: datetime | None = None,
        end_time : datetime | None = None,
        page: Annotated[int, Query( ge=1)] = 1,
        limit: Annotated[int, Query( ge=1, le= 100)] = 20,
        sort_order: Annotated[str, Query( pattern="^(asc|desc)$")] = "desc",
) -> LogFilterParams :
     """
     Build log filter parameters from query string input.
     This keeps the router handler clean while still producing a strongly typed schema
     object for this service layer.
     """
     return LogFilterParams(
            level= level,
            service = service,
            environment = environment,
            trace_id= trace_id,
            request_id= request_id,
            host = host,
            keyword = keyword,
            start_time= start_time,
            end_time= end_time,
            page = page,
            limit = limit,
            sort_order= sort_order,
    )