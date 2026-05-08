import logging
import json
import sys
from datetime import datetime


class JsonFormatter(logging.Formatter):

    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
        }

        if hasattr(record, "method"):
            log_record["method"] = record.method

        if hasattr(record, "path"):
            log_record["path"] = record.path

        if hasattr(record, "status"):
            log_record["status"] = record.status

        if hasattr(record, "client_ip"):
            log_record["client_ip"] = record.client_ip

        return json.dumps(log_record)


logger = logging.getLogger("app")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())

logger.addHandler(handler)
