
import datetime


def acquire(lock_file_path):
    with open(lock_file_path, 'w') as lockfile:
        try:
            portalocker.lock(lockfile, portalocker.LOCK_EX | portalocker.LOCK_NB)
        except IOError:
            now = datetime.today().date()
            write_log(f"{now} - Another instance is running")
            quit()


def release(lock_file_path):
    with open(lock_file_path, 'w') as lockfile:
        portalocker.lock(lockfile, portalocker.LOCK_UN)
    print('releasing lock')