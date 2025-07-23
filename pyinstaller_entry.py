import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "folder2md4llms"))

from folder2md4llms.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
