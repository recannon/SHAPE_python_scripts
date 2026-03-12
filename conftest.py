#Last modified by @recannon 10/03/2026

#Runs when using pytest, to temporarily add pyshape to PYTHONPATH (if not already)
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))