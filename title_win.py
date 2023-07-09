import win32gui
import pywintypes
import win32api
def title():
    hwnd = win32gui.GetForegroundWindow()
    name = win32gui.GetWindowText(hwnd)
    # print(win_name)
    return name