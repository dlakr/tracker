#!C:\Users\py_venv\venv_ttracker\Scripts\python.exe
from os import listdir
import os
import platform
import report as r
from pynput import mouse, keyboard
import sqlite3
import logging
import time
from PRINT_LINK import write_log
from PRINT_LINK import plink
import socket
from datetime import datetime
import atexit
import re

# with open(log_file, "w"):
#     pass

c_name = socket.gethostname()
log_file = f"ttracker-{c_name}.log"
lock_file_path = "../script.lock"
# def write_log(info):
#     with open(log_file, "a") as f:
#         f.write(str(f"\n{info}"))


def get_os():
    system = platform.system()
    if system == 'Windows':
        os = "win"
    else:
        os = "mac"
    return os



os = get_os()

def acquire_lock():
    if os == 'win':
        import locker_win
        locker_win.acquire(lock_file_path)
    else:
        import locker_mac
        locker_mac.acquire(lock_file_path)


def release_lock():
    if os == 'win':
        import locker_win
        locker_win.release(lock_file_path)
    else:
        import locker_mac
        locker_mac.release(lock_file_path)


if os == 'win':

    projects = listdir(r'G:\My Drive\PLICO_CLOUD\PROJECTS')
    archive = listdir(r'G:\My Drive\PLICO_ARCHIVE')


else:
    pass
folders = projects + archive

