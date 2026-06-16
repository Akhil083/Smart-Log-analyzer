from __future__ import annotations

import json
from typing import Iterable

from app.schemas.log import LogCreate


class FileParse:
    """
    Utility for parsing uploaded log file into logcreate object
    """

    @staticmethod
    def parse_json(content: str) -> list[dict]:
        data = json.loads(content)

        if not isinstance(data, list):
            raise ValueError("Expected JSON array")

        return data
    

    @staticmethod
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

        if content.startswith("["):
            return cls.parse_json(content)
        
        return cls.parse_json_line(content)

