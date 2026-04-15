from __future__ import annotations

import json
import logging
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
	def format(self, record: logging.LogRecord) -> str:
		payload: dict[str, object] = {
			"timestamp": datetime.now(timezone.utc).isoformat(),
			"level": record.levelname,
			"logger": record.name,
			"message": record.getMessage(),
		}

		extra_data = getattr(record, "extra_data", None)
		if isinstance(extra_data, dict):
			payload.update(extra_data)

		if record.exc_info:
			payload["exception"] = self.formatException(record.exc_info)

		return json.dumps(payload, default=str)


def configure_logging(level: int = logging.INFO) -> None:
	root_logger = logging.getLogger()
	root_logger.setLevel(level)

	if root_logger.handlers:
		root_logger.handlers.clear()

	handler = logging.StreamHandler()
	handler.setFormatter(JsonFormatter())
	root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
	return logging.getLogger(name)
