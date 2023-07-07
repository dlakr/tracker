import inspect
import socket

c_name = socket.gethostname()
log_file = f"ttracker-{c_name}.log"

def write(info):
    with open(log_file, "a") as f:
        f.write(str(f"\n{info}"))


def write_log(printout, file=None, line=None):

    if file is None:
        file = inspect.stack()[1].filename
    if line is None:
        line = inspect.stack()[1].lineno
    string = f'File "{file}", line {max(line, 1)}'.replace("\\", "/")
    logged = string + '\n' + str(printout)
    write(logged)

    return string
test = ''
def plink(printout, file=None, line=None):

    if file is None:
        file = inspect.stack()[1].filename
    if line is None:
        line = inspect.stack()[1].lineno
    string = f'File "{file}", line {max(line, 1)}'.replace("\\", "/")
    logged = string + '\n' + str(printout)
    print(logged)

    return string




