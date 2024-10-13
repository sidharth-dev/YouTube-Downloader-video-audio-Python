from cx_Freeze import setup, Executable

setup(
    name="YouTube Downloader",
    version="1.0",
    description="Download YouTube videos",
    executables=[Executable("youtube_downloader.py", base="Win32GUI", icon="icon.ico")]
)
