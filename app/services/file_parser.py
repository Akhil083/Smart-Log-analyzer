from __future__ import annotations

import json
from typing import Iterable

from app.schemas.log import LogCreate


class FileParse:
    """
    Utility for parsing uploaded log file into logcreate object
    """

    @staticmethod
    def parse_json(content: str) -> list:
        """Parse a json array of logs"""

        data = json.loads(content)

        if not isinstance(data, list):
            raise ValueError("Expected JSON array of log object")
        
        return [LogCreate.model_validate(item) for item in data]
    

    @staticmethod
    def parse_json_line(content: str):
        """Parse newline-seperated json obejct (jsonl format)"""

        logs : list[LogCreate] = []

        lines = content.splitlines()

        for line in lines:
            line = line.split()
            if not line:
                continue

            try:
                data = json.loads(line)
                logs.append(LogCreate.model_validate(data))
            except Exception as e:
                raise ValueError(f"Invalid json line: {line}") from e
            
        return logs
    

    @classmethod
    def parse(cls, content: str):
        """Auto dectect format and parse logs"""

        content = content.strip()

        if content.startswith("["):
            return cls.parse_json(content)
        
        return cls.parse_json_line(content)

