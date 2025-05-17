# This file makes tests a package

import sys, pathlib
root = pathlib.Path(__file__).resolve().parents[1]
lib_path = root / "packages" / "libs" / "medflowai"
if str(lib_path) not in sys.path:
    sys.path.insert(0, str(root))
