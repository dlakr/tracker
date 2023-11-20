import portalocker
import datetime
import socket
# from PRINT_LINK import write_log
# c_name = socket.gethostname()
# log_file = f"ttracker-{c_name}.log"

# def write_log(info):
#     with open(log_file, "a") as f:
#         f.write(str(f"\n{info}"))

def acquire(lock_file_path):
    with open(lock_file_path, 'w') as lockfile:
        try:
            portalocker.lock(lockfile, portalocker.LOCK_EX | portalocker.LOCK_NB)
        except IOError:
            now = datetime.today().date()
            print(f"{now} - Another instance is running")
            quit()

def release(lock_file_path):
    with open(lock_file_path, 'w') as lockfile:
        portalocker.lock(lockfile, portalocker.LOCK_UN)
    print('releasing lock')