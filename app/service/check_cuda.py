import ctranslate2
import os
import sys
from pathlib import Path

def find_cudnn_path():
    required_files = [
        "cudnn64_9.dll",
        "cudnn_ops64_9.dll",
        "cudnn_cnn_infer64_9.dll",
        "cudnn_adv_infer64_9.dll",
    ]
    
    possible_paths = [
        Path(sys.executable).parent.parent / "Lib" / "site-packages" / "nvidia" / "cudnn" / "bin",
        Path("C:/Program Files/NVIDIA/CUDNN/v9.5/bin"),
        Path("C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v12.3/bin"),
        Path(sys.executable).parent.parent / "Lib" / "site-packages" / "ctranslate2",
    ]
    
    print("\nSearching for cuDNN files:")
    for path in possible_paths:
        print(f"\nChecking {path}")
        if path.exists():
            found_files = []
            missing_files = []
            for required_file in required_files:
                if (path / required_file).exists():
                    found_files.append(required_file)
                else:
                    missing_files.append(required_file)
            
            if found_files:
                print(f"Found files in {path}:")
                for file in found_files:
                    print(f"  ✓ {file}")
            if missing_files:
                print(f"Missing files in {path}:")
                for file in missing_files:
                    print(f"  × {file}")
            
            if not missing_files:  # If all required files are found
                return str(path)
    return None

# Print basic environment info
print("Python executable:", sys.executable)
print("Python version:", sys.version)

# Print CUDA paths from environment with deduplication and existence check
print("\nCUDA paths in PATH:")
seen_paths = set()
for path in os.environ['PATH'].split(os.pathsep):
    if 'cuda' in path.lower():
        # Normalize path for comparison
        normalized_path = os.path.normpath(path.lower())
        if normalized_path not in seen_paths:
            seen_paths.add(normalized_path)
            exists = os.path.exists(path)
            print(f"{path} {'[EXISTS]' if exists else '[NOT FOUND]'}")

# Add more detailed CUDA environment checking
print("\nDetailed CUDA Environment:")
cuda_vars = ['CUDA_HOME', 'CUDA_PATH', 'CUDA_PATH_V11_0', 'CUDA_PATH_V12_2', 'CUDA_PATH_V12_3']
for var in cuda_vars:
    value = os.getenv(var)
    if value:
        exists = os.path.exists(value)
        print(f"{var}: {value} {'[EXISTS]' if exists else '[NOT FOUND]'}")

# Check CTranslate2
print(f"\nCTranslate2 version: {ctranslate2.__version__}")
print(f"CUDA device count: {ctranslate2.get_cuda_device_count()}")

# Check compute types
print("\nSupported compute types:")
try:
    print(f"CUDA: {ctranslate2.get_supported_compute_types('cuda')}")
except Exception as e:
    print(f"Error getting CUDA compute types: {e}")
print(f"CPU: {ctranslate2.get_supported_compute_types('cpu')}")

# Find cuDNN
cudnn_path = find_cudnn_path()
if cudnn_path:
    print(f"\nFound cuDNN path: {cudnn_path}")
    # Add to PATH if not already there
    if cudnn_path not in os.environ['PATH']:
        os.environ['PATH'] = cudnn_path + os.pathsep + os.environ['PATH']
        print("Added cuDNN path to PATH")
else:
    print("\nCould not find cuDNN path")

# Try to load a model
print("\nTrying to load a model:")
try:
    model = WhisperModel("tiny", device="cuda", compute_type="int8")
    print("Successfully loaded model on CUDA")
except Exception as e:
    print(f"Failed to load on CUDA: {e}")