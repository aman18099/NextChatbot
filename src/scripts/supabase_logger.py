import logging
from datetime import datetime
import uuid
from src.scripts.supabase_config import create_supabase_client

class SupabaseLogger(logging.Handler):
    def __init__(self):
        super().__init__()
        self.supabase = create_supabase_client()

    def emit(self, record: logging.LogRecord) -> None:
        try:
            log_data = {
                "id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "message": record.getMessage(),
                "module": record.name,
                "user_id": getattr(record, "user_id", None),
            }
            self.supabase.table("logs").insert(log_data).execute()
        except Exception as e:
            print(f"Failed to log to Supabase: {e}")
