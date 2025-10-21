"""
Production-Grade Logging Configuration
Structured JSON logging with rotation for offline field debugging
"""

import os
import sys
import json
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter with additional context fields
    """

    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        """Add custom fields to log record"""
        super().add_fields(log_record, record, message_dict)

        # Add timestamp
        if not log_record.get('timestamp'):
            log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'

        # Add log level
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname

        # Add service identifier
        log_record['service'] = 'tactical-rag-backend'

        # Add environment
        log_record['environment'] = os.getenv('ENVIRONMENT', 'development')

        # Add process info
        log_record['process_id'] = record.process
        log_record['thread_id'] = record.thread

        # Add source location
        log_record['source'] = {
            'file': record.pathname,
            'line': record.lineno,
            'function': record.funcName
        }


class StructuredLogger:
    """
    Production-grade structured logger with rotation
    """

    def __init__(
        self,
        name: str = "tactical-rag",
        log_level: str = None,
        log_dir: str = None,
        log_format: str = None,
        enable_console: bool = True,
        enable_file: bool = True
    ):
        """
        Initialize structured logger

        Args:
            name: Logger name
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_dir: Directory for log files
            log_format: Format type ('json' or 'text')
            enable_console: Enable console logging
            enable_file: Enable file logging
        """
        self.name = name
        self.log_level = (log_level or os.getenv('LOG_LEVEL', 'INFO')).upper()
        self.log_dir = Path(log_dir or os.getenv('LOG_DIR', './logs'))
        self.log_format = log_format or os.getenv('LOG_FORMAT', 'json')
        self.enable_console = enable_console
        self.enable_file = enable_file

        # Create log directory
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Initialize logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, self.log_level))
        self.logger.handlers = []  # Clear existing handlers

        # Add handlers
        if self.enable_console:
            self._add_console_handler()

        if self.enable_file:
            self._add_file_handler()
            self._add_error_file_handler()

    def _add_console_handler(self) -> None:
        """Add console handler"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, self.log_level))

        if self.log_format == 'json':
            formatter = CustomJsonFormatter(
                '%(timestamp)s %(level)s %(name)s %(message)s'
            )
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def _add_file_handler(self) -> None:
        """Add rotating file handler for all logs"""
        log_file = self.log_dir / f"{self.name}.log"

        # Rotating file handler (100MB per file, keep 10 files)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=100 * 1024 * 1024,  # 100MB
            backupCount=10,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, self.log_level))

        if self.log_format == 'json':
            formatter = CustomJsonFormatter(
                '%(timestamp)s %(level)s %(name)s %(message)s'
            )
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def _add_error_file_handler(self) -> None:
        """Add separate rotating file handler for errors only"""
        error_log_file = self.log_dir / f"{self.name}-errors.log"

        # Rotating file handler for errors (50MB per file, keep 5 files)
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=50 * 1024 * 1024,  # 50MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)

        if self.log_format == 'json':
            formatter = CustomJsonFormatter(
                '%(timestamp)s %(level)s %(name)s %(message)s'
            )
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

        error_handler.setFormatter(formatter)
        self.logger.addHandler(error_handler)

    def get_logger(self) -> logging.Logger:
        """Get configured logger instance"""
        return self.logger


class PerformanceLogger:
    """
    Performance metrics logger for offline analysis
    """

    def __init__(self, log_dir: str = None):
        """
        Initialize performance logger

        Args:
            log_dir: Directory for performance logs
        """
        self.log_dir = Path(log_dir or os.getenv('LOG_DIR', './logs'))
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.metrics_file = self.log_dir / "performance-metrics.jsonl"

    def log_query_performance(
        self,
        query: str,
        response_time: float,
        retrieval_time: float,
        generation_time: float,
        cache_hit: bool,
        num_sources: int,
        mode: str,
        metadata: Dict[str, Any] = None
    ) -> None:
        """
        Log query performance metrics

        Args:
            query: User query
            response_time: Total response time (seconds)
            retrieval_time: Document retrieval time (seconds)
            generation_time: LLM generation time (seconds)
            cache_hit: Whether query hit cache
            num_sources: Number of sources retrieved
            mode: Query mode (simple/adaptive)
            metadata: Additional metadata
        """
        metrics = {
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "event": "query_performance",
            "query_length": len(query),
            "response_time_seconds": response_time,
            "retrieval_time_seconds": retrieval_time,
            "generation_time_seconds": generation_time,
            "cache_hit": cache_hit,
            "num_sources": num_sources,
            "mode": mode,
            "metadata": metadata or {}
        }

        # Append to JSONL file
        with open(self.metrics_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(metrics) + '\n')

    def log_system_health(
        self,
        memory_usage_mb: float,
        cpu_percent: float,
        gpu_memory_mb: float = None,
        active_connections: int = 0,
        cache_size_mb: float = 0,
        metadata: Dict[str, Any] = None
    ) -> None:
        """
        Log system health metrics

        Args:
            memory_usage_mb: Memory usage in MB
            cpu_percent: CPU usage percentage
            gpu_memory_mb: GPU memory usage in MB
            active_connections: Number of active connections
            cache_size_mb: Cache size in MB
            metadata: Additional metadata
        """
        metrics = {
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "event": "system_health",
            "memory_usage_mb": memory_usage_mb,
            "cpu_percent": cpu_percent,
            "gpu_memory_mb": gpu_memory_mb,
            "active_connections": active_connections,
            "cache_size_mb": cache_size_mb,
            "metadata": metadata or {}
        }

        # Append to JSONL file
        with open(self.metrics_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(metrics) + '\n')


# Global logger instances
_app_logger: logging.Logger = None
_perf_logger: PerformanceLogger = None


def get_logger(name: str = None) -> logging.Logger:
    """
    Get application logger

    Args:
        name: Logger name (defaults to tactical-rag)

    Returns:
        Configured logger instance
    """
    global _app_logger

    if _app_logger is None:
        structured_logger = StructuredLogger(
            name=name or "tactical-rag",
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            log_dir=os.getenv('LOG_DIR', './logs'),
            log_format=os.getenv('LOG_FORMAT', 'json')
        )
        _app_logger = structured_logger.get_logger()

    return _app_logger


def get_performance_logger() -> PerformanceLogger:
    """
    Get performance logger

    Returns:
        Performance logger instance
    """
    global _perf_logger

    if _perf_logger is None:
        _perf_logger = PerformanceLogger(
            log_dir=os.getenv('LOG_DIR', './logs')
        )

    return _perf_logger


# Export commonly used functions
__all__ = [
    'StructuredLogger',
    'PerformanceLogger',
    'get_logger',
    'get_performance_logger'
]
