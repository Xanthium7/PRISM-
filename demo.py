"""Root convenience entry point for the PRISM demo."""
import sys

# Prevent Python from creating __pycache__ folders
sys.dont_write_bytecode = True

from prism.demo import main

if __name__ == "__main__":
    main()
