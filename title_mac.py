# import Quartz
import time

def get_active_window_title():
    window = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements, Quartz.kCGNullWindowID)
    print(window)
    for w in window:
        if w.get('kCGWindowOwnerName') == Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements, Quartz.kCGNullWindowID)[0].get('kCGWindowOwnerName'):
            window_name = w.get('kCGWindowName', 'No Title for Window')
            return window_name

while True:
    print(get_active_window_title())
    time.sleep(1)

