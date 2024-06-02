###########################################################################################
# Author: HappyDay Johnson
# Version: 0.02
# - fixed `AttributeError: 'NoneType' object has no attribute 'f_back'` by breaking if f.f_back
#   is None 2024-05-11
# Date: 2024-03-20
# Summary: This module enhances logging with a custom 'FLOW' level for detailed application flow
# events, positioned between 'DEBUG' and 'INFO'. It utilizes colorlog for colorized logging,
# including caller information like filename and line number in logs for better debugging and
# monitoring. The LoggerBase class facilitates easy setup of these enhanced loggers, promoting
# consistent logging practices with visual cues for severity and context across applications.

# License Information: MIT License

# Copyright (c) 2024 HappyDay Johnson

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
###########################################################################################

import inspect
import logging
import colorlog

# Step 1: Define the custom logging level
FLOW_LEVEL_NUM = 15
logging.addLevelName(FLOW_LEVEL_NUM, "FLOW")

def flow(self, message, *args, **kwargs):
    """
    Logs a message with the custom FLOW level. Designed for detailed tracking of application flow,
    using a different color than DEBUG, INFO, WARNING, ERROR.

    Args:
        message (str): The message to log.
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.

    Example:
        logger.flow("Starting data processing flow.")
    """
    # Utility method for logging messages at the custom FLOW level
    if self.isEnabledFor(FLOW_LEVEL_NUM):
        self._log(FLOW_LEVEL_NUM, message, args, **kwargs) # pylint: disable=protected-access

logging.Logger.flow = flow
class CustomFormatter(colorlog.ColoredFormatter):
    def format(self, record):
        """
        Enhances the base logging format with the filename, line number, and function name of the
        log message's source. Uses stack inspection to enrich log records, aimed at aiding debugging
        and tracking.

        Args:
            record (logging.LogRecord): The log record to format.

        Returns:
            str: The formatted log message with added context information.

        Note:
            Adjusts the stack frame depth to locate the caller, which may need tuning based on usage.
        """
        # Get the stack frame of the caller to the logging call
        f = inspect.currentframe()
        # Go back 2 frames to find the caller
        # Adjust the range as necessary based on your logging setup
        for _ in range(10):
            if f is None:
                break
            f = f.f_back
        if f is not None:
            i = inspect.getframeinfo(f)
        else:
             i = inspect.getframeinfo(inspect.currentframe())

        # Add custom attributes for filename, line number, and function name to the record
        record.custom_pathname = i.filename
        record.custom_lineno = i.lineno
        record.custom_funcname = i.function

        # Now format the message with these custom attributes
        return super(CustomFormatter, self).format(record)

class LoggerBase:
    @staticmethod
    def setup_logger(name=None,level=logging.INFO):
        """
        Configures and returns a logger with a custom, colorized output format. Integrates the custom
        FLOW log level and enhances log messages with detailed source information (file, line, function).
        Ensures unique logger instances through named retrieval, avoiding duplicate log entries.

        Args:
            name (str, optional): The name of the logger. Defaults to 'TranscriptionLogger'.
            level (int, optional): The logging level. Defaults to logging.DEBUG.

        Returns:
            logging.Logger: Configured logger with a colorized output and custom formatting.

        Example:
            logger = LoggerBase.setup_logger('MyAppLogger', logging.INFO)
        """
        logger_name = 'TranscriptionLogger' if name is None else name
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)  # Set the logging level

        # Check if the logger already has handlers to avoid duplicate messages
        if not logger.handlers:
            # Define log format
            log_format = (
            "%(log_color)s[%(levelname)-3s]%(reset)s "
            "%(log_color)s%(custom_pathname)s:%(custom_lineno)d%(custom_funcname)s\n"
            "%(reset)s%(message_log_color)s%(message)s"
        )
            colors = {
                'DEBUG': 'green',
                'INFO': 'yellow',
                'WARNING': 'purple',
                'ERROR': 'red',
                'CRITICAL': 'bold_red',
                'FLOW': 'cyan',  # Assign a color to the "FLOW" level
            }

            # Create a stream handler (console output)
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.DEBUG)  # Set the logging level for the handler

            formatter = CustomFormatter(log_format, log_colors=colors, reset=True,
                                        secondary_log_colors={'message': colors})

            stream_handler.setFormatter(formatter)
            logger.addHandler(stream_handler)


        return logger
