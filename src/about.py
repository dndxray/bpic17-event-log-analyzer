import platform
import tkinter
from importlib.metadata import version

PACKAGES = ["pm4py", "pandas", "numpy"]


def get_about_info():
    info = {
        "Python": platform.python_version(),
        "Tk": str(tkinter.TkVersion),
        "Sistem": platform.platform(),
    }
    for name in PACKAGES:
        info[name] = version(name)
    return info


if __name__ == "__main__":
    for key, value in get_about_info().items():
        print(f"{key}: {value}")