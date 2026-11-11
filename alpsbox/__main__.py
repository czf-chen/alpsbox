# -*- coding: utf-8 -*-
"""Allow running the package directly via python -m alpsbox."""
import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