now = datetime.now()
write_log(f'monitoring started at {now}')
class Tracker:

    """contains all pertaining to tracker & timer"""
    commit_interval = 2
    inactive_cap = 5
    interrupt_delay = 1# must be smaller than commit interval
    survey_interval = 5 # interval at which the project folder is checked for updates


    def __init__(self):

        acquire_lock()
        atexit.register(self.closing)

        # self.survey_project_folder()
        self.conn = sqlite3.connect(r'F:\Dropbox\_Programming\timeTracker\timeTracker-{}.sqlite'.format(c_name))
        # self.conn.set_trace_callback(print)
        self.cur = self.conn.cursor()
        self.cur.execute('''CREATE TABLE IF NOT EXISTS Time 
            (id INTEGER PRIMARY KEY UNIQUE, 
            project_id TEXT,
            date TEXT,
            time INTEGER) ''')

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
        self.project_name = ''
        self.proj_id = self.survey_project_folder()[0]
        self.start = ''
        self.project_text = self.survey_project_folder()[1]
        self.process_current_time = 0
        # self.sql_insert = 'INSERT OR IGNORE INTO Time (project_id, date, time) VALUES ( ?, ?, ?)'
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
        now = datetime.now()
        if self.process_time > self.commit_interval*60:
            intro = f'\nERROR!!!!!\n process time:{self.process_time}\ncommit_interval:{self.commit_interval*60}\n{now}\n'
        else:
            intro = f'\n{now}\n'

        cmd = ''
        date = str(datetime.now().date())
        match = (self.projectNum, date)
        # serial = f'{self.projectNum}-{date}'

        cmd = f"SELECT * FROM Time WHERE project_id = ? And date = ? ;"

        # crit = (self.projectNum, date)
        self.cur.execute(cmd, match)
        entry = self.cur.fetchone()



        if entry:

            cmd = f'''UPDATE Time SET time = time + {self.process_time} WHERE project_id = ? And date = ? ;'''
            self.cur.execute(cmd, match)
            printout = f'{intro} TIME ADDED: {self.projectNum} {date}--> {self.process_time}'
        else:

            cmd = 'INSERT OR IGNORE INTO Time (project_id, date, time) VALUES ( ?, ?, ?)'
            self.cur.execute(cmd, (self.projectNum, date, self.process_time))
            printout = f'{intro} NEW ENTRY: {self.projectNum} {date} --> {self.process_time}'
        self.conn.commit()
        self.process_time = 0

        write_log(printout)

    def sql_commit_handler(self, title):

        if self.projectNum == 0:
            pass
        else:
            if self.interrupt:

                # self.start = re.sub('[:.]', '-', str(datetime.now().time()))
                # self.process_time = self.interrupt_time
                self.interrupt_time = 0
                self.write_sql()
                # self.process_time = 0



            elif self.projectNum == title:

                # if self.process_current_time == 0:
                #     self.start = re.sub('[:.]', '-', str(datetime.now().time()))
                # self.process_time += 1

                if self.process_time >= self.commit_interval * 60:

                    # if self.process_time <= self.commit_interval*60:
                    #
                    #     self.write_sql()
                    # else:
                    self.write_sql()

            elif self.not_project_file():
                self.not_project_file_counter += 1
            else:
                pass

            # date_time = time.time()
            # self.timestamp[title] = int(date_time)

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

            if (self.interrupt_delay * 60) == self.interrupt_time:
                self.latest_tracked = self.projectNum
                self.interrupt = True
                self.projectNum = title
            # elif self.not_project_file_counter >= (self.interrupt_delay * 60):


            else:
                self.interrupt_time += 1


    def survey_project_folder(self):
        match = r"[A-Za-z\d]+"
        # txt_match = r"[a-zA-Z]+"
        parts = []
        proj_num = []
        proj_text = []

        for i in folders:

            info = re.findall(match, i)
            num = info.pop(0)

            parts.reverse()

            try:
                proj_num.append(int(num))
            except ValueError as error:
                pass
                # write_log(error)

            for j in info:
                if j.lower() not in proj_text:
                    # try:
                    #     int(j)
                    # except ValueError:
                    proj_text.append(j.lower())
        proj_text.sort()
        proj_num.sort(reverse=True)
        proj_info = (proj_num, proj_text)
        return proj_info

    def idle(self):
        value = 0
        if self.inactive_cap == 0:
            value = 1
        elif self.not_project_file_counter >= (self.interrupt_delay * 60):
            value = 0
        else:
            if self.inactive_time < (self.inactive_cap * 60) and self.inactive_cap != 0:
                value = 1

            else:

                if self.process_time > 1:
                    # self.end = re.sub('[:.]', '-', str(datetime.now().time()))
                    self.write_sql()
                else:
                    self.current_project = ''
                    self.projectNum = 0
                    self.process_time = 0

        return value

    def not_project_file(self):
        # time = self.process_time
        # if not self.valid_title:
        #     self.not_project_file_counter += 1
        # else:
        #     self.not_project_file_counter = 0

        if self.inactive_cap > 0 and self.not_project_file_counter >= self.inactive_cap*60:
            # print('... been idling for {} sec'.format(self.not_project_file_counter - self.inactive_cap*60))
            # self.write_sql()
            # self.process_time = time
            return True
        else:
            return False

    def get_title(self):
        if os == 'win':
            import title_win
            name = title_win.title()
        else:
            import title_mac
            name = title_mac.title()
        return name

    def mac_title(self):
        pass
    def track(self):

        while True:
            r.report(self.conn)
            project_name = self.get_title()
            # print(project_name)
            score = 0
            try:
                id = re.findall('\d+', project_name)[0]

                text = [i.lower() for i in re.findall(r"[A-Za-z]+", project_name)]


                scored = []
                # print(self.project_text)
                for i in self.project_text:


                    for j in text:
                        if i == j:
                            score += 1
                            scored.append(j)
                print(type(score))
                # print(scored)


            except Exception as error:
                # write_log(error)
                self.valid_title = False
            self.inactive_time += 1
            if self.elapsed_time % (self.survey_interval * 60) == 0:
                self.proj_id = self.survey_project_folder()[0]
                self.project_text = self.survey_project_folder()[1]
            self.elapsed_time += 1


            try:
                title = int(id)

            except (ValueError, UnboundLocalError) as error:
                # write_log(error)

                title = self.projectNum
                self.valid_title = False

            if title in self.proj_id:
                # self.project_name = project_name
                self.interrupt_handler(title)
            if score >= 1:
                self.valid_title = True
            elif self.not_project_file():

                self.sql_commit_handler(title)
            write_log(self.process_time)
            time.sleep(1)

    def closing(self):

        self.write_sql()
        self.cur.close()
        release_lock()


if __name__ == '__main__':

    try:
        tracker = Tracker()
        tracker.cur.close()

    except Exception as argument:
        logging.exception("Error occured while executing Time tracker")
        write_log(argument)



