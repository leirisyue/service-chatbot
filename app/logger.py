import logging
import os
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None  # Python < 3.9 fallback

LOG_DIR = os.getenv("LOG_DIR", "/app/logs")
os.makedirs(LOG_DIR, exist_ok=True)

class TZFormatter(logging.Formatter):
    """
    Formatter dùng timezone cố định (mặc định Asia/Ho_Chi_Minh) cho thời gian log.
    Cho phép override qua biến môi trường TZ.
    """

    def __init__(self, fmt=None, datefmt=None):
        super().__init__(fmt=fmt, datefmt=datefmt)
        tz_name = os.getenv("TZ", "Asia/Ho_Chi_Minh")
        self.tz = ZoneInfo(tz_name) if ZoneInfo else None

    def formatTime(self, record, datefmt=None):
        if self.tz:
            dt = datetime.fromtimestamp(record.created, tz=self.tz)
        else:
            # Fallback nếu không có zoneinfo: dùng localtime của hệ thống
            dt = datetime.fromtimestamp(record.created)
        return dt.strftime(datefmt or "%Y-%m-%d %H:%M:%S")


def setup_logger(name: str) -> logging.Logger:
    """
    Tạo logger:
    - Ghi ra console (stdout)
    - Ghi ra file log, xoay file theo ngày (mỗi ngày 1 file)
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Tránh add handler trùng lặp nếu setup nhiều lần
    if logger.handlers:
        return logger

    # Format chung
    formatter = TZFormatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Handler console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Handler file, xoay hàng ngày, giữ 7 file gần nhất (tùy chỉnh)
    # Tên base file; handler sẽ tự thêm suffix theo ngày
    log_file = os.path.join(LOG_DIR, "app.log")
    file_handler = TimedRotatingFileHandler(
        log_file,
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8",
    )
    # File sẽ xoay theo ngày với hậu tố YYYY-MM-DD, ví dụ: app.log.2025-12-12
    file_handler.suffix = "%Y-%m-%d"
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger