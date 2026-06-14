from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.semanti_search_service import SemanticSearchService
from app.db.models.log import Log
from app.schemas.log import LogFilterParams
# from app.services.query_filter import apply_log_filters

@dataclass(slots=True)
class SemanticLogMatch:
    """Represent a log record matched through semantic similarity"""

    log : Log
    score: float


class SemanticLogSearchService:
    """Backend service that connect database log record with AI based semantic search"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.semantic_search_service = SemanticSearchService()


    @staticmethod
    def _validate_limits(candidate_limit:int , top_k : int):
        if candidate_limit < 1:
            raise ValueError("Candidate limit must be at least 1")
        
        if top_k < 1:
            raise ValueError("top k must be at least 1")
        


    def _rank_candidate_logs(self, query_text:str ,candidate_logs: list[Log], top_k: int):
        """Rank candidate ORM log objects by semantic similarity to the query text"""

        if not  candidate_logs:
            return []
        
        candidate_message = [log.message for log in candidate_logs]

        ranked_results = self.semantic_search_service.rank_texts(
            query = query_text,
            texts= candidate_message,
            top_k=top_k,
        )

        matches: list[SemanticLogMatch] = []
        for rank in ranked_results:
            matches.append(
                SemanticLogMatch(
                    log = candidate_logs[rank.index],
                    score = rank.score
                )
            )


        return matches



    async def search(self, query:str ,candidate_limit: int = 200, top_k: int = 10, filters: LogFilterParams | None = None):
        from app.services.query_filter import apply_log_filters

        self._validate_limits(candidate_limit,top_k)
        effective_filters = filters or LogFilterParams()

        query_stmt = select(Log).where(Log.message.is_not(None))
        query_stmt = apply_log_filters(query_stmt,effective_filters)
        query_stmt = query_stmt.order_by(Log.emitted_at.desc()).limit(candidate_limit)


        result = await self.session.execute(query_stmt)
        candidate_logs = result.scalars().all()

        return self._rank_candidate_logs(
            query_text=query,
            candidate_logs=candidate_logs,
            top_k=top_k
        )
    

    async def find_similar_to_log(self, source_log: Log, candidate_limit: int = 200,top_k: int = 10, same_service_only: bool = False):
        """Find logs semanticallly similar to an existing log record"""

        self._validate_limits(candidate_limit,top_k)

        source_message = source_log.message.strip()
        if not source_message:
            raise ValueError("Source log message cannot be empty")
        
        stmt = (
            select(Log)
            .where(Log.id != source_log.id)
            .order_by(Log.emitted_at.desc())
            .limit(candidate_limit)
        )

        if same_service_only and source_log.service:
            stmt = stmt.where(Log.service == source_log.service)

        result = await self.session.execute(stmt)
        candidate_logs = result.scalars().all()


        return self._rank_candidate_logs(
            query_text=source_message,
            candidate_logs=candidate_logs,
            top_k=top_k,
        )