"""Build script to create Neural Dungeon .exe with PyInstaller."""
import subprocess
import sys


def build():
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", "NeuralDungeon",
        "--windowed",
        "--clean",
        "--noconfirm",
        "--hidden-import", "pygame",
        "neural_dungeon/__main__.py",
    ]
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    print("\nBuild complete! EXE is at: dist/NeuralDungeon.exe")


if __name__ == "__main__":
    build()
