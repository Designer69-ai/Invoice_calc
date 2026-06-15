import os
import sys

# Add root directory to python path so app can be imported when running inside api/
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
