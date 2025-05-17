"""
Test script to verify imports are working correctly.
"""
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("Testing imports...")
print(f"Python version: {sys.version}")
print(f"Current working directory: {Path.cwd()}")
print(f"Project root: {project_root}")
print(f"Python path: {sys.path}")

try:
    from src.search import FileSearcher, SearchAlgorithm
    print("Successfully imported FileSearcher and SearchAlgorithm")
except ImportError as e:
    print(f"Error importing search module: {e}")
    sys.exit(1)

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from tabulate import tabulate
    print("Successfully imported matplotlib and tabulate")
except ImportError as e:
    print(f"Error importing visualization modules: {e}")
    sys.exit(1)

print("All imports successful!") 