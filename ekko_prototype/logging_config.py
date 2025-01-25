"""
Centralized logging configuration for ekko application.

This module provides consistent logging setup across all modules with:
- Structured logging format
- Log rotation
- Different log levels for different modules
- Optional JSON logging for production
"""

import json
import logging
import logging.handlers
import sys
from datetime import datetime
from pathlib import Path


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured logs.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with additional context."""
        # Add timestamp in ISO format
        record.iso_time = datetime.fromtimestamp(record.created).isoformat()

        # Add relative path for filename
        if record.pathname:
            try:
                record.rel_path = Path(record.pathname).relative_to(Path.cwd())
            except ValueError:
                record.rel_path = Path(record.pathname).name
        else:
            record.rel_path = record.filename

        return super().format(record)


class JSONFormatter(logging.Formatter):
    """
    Formatter that outputs logs as JSON for production environments.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_obj = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "lineno",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "pathname",
                "processName",
                "process",
                "threadName",
                "thread",
                "getMessage",
                "levelno",
                "msecs",
                "relativeCreated",
            ]:
                log_obj[key] = value

        return json.dumps(log_obj)


def setup_logging(
    log_level: str = "INFO",
    log_file: str | None = None,
    log_dir: str = "./logs",
    use_json: bool = False,
    module_levels: dict[str, str] | None = None,
) -> None:
    """
    Configure logging for the entire application.

    :param log_level: Default log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    :type log_level: str
    :param log_file: Optional log file name (will be created in log_dir)
    :type log_file: Optional[str]
    :param log_dir: Directory for log files
    :type log_dir: str
    :param use_json: Whether to use JSON formatting (for production)
    :type use_json: bool
    :param module_levels: Optional dict of module-specific log levels
    :type module_levels: Optional[Dict[str, str]]
    """
    # Create logs directory if needed
    if log_file:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))

    # Choose formatter based on environment
    if use_json:
        formatter = JSONFormatter()
    else:
        formatter = StructuredFormatter(
            fmt="%(iso_time)s | %(levelname)-8s | %(name)-20s | %(rel_path)s:%(lineno)d | %(funcName)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler with rotation
    if log_file:
        file_path = Path(log_dir) / log_file
        file_handler = logging.handlers.RotatingFileHandler(
            file_path,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Configure module-specific levels
    if module_levels:
        for module_name, level in module_levels.items():
            module_logger = logging.getLogger(module_name)
            module_logger.setLevel(getattr(logging, level.upper()))

    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("transformers").setLevel(logging.WARNING)
    logging.getLogger("torch").setLevel(logging.WARNING)
    logging.getLogger("watchdog").setLevel(logging.WARNING)
    logging.getLogger("watchdog.observers.inotify_buffer").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.INFO)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("langchain").setLevel(logging.INFO)

    # Log initial setup
    logger = logging.getLogger(__name__)
    logger.info(
        f"Logging configured - Level: {log_level}, JSON: {use_json}, File: {log_file}"
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.

    :param name: Logger name (usually __name__)
    :type name: str
    :return: Configured logger instance
    :rtype: logging.Logger
    """
    return logging.getLogger(name)


# Convenience function for Streamlit apps
def setup_streamlit_logging():
    """
    Setup logging optimized for Streamlit applications.

    Reduces verbosity and focuses on application-specific logs.
    """
    setup_logging(
        log_level="INFO",
        log_file="ekko.log",
        module_levels={
            "ekko_prototype": "DEBUG",
            "ekko_prototype.pages.tools": "INFO",
            "ekko_prototype.auth": "INFO",
        },
    )


# Example usage for different environments
def setup_development_logging():
    """Setup logging for development environment."""
    setup_logging(
        log_level="DEBUG",
        log_file="ekko_dev.log",
        use_json=False,
        module_levels={
            "ekko_prototype": "DEBUG",
        },
    )


def setup_production_logging():
    """Setup logging for production environment."""
    setup_logging(
        log_level="INFO",
        log_file="ekko_prod.log",
        use_json=True,
        module_levels={
            "ekko_prototype": "INFO",
            "ekko_prototype.auth": "WARNING",
        },
    )
