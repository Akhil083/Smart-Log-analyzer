from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_log_filter
from app.db.session import get_db_session
from app.schemas.analytics import (
    ClusterResponse,
    CountMapResponse,
    LogBaseResponse,
    SemanticSearchResponse,
    SemanticSearchResult,
    SummaryResponse,
    TimelineAnomalyPoint,
    TimelineAnomalyResponse,
    TimelinePoint,
    TimelineResponse,
    TopErrorServicesResponse,
)
from app.schemas.log import LogFilterParams
from app.services.analytics_service import AnalyticsServices
from app.services.semantic_log_search_service import SemanticLogSearchService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


# Summary
@router.get(
    "/summary", response_model=SummaryResponse, summary="Get overall log summary"
)
async def get_summary(
    filters: Annotated[LogFilterParams, Depends(get_log_filter)],
    session: AsyncSession = Depends(get_db_session),
) -> SummaryResponse:

    service = AnalyticsServices(session)
    result = await service.get_summary(filters=filters)
    return SummaryResponse(**result)


@router.get(
    "/warning-count",
    summary="Get warning log count",
)
async def get_warning_count(
    filters: Annotated[
        LogFilterParams,
        Depends(get_log_filter),
    ],
    session: AsyncSession = Depends(get_db_session),
):

    service = AnalyticsServices(session)

    count = await service.get_warning_count(filters=filters)

    return {"warning_logs": count}


@router.get(
    "/critical-count",
    summary="Get critical log count",
)
async def get_critical_count(
    filters: Annotated[
        LogFilterParams,
        Depends(get_log_filter),
    ],
    session: AsyncSession = Depends(get_db_session),
):

    service = AnalyticsServices(session)

    count = await service.get_critical_count(filters=filters)

    return {"critical_logs": count}


# Level
@router.get("/level", response_model=CountMapResponse, summary="Get log count by level")
async def get_log_by_level(
    filters: Annotated[LogFilterParams, Depends(get_log_filter)],
    session: AsyncSession = Depends(get_db_session),
) -> CountMapResponse:

    service = AnalyticsServices(session)
    result = await service.get_logs_by_level(filters=filters)
    return CountMapResponse.model_validate(result)


# Services
@router.get(
    "/service", response_model=CountMapResponse, summary="Get log count by services"
)
async def get_log_by_service(
    filters: Annotated[LogFilterParams, Depends(get_log_filter)],
    session: AsyncSession = Depends(get_db_session),
) -> CountMapResponse:

    service = AnalyticsServices(session)
    result = await service.get_logs_by_service(filters=filters)
    return CountMapResponse.model_validate(result)


# timeline
@router.get("/timeline", response_model=TimelineResponse, summary="Get log timeline")
async def get_timeline(
    filters: Annotated[LogFilterParams, Depends(get_log_filter)],
    interval: str = "minute",
    session: AsyncSession = Depends(get_db_session),
) -> TimelineResponse:

    service = AnalyticsServices(session)
    result = await service.get_timeline(interval, filters=filters)
    return TimelineResponse(item=[TimelinePoint(**item) for item in result])


# Anomaly detection
@router.get(
    "/timeline/anomalies",
    response_model=TimelineAnomalyResponse,
    summary="Timeline with anomaly detection",
)
async def get_timeline_anomalies(
    filters: Annotated[LogFilterParams, Depends(get_log_filter)],
    interval: str = "minute",
    session: AsyncSession = Depends(get_db_session),
) -> TimelineAnomalyResponse:

    service = AnalyticsServices(session)

    result = await service.get_timeline_with_anomalies(
        interval=interval,
        filters=filters,
    )

    return TimelineAnomalyResponse(
        item=[TimelineAnomalyPoint(**item) for item in result]
    )


# Clustering
@router.get(
    "/clusters", response_model=ClusterResponse, summary="Cluster recent log messages"
)
async def get_clusters(
    filters: Annotated[LogFilterParams, Depends(get_log_filter)],
    limit: Annotated[
        int,
        Query(
            ge=1,
        ),
    ] = 200,
    n_clusters: Annotated[int, Query(ge=1, le=20)] = 5,
    session: AsyncSession = Depends(get_db_session),
) -> ClusterResponse:

    service = AnalyticsServices(session)
    result = await service.get_cluster(
        limit=limit,
        n_clusters=n_clusters,
        filters=filters,
    )
    return ClusterResponse(clusters=result)


# Semantic Search


def to_semantic_result(match) -> SemanticSearchResult:
    """Convert a semantic log match into an API friendly response dictionary"""

    raw_metadata = {}
    if match.log.log_metadata:
        if hasattr(match.log.log_metadata, "__dict__"):
            # Filter out internal SQLAlchemy keys (like _sa_instance_state)
            raw_metadata = {
                k: v
                for k, v in match.log.log_metadata.__dict__.items()
                if not k.startswith("_")
            }
        else:
            try:
                raw_metadata = dict(match.log.log_metadata)
            except (TypeError, ValueError):
                raw_metadata = {}

    return SemanticSearchResult(
        score=round(match.score, 6),
        log=LogBaseResponse(
            id=match.log.id,
            emitted_at=match.log.emitted_at,
            ingested_at=match.log.ingested_at,
            level=match.log.level,
            service=match.log.service,
            environment=match.log.environment,
            message=match.log.message,
            source=match.log.source,
            trace_id=match.log.trace_id,
            request_id=match.log.request_id,
            host=match.log.host,
            metadata=raw_metadata,
            ingestion_mode=match.log.ingestion_mode,
        ),
    )


@router.get(
    "/semantic_search",
    response_model=SemanticSearchResponse,
    summary="Search log by semantic search",
)
async def semantic_search(
    filters: Annotated[LogFilterParams, Depends(get_log_filter)],
    query: Annotated[str, Query(min_length=1)],
    candidate_limit: Annotated[int, Query(ge=1, le=1000)] = 200,
    top_k: Annotated[int, Query(ge=1, le=50)] = 10,
    session: AsyncSession = Depends(get_db_session),
) -> SemanticSearchResponse:

    service = SemanticLogSearchService(session)
    matches = await service.search(
        query=query,
        candidate_limit=candidate_limit,
        top_k=top_k,
        filters=filters,
    )

    return SemanticSearchResponse(
        results=[to_semantic_result(match) for match in matches]
    )


@router.get(
    "/top-error-services",
    response_model=TopErrorServicesResponse,
)
async def top_error_services(
    filters: Annotated[LogFilterParams, Depends(get_log_filter)],
    limit: Annotated[
        int,
        Query(ge=1, le=20),
    ] = 5,
    session: AsyncSession = Depends(get_db_session),
):

    service = AnalyticsServices(session)

    result = await service.get_top_error_services(limit=limit, filters=filters)

    return TopErrorServicesResponse(items=result)


@router.get(
    "/filter-options",
    summary="Get filter dropdown values",
)
async def get_filter_options(
    filters: Annotated[LogFilterParams, Depends(get_log_filter)],
    session: AsyncSession = Depends(get_db_session),
):
    service = AnalyticsServices(session)

    return await service.get_filter_options(
        filters=filters,
    )
