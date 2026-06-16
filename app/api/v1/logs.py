from __future__ import annotations

from fastapi import APIRouter, Depends, status, Query,HTTPException, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select , func

from datetime import datetime
from typing import Annotated
import time

from app.db.session import get_db_session
from app.schemas.log import LogBulkCreate, LogRead, LogCreate, LogFilterParams, LogListResponse
from app.schemas.analytics import *
from app.services.ingestion_service import IngestionService
from app.services.search_service import SearchService
from app.services.semantic_log_search_service import SemanticLogSearchService
from app.services.file_parser import FileParse
from app.api.dependencies import get_log_filter
from app.db.models.log import Log

router = APIRouter(prefix="/logs" , tags=["Logs"])


#Single log ingestion
@router.post("",response_model = LogRead,status_code = status.HTTP_201_CREATED,summary= "Ingest a single log entry")
async def create_log(payload : LogCreate,session: AsyncSession = Depends(get_db_session),) -> LogRead:
    """
    Ingest a single log entry
    """

    service = IngestionService(session)
    log = await service.create_log(payload)

    return LogRead.model_validate(log)


#bulk log ingestion
@router.post("/bulk",response_model = list[LogRead], status_code = status.HTTP_201_CREATED, summary ="Ingest multiple log enteries" )
async def create_log_bulk(payload : LogBulkCreate, session: AsyncSession=Depends(get_db_session)) ->list[LogRead]:
    service = IngestionService(session)
    logs = await service.create_log_bulk(payload)

    return [LogRead.model_validate(log) for log in logs]






def to_log_read(log) ->LogRead:
    """
    Convert a Log ORM insatance into a LogRead response schema.
    """
    return LogRead.model_validate(
        {
            "id" : log.id,
            "emitted_at" :log.emitted_at,
            "ingested_at": log.ingested_at,
            "level":log.level,
            "service": log.service,
            "environment": log.environment,
            "message": log.message,
            "source": log.source,
            "trace_id": log.trace_id,
            "request_id": log.request_id,
            "host": log.host,
            "metadata": log.log_metadata,
        }
    )




@router.get("",response_model = LogListResponse, summary="List and filter of Logs")
async def get_logs(
    filters:Annotated[LogFilterParams,Depends(get_log_filter)],
    session : AsyncSession = Depends(get_db_session),
) -> LogListResponse :
    """
    Retrive logs with filtering , pagination and sorting support.
    """

    service = SearchService(session)
    logs , total = await service.get_logs(filters)

    return LogListResponse(
        item = [to_log_read(log) for log in logs],
        total = total,
        page = filters.page,
        limit = filters.limit 
    )





def to_similar_log_result(match) -> SimilarLogResponse:
    """Convert a semantic log match into an API friendly response dictionary"""

    return SimilarLogResponse(
        score = round(match.score, 6),
        log =  {
            "id" : match.log.id,
            "emitted_at" :match.log.emitted_at,
            "ingested_at": match.log.ingested_at,
            "level":match.log.level,
            "service": match.log.service,
            "environment": match.log.environment,
            "message": match.log.message,
            "source": match.log.source,
            "trace_id": match.log.trace_id,
            "request_id": match.log.request_id,
            "host": match.log.host,
            "metadata": match.log.log_metadata,
        },
    )


@router.get("/service-count")
async def get_service_count(
    session: AsyncSession = Depends(get_db_session)
):
    result = await session.execute(
        select(func.count(func.distinct(Log.service)))
    )

    return {
        "service_count": result.scalar_one()
    }

@router.get("/{log_id}", response_model = LogRead, summary= "Get a single log by ID") 
async def get_log_by_id(log_id: int , session: AsyncSession=Depends(get_db_session)) -> LogRead:

    service = SearchService(session)

    log = await service.get_log_by_id(log_id)

    if log is None:
        raise HTTPException (
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Log with id={log_id} was not found"
        )
    
    return to_log_read(log)




@router.get("/{log_id}/similar",response_model=SimilarLogsResponses, summary="find logs similar to existing log")
async def get_similar_log(
    log_id: int,
    candidate_limit: Annotated[int,Query(ge=1,le=1000)] = 200,
    top_k:Annotated[int, Query(ge=1, le=50)] = 10,
    session: AsyncSession = Depends(get_db_session),
    same_service_only: bool = False,
) -> SimilarLogsResponses :
    
    search_service = SearchService(session)
    source_log = await search_service.get_log_by_id(log_id)


    if source_log is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"log with id {log_id} was not found"
        )
    
    semantic_service = SemanticLogSearchService(session)
    matches = await semantic_service.find_similar_to_log(
        source_log=source_log,
        candidate_limit=candidate_limit,
        top_k=top_k,
        same_service_only=same_service_only,
    ) 


    return SimilarLogsResponses(results = [to_similar_log_result(match) for match in matches])
     




#Upload file
@router.post("/upload", summary="Upload and ingest log files")
async def upload_logs(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db_session),
) -> dict:

    start = time.perf_counter()

    content = await file.read()
    text = content.decode("utf-8", errors="replace")

    try:
        raw_logs = FileParse.parse(text)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to parse file: {str(e)}",
        )

    valid_logs: list[LogCreate] = []
    failed_count = 0

    for item in raw_logs:
        try:
            valid_logs.append(
                LogCreate.model_validate(item)
            )
        except Exception:
            failed_count += 1

    service = IngestionService(session)

    created_logs = (
        await service.create_logs_from_items(valid_logs)
        if valid_logs
        else []
    )

    elapsed_ms = round(
        (time.perf_counter() - start) * 1000,
        2,
    )

    return {
        "message": "Logs uploaded successfully",
        "ingested_count": len(created_logs),
        "failed_count": failed_count,
        "processing_time_ms": elapsed_ms,
    }



