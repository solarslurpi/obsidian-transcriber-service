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

class KeyException(AppException):
    """Exception raised for errors during local file operations."""
    def __init__(self, message="Error creating key for state cache."):
        super().__init__(message)

class AddChapterException(AppException):
    """Exception raised for errors during chapter addition."""
    def __init__(self, message="Error adding chapter to transcription state."):
        super().__init__(message)
class TranscriberException(AppException):
    """Exception raised for errors during transcription."""
    def __init__(self, message="Error during transcription."):
        super().__init__(message)

class ProgressHookException(Exception):
    def __init__(self, message="A custom error occurred"):
        self.message = message
        super().__init__(self.message)

class YouTubeDownloadException(Exception):
    def __init__(self, message="Exception raised either during YouTube downloading or post processing the content into metadata and chapters."):
        self.message = message
        super().__init__(self.message)

class SendSSEDataException(Exception):
    def __init__(self, message="Exception raised attempting to format state properties to send over sse."):
        self.message = message
        super().__init__(self.message)

class MissingContentException(Exception):
    def __init__(self, message="Exception raised when client requests missing content and the request can't be parsed."):
        self.message = message
        super().__init__(self.message)
        MissingContentException
