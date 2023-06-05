#!C:\Users\py_venv\venv_ttracker\Scripts\python.exe
from os import listdir
import platform
# import pyautogui
from pynput import mouse, keyboard
import sqlite3
import logging
import time
import win32gui
import socket
import win32process
# from paramiko import SSHClient
# from paramiko import RSAKey
from datetime import datetime
import atexit
import re

# with open(log_file, "w"):
#     pass

c_name = socket.gethostname()
log_file = f"ttracker-{c_name}.log"
def write_log(info):
    with open(log_file, "a") as f:
        f.write(str(f"\n{info}"))


def get_os():
    system = platform.system()
    if system == 'Windows':
        os = "win"
    else:
        os = "mac"
    return os



os = get_os()

if os == 'win':

    projects = listdir('G:\My Drive\PLICO_CLOUD\PROJECTS')
    archive = listdir('G:\My Drive\PLICO_ARCHIVE')
else:
    pass
folders = projects + archive

now = datetime.now()
write_log(f'monitoring started at {now}')
class Tracker:

    """contains all pertaining to tracker & timer"""
    commit_interval = 10
    inactive_cap = 5
    interrupt_delay = 1# must be smaller than commit interval
    survey_interval = 5 # interval at which the project folder is checked for updates

    def __init__(self):
        self.conn = sqlite3.connect(r'F:\Dropbox\_Programming\timeTracker\timeTracker-{}.sqlite'.format(c_name))
        # self.conn.set_trace_callback(print)
        self.cur = self.conn.cursor()
        self.cur.execute('''CREATE TABLE IF NOT EXISTS Time 
            (id INTEGER PRIMARY KEY UNIQUE, 
            project_id TEXT,
            date TEXT,
            start TEXT,
            time INTEGER,
            serial TEXT UNIQUE,
            CONSTRAINT unq UNIQUE (project_id, start)) ''')


        self.latest_tracked = None
        self.projectNum = 0
        self.current_project = ''
        self.interrupt = False
        self.valid_title = False
        self.interrupt_time = 0
        self.elapsed_time = 0
        self.process_time = 0
        self.not_project_file_counter = 0
        self.timestamp = {}
        self.win_name = ''
        self.proj_id = []
        self.start = ''

        self.process_current_time = 0
        self.sql_insert = 'INSERT OR IGNORE INTO Time (project_id, start, date, time, serial) VALUES ( ?, ?, ?, ?, 0, ?)'
          # in minutes
        self.inactive_time = 0
        self.mouse_listener = mouse.Listener(on_move=self.on_move)
        self.mouse_listener.start()
        self.key_listener = keyboard.Listener(on_press=self.kb_down, on_release=self.up)
        self.key_listener.start()
        self.track()


    def on_move(self, x, y):
        self.inactive_time = 0


    def kb_down(self, key):
        self.inactive_time = 0


    def up(self, key):
        if key == keyboard.Key.esc:
            return False


    def write_sql(self):

        date = str(datetime.now().date())
        match = (self.projectNum, date)
        serial = f'{self.projectNum}-{date}'

        find_cmd = f"SELECT * FROM Time WHERE project_id = ? And date = ? ;"
        crit = (self.projectNum, date)
        self.cur.execute(find_cmd, crit)
        entry = self.cur.fetchone()

        if entry:

            cmd = f'''UPDATE Time SET time = time + {self.process_time} WHERE project_id = ? And date = ? ;'''
            self.cur.execute(cmd, match)
        else:
            self.cur.execute(
                'INSERT OR IGNORE INTO Time (project_id, start, date, time, serial) VALUES ( ?, ?, ?, 0,?)',
                (self.projectNum, self.start, date, serial))

        self.conn.commit()
        self.process_time = 0


    def sql_commit_handler(self, title):

        if self.projectNum == 0:
            pass
        else:
            if self.interrupt:
                print('committed {} seconds by interrupt'.format(self.process_time))
                self.start = re.sub('[:.]', '-', str(datetime.now().time()))
                self.process_time = self.interrupt_time
                self.process_current_time = 0
                self.interrupt_time = 0
                self.write_sql()



                # self.interrupt = False

            elif self.projectNum == title:
                # print('process time is now {}'.format(self.process_time))
                if self.process_current_time == 0:
                    self.start = re.sub('[:.]', '-', str(datetime.now().time()))
                self.process_current_time += 1

                if self.process_time == self.commit_interval * 60:
                    print('committed {} sec on scheduled interval'.format(self.process_time))
                    if self.process_current_time <= self.commit_interval*60:
                        print('new')
                        self.write_sql()
                    else:
                        # print(f'pct: {self.process_current_time}')
                        self.write_sql()

            else:
                pass

            date_time = time.time()
            self.timestamp[title] = int(date_time)

    def interrupt_handler(self, title):

        if title == 0 and self.projectNum == 0:
            self.interrupt = False

        elif title != 0 and self.projectNum == 0:
            self.interrupt = False
            self.projectNum = title
            self.process_time += self.idle()

        elif self.projectNum == title and title != 0:
            self.interrupt = False
            self.projectNum = title
            self.process_time += self.idle()

        elif self.projectNum != title:

            print(f'will interrupt in{self.interrupt_delay - self.interrupt_time} sec')
            if (self.interrupt_delay * 60) == self.interrupt_time:
                self.latest_tracked = self.projectNum
                self.interrupt = True
                self.projectNum = title
                print(f'will interrupt in{self.interrupt_delay - self.interrupt_time} sec')
            else:
                self.interrupt_time += 1


            # else:
            #     print(f'will interrupt in{self.interrupt_delay-self.interrupt_time} sec')

    def survey_project_folder(self):


        proj_num = []
        for i in folders:
            try:
                proj_num.append(int(i[:4]))
            except ValueError:
                pass
        proj_num.sort(reverse=True)
        self.proj_id = proj_num
        
    def idle(self):
        value = 0
        if self.inactive_cap == 0:

            value = 1
        else:
            if self.inactive_time < (self.inactive_cap * 60) and self.inactive_cap != 0:
                value = 1

            else:

                if self.process_time > 1:
                    self.end = re.sub('[:.]', '-', str(datetime.now().time()))
                    self.write_sql()
                else:
                    self.current_project = ''
                    self.projectNum = 0
                    self.process_time = 0
        return value

    def not_project_file(self, title):
        time = self.process_time
        if not self.valid_title:
            self.not_project_file_counter += 1
        else:
            self.not_project_file_counter = 0

        if self.inactive_cap > 0 and self.not_project_file_counter > self.inactive_cap*60:
            print('... been idling for {} sec'.format(self.not_project_file_counter - self.inactive_cap*60))
            self.process_time = time
            return True
        else:
            return False



    def win_title(self):
        hwnd = win32gui.GetForegroundWindow()
        win_name = win32gui.GetWindowText(hwnd)
        return win_name

    def mac_title(self):
        pass
    def track(self):

        while True:
            if os == "win":
                win_name = self.win_title()
            else:
                win_name = self.mac_title()

            try:
                starts = re.findall('\d+[\s_-]', win_name)
                self.valid_title = True

            except TypeError as error:
                self.valid_title = False


                starts = ''
            self.inactive_time += 1
            if self.elapsed_time % (self.survey_interval * 60) == 0:
                self.survey_project_folder()
            self.elapsed_time += 1

            if len(starts) > 0:
                try:
                    title = int(starts[0][:4])

                except ValueError as error:
                    title = self.projectNum
            else:

                title = self.projectNum
                self.valid_title = False

            if title in self.proj_id:
                # self.win_name = win_name
                self.interrupt_handler(title)


            if not self.not_project_file(title):
                self.sql_commit_handler(title)
            time.sleep(1)



def exit_update():
    print("closing")
    # print('updating db before closing with {} - {}'.format(t.projectNum, t.process_time))
    # t.db_updater()


if __name__ == '__main__':
    try:
        tracker = Tracker()
        atexit.register(tracker.write_sql)
        tracker.cur.close()
    except Exception as argument:
        logging.exception("Error occured while executing Time tracker")
        write_log(argument)



# now  we need to track the input (keyboard/mouse)



