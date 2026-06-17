from __future__ import annotations

from dataclasses import dataclass

from sklearn.cluster import MiniBatchKMeans
from sklearn.feature_extraction.text import TfidfVectorizer


@dataclass(slots=True)
class ClusteredLog:
    """Represent a log message assigned to a cluster"""

    message: str
    cluster_id: int


class ClusteringService:
    def __init__(
        self,
        n_clusters: int = 5,
        max_feature: int = 2000,
        random_state: int = 42,
    ):
        self.n_clusters = n_clusters
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
            max_features=max_feature,
        )
        self.model = MiniBatchKMeans(
            n_clusters=n_clusters,
            random_state=random_state,
            n_init="auto",
        )

    def cluster_messages(self, messages: list[str]):
        """Cluster input log messages and assign a cluster ID to each message"""

        cleaned_message = [message.strip() for message in messages if message.strip()]

        if not cleaned_message:
            return []

        if len(cleaned_message) < self.n_clusters:
            # Avoid invalid clustering configuration when the message count
            # is smaller than the requested number of cluster

            adjusted_cluster_count = max(1, len(cleaned_message))
            self.model = MiniBatchKMeans(
                n_clusters=adjusted_cluster_count,
                random_state=42,
                n_init="auto",
            )

        features = self.vectorizer.fit_transform(cleaned_message)
        cluster_id = self.model.fit_predict(features)

        return [
            ClusteredLog(message=message, cluster_id=int(cluster_id))
            for message, cluster_id in zip(cleaned_message, cluster_id, strict=True)
        ]

    def get_cluster_summary(self, messages: list[str]):
        """
        Return a summary view of cluster
        Example:
        [
        {
        cluster_id = 0,
        size = 15,
        sample_message = Database cnnection timeout
        }
        ]
        """

        clustered_logs = self.cluster_messages(messages)

        if not clustered_logs:
            return []

        grouped: dict[int, list[str]] = {}
        for item in clustered_logs:
            grouped.setdefault(item.cluster_id, []).append(item.message)

        summaries: list[dict] = []
        for cluster_id, cluster_messages in grouped.items():
            sample = cluster_messages[0]
            summaries.append(
                {
                    "cluster_id": cluster_id,
                    "size": len(cluster_messages),
                    "label": sample[:50],
                    "sample_message": sample,
                }
            )

        summaries.sort(key=lambda item: item["size"], reverse=True)
        return summaries
