import os
import signal

def kill_process(proc):
    pid = int(proc.split()[1])
    os.kill(pid, signal.SIGTERM)


for proc in os.popen('tasklist').read().splitlines()[3:]:

    if 'pythonw.exe' in proc:
        kill_process(proc)
    elif 'python.exe' in proc:
        kill_process(proc)
