from __future__ import annotations

import json


class FileParse:
    """
    Utility for parsing uploaded log file into logcreate object
    """

    @staticmethod
    def parse_json(content: str) -> list[dict]:
        data = json.loads(content)

        if isinstance(data, dict):
            # Find all top-level keys that contain a list
            list_keys = [k for k, v in data.items() if isinstance(v, list)]

            if list_keys:
                # Dynamically extract the first list found (handles "logs", "data", "events", etc.)
                return data[list_keys[0]]

            # If no internal lists exist, treat the dictionary itself as a single log item
            return [data]

        if not isinstance(data, list):
            raise ValueError("Expected JSON array")

        return data

    @staticmethod
    def parse_json_line(content: str) -> list[dict]:
        logs = []

        for line in content.splitlines():
            line = line.strip()

            if not line:
                continue

            logs.append(json.loads(line))

        return logs

    @classmethod
    def parse(cls, content: str):
        """Auto dectect format and parse logs"""

        content = content.strip()

        if content.startswith("[") or content.startswith("{"):
            return cls.parse_json(content)

        return cls.parse_json_line(content)
