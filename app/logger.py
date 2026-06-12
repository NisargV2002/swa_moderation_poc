"""
app/logger.py

Purpose:
- Creates local runtime logs.
- These are developer/debugging logs.
- Business/audit logs are separately written to DB using db.py.

Output files:
- logs/moderation_YYYY-MM-DD.log
- logs/errors.log

Why this matters:
- File logs help debug Python/API failures.
- DB logs help explain moderation execution to stakeholders.
"""


import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime

from config.settings import settings


def get_logger():
    log_dir = Path(settings.LOG_DIR)
    log_dir.mkdir(exist_ok=True)

    logger = logging.getLogger("swa_moderation_logger")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    today = datetime.now().strftime("%Y-%m-%d")

    main_handler = RotatingFileHandler(
        log_dir / f"moderation_{today}.log",
        maxBytes=2_000_000,
        backupCount=5,
        encoding="utf-8"
    )

    error_handler = RotatingFileHandler(
        log_dir / "errors.log",
        maxBytes=2_000_000,
        backupCount=5,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    main_handler.setFormatter(formatter)
    error_handler.setFormatter(formatter)

    logger.addHandler(main_handler)
    logger.addHandler(error_handler)

    return logger