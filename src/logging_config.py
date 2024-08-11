# src/logging_config.py
import logging

class ModuleFilter(logging.Filter):
    def __init__(self, allowed_modules):
        self.allowed_modules = allowed_modules

    def filter(self, record):
        return record.module in self.allowed_modules

# Define the allowed modules
allowed_modules = ['app']

# Configure the root logger
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(pathname)s:%(lineno)d ',
    handlers=[
        logging.StreamHandler()
    ]
)
# Set the logging levels
logging.getLogger('sse_starlette.sse').setLevel(logging.WARNING)
logging.getLogger('watchfiles.main').setLevel(logging.WARNING)
logging.getLogger('multipart.multipart').setLevel(logging.WARNING)
logging.getLogger('transcription_state_code').setLevel(logging.WARNING)
logging.getLogger('metadata_extractor_code').setLevel(logging.WARNING)
logging.getLogger('utils').setLevel(logging.WARNING)
logging.getLogger('youtube_handler_code').setLevel(logging.WARNING)
logging.getLogger('transcription_code').setLevel(logging.WARNING)
logging.getLogger('app').setLevel(logging.DEBUG)
logging.getLogger('process_check_code').setLevel(logging.WARNING)
logging.getLogger('faster_whisper').setLevel(logging.WARNING)
