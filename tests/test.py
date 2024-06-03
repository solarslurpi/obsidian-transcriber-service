import os
import sys

# Determine the directory containing this script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Assume the workspace directory is the parent of the script directory
workspace_dir = os.path.abspath(os.path.join(script_dir, '..'))

# Path to the 'src' directory relative to the workspace directory
src_path = os.path.join(workspace_dir, 'src')

# Append the 'src' directory to sys.path
sys.path.append(src_path)

# Print out sys.path to verify
print("sys.path:", sys.path)


from logger_code import LoggerBase
