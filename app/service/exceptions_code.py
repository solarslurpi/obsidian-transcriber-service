#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
###########################################################################################
# Author: Margaret Johnson
# Copyright (c) 2024 Margaret Johnson
###########################################################################################

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

class YouTubePostProcessingException(Exception):
    def __init__(self, message="Exception raised during YouTube post processing the content into metadata and chapters."):
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
