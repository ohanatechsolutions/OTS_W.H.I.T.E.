"""PyInstaller entry point; imports GUI as a package, preserving relative imports."""
from ots_white.gui import main

if __name__ == "__main__":
    main()
