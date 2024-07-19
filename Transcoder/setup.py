import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
    "packages": ["os", "struct", "json"],
    "excludes": [],
}

# Base is set to "Console" for console application
base = None
if sys.platform == "win32":
    base = "Console"

setup(
    name="HBJSON_Trasncoder",
    version="1.0",
    description="Two Way Converter for Houdini Point Cache files",
    options={"build_exe": build_exe_options},
    executables=[Executable("HBJSON_Trasncoder.py", base=base)],
)
