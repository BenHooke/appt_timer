# build_exe.py
import PyInstaller.__main__

PyInstaller.__main__.run([
    "main.py",              # your main script
    "--name=AppointmentTimer",  # exe name
    "--onefile",            # bundle everything into a single exe
    "--windowed",           # no console window (good for GUI apps)
])
