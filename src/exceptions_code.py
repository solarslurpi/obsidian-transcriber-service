# exceptions_code.py

from fastapi import HTTPException

from global_stuff import global_message_queue
from logger_code import LoggerBase
from utils import format_sse

class AppException(Exception):
    """Base exception class for the application."""
    def __init__(self, message="An error occurred"):
        self.message = message
        super().__init__(self.message)

class DownloadException(AppException):
    """Exception raised for errors during YouTube audio download."""
    def __init__(self, message="Error downloading YouTube audio"):
        super().__init__(message)

class TranscriptionException(AppException):
    """Exception raised for errors during the transcription process."""
    def __init__(self, message="Error during transcription"):
        super().__init__(message)

class MetadataExtractionException(AppException):
    """Exception raised for errors during metadata extraction."""
    def __init__(self, message="Error extracting metadata"):
        super().__init__(message)

class LocalFileException(AppException):
    """Exception raised for errors during local file operations."""
    def __init__(self, message="Error during local file operations"):
        super().__init__(message)

async def handle_exception(exception, status_code, detail, logger: LoggerBase=None):
    error_msg = str(exception)
    message = format_sse("error", error_msg)
    logger.debug(f"handle_exception: {error_msg}")
    await global_message_queue.put(message)
    return HTTPException(status_code=status_code, detail=detail)
