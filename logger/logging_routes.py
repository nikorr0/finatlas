from flask import Blueprint, Response, stream_with_context
import time

from .log_config import log_buffer, log_buffer_lock

bp = Blueprint("logging_routes", __name__)

@bp.route("/stream-logs")
def stream_logs():
    def event_stream():
        last_sent = 0
        while True:
            with log_buffer_lock:
                # new_lines = log_buffer[last_sent:]
                if last_sent > len(log_buffer):
                    last_sent = len(log_buffer)
                new_lines = log_buffer[last_sent:]
            for line in new_lines:
                # Каждое событие — две реальных перевода строки
                yield f"data: {line}\n\n"
            last_sent += len(new_lines)
            time.sleep(1)

    return Response(
        stream_with_context(event_stream()),
        # event_stream(),
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )
