
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Ensure PYTHONPATH is set correctly
print(os.getenv('PYTHONPATH'))
from logger_code import LoggerBase
