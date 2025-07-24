import os
import sys

# Add the parent directory containing folder2md4llms to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from folder2md4llms.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
