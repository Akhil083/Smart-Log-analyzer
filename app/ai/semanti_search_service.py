from __future__ import annotations

from dataclasses import dataclass

import numpy as np 

from app.ai.embedding_service import EmbeddingService


@dataclass(slots=True)
class SemanticSearchResult:
    """Represent one ranked semantic search match"""

    index : int
    text : str 
    score: float



class SemanticSearchService:
    """Perform semantic similarity ranking over log message"""

    def __init__(self):
        self.embedding_service = EmbeddingService()

    def rank_texts(self, query: str, texts: list[str] , top_k : int = 10):
        
        cleaned_query = query.strip()
        if not cleaned_query:
            raise ValueError("Semantic search query cannot be empty")
        
        cleaned_texts_with_index = [
            (index,text.strip())
            for index, text in enumerate(texts)
            if text and text.strip()
        ]

        if not cleaned_texts_with_index: 
            return []
        
        original_indexes = [item[0] for item in cleaned_texts_with_index]
        cleaned_texts = [item[1] for item in cleaned_texts_with_index]

        query_embedding = np.array(
            self.embedding_service.embed_texts(cleaned_query),
            dtype=np.float32, 
        )

        text_embedding = np.array(
            self.embedding_service.embed_texts(cleaned_texts),
            dtype=np.float32, 
        )


        similarity_scores = text_embedding @ query_embedding

        ranked_indexes = np.argsort(similarity_scores)[::-1]

        limited_ranked_indexes = ranked_indexes[:top_k]

        results: list[SemanticSearchResult] =[]

        for ranked_position in limited_ranked_indexes:
            results.append(
                SemanticSearchResult(
                    index=original_indexes[int(ranked_position)],
                    text = cleaned_texts[int(ranked_position)],
                    score = float(similarity_scores[int(ranked_position)]),
                )
            ) 

        return results

