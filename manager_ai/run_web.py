#!/usr/bin/env python3
"""
Start the Manager AI web app. Run from the project root:
  python -m manager_ai.run_web
Then open in your browser: http://127.0.0.1:5000/
"""
import sys
from pathlib import Path

# Ensure project root is on path when run as script
root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from manager_ai.app import app

if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    print(f"Manager AI: open in your browser → http://127.0.0.1:{port}/")
    app.run(host="0.0.0.0", port=port, debug=debug)
