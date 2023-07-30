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
from PRINT_LINK import write
import socket
from datetime import datetime
import atexit
import re
import threading


def get_os():
    system = platform.system()
    if system == 'Windows':
        osys = "win"
    else:
        osys = "mac"
    return osys


c_name = socket.gethostname()
log_file = f"ttracker-{c_name}.log"
lock_file_path = "script.lock"
database_path = r'timeTracker-{}.sqlite'.format(c_name)

commit_interval = 2
interrupt_delay = 1  # must be smaller than commit interval `
survey_interval = 300  # interval at which the project folder is checked for updates - in seconds
inactive_cap = 300

osys = get_os()

if osys == 'win':
    projects = listdir(r'G:\My Drive\PLICO_CLOUD\PROJECTS')
    archive = listdir(r'G:\My Drive\PLICO_ARCHIVE')
else:
    projects = listdir(r'mac location of project folder')
    archive = listdir(r'mac location of archive folder')

folders = projects + archive
now = datetime.now()
write_log(f'monitoring started at {now}')


def acquire_lock():
    if osys == 'win':
        import locker_win
        locker_win.acquire(lock_file_path)
    else:
        import locker_mac
        locker_mac.acquire(lock_file_path)


def release_lock():
    if osys == 'win':
        import locker_win
        locker_win.release(lock_file_path)
    else:
        import locker_mac
        locker_mac.release(lock_file_path)


def survey_project_folder_old():
    match = r"[A-Za-z\d]+"
    parts = []
    proj_num = []
    proj_text = []
    projects = {}
    for i in folders:
        info = re.findall(match, i)
        num = info.pop(0)
        parts.reverse()
        data = {num: info}
        projects.update(data)
        try:
            proj_num.append(str(int(num)))
        except ValueError as error:
            pass
        for j in info:
            if j.lower() not in proj_text:
                proj_text.append(j.lower())
    proj_text.sort()
    proj_num.sort(reverse=True)
    proj_info = (proj_num, proj_text)
    return proj_info


def survey_project_folder():
    match = r"[A-Za-z\d]+"
    parts = []
    proj_num = []
    proj_text = []
    projects = {}
    for i in folders:
        info = re.findall(match, i)
        num = info.pop(0)
        parts.reverse()
        # new way:
        text = []
        for i in info:
            text.append(i.lower())
        data = {num: text}
        projects.update(data)
        # old way
        try:
            proj_num.append(str(int(num)))
        except ValueError as error:
            pass
        for j in info:
            if j.lower() not in proj_text:
                proj_text.append(j.lower())
    proj_text.sort()
    proj_num.sort(reverse=True)
    proj_info = (proj_num, proj_text)
    print(projects)
    return projects

# todo: still commits double entry need to find out why
class Tracker:

    def __init__(self):

        acquire_lock()
        atexit.register(self.closing)
        self.conn = sqlite3.connect(database_path)
        self.cur = self.conn.cursor()
        self.cur.execute(
            '''CREATE TABLE IF NOT EXISTS Time 
            (id INTEGER PRIMARY KEY UNIQUE, 
            project_id TEXT,
            date TEXT,
            time INTEGER) '''
        )
        self.latest_tracked = None
        self.current_id_tracked = 0
        self.current_project = ''
        self.inactive_time = 0
        self.interrupt_time = 0
        self.elapsed_time = 0
        self.process_time = 0
        self.proj_info = survey_project_folder()
        self.mouse_listener = mouse.Listener(on_move=self.on_move)
        self.mouse_listener.start()
        self.key_listener = keyboard.Listener(on_press=self.kb_down, on_release=self.up)
        self.key_listener.start()
        # self.track()

    def on_move(self, x, y):
        self.inactive_time = 0

    def kb_down(self, key):
        self.inactive_time = 0

    def up(self, key):
        if key == keyboard.Key.esc:
            return False

    def write_sql(self):
        project_id = int(self.current_id_tracked)
        if self.process_time != 0:#project_id != 0 and
            now = datetime.now()
            intro = f'\n{now}\n'
            date = str(datetime.now().date())
            match = (project_id, date)
            cmd = f"SELECT * FROM Time WHERE project_id = ? And date = ? ;"
            self.cur.execute(cmd, match)
            entry = self.cur.fetchone()
            if entry:
                cmd = f'''UPDATE Time SET time = time + {self.process_time} WHERE project_id = ? And date = ? ;'''
                self.cur.execute(cmd, match)
                printout = f'{intro} TIME ADDED: {project_id} {date}--> {self.process_time}'
            else:
                cmd = 'INSERT OR IGNORE INTO Time (project_id, date, time) VALUES ( ?, ?, ?)'
                self.cur.execute(cmd, (project_id, date, self.process_time))
                printout = f'{intro} NEW ENTRY: {project_id} {date} --> {self.process_time}'
            self.conn.commit()
            self.zero_timers()
            write_log(printout)


    def timer_manager(self):
        self.process_time += 1
        if self.process_commit_interval_test():
            self.write_sql()
            write(f'INTERVAL')
        if self.inactive_cap_test():
            self.inactive_triggered()
            self.process_time -= 1
        if self.interrupt_test():
            self.interrupt_time += 1
            if self.interrupt_delay_test():
                self.window_id_validity_test()
                self.interrupt_time = 0
                self.write_sql()
                write(f"INTERRUPT")
                self.project_info_updater()
                # else:
                #     self.zero_timers()
        else:
            """reset interrupt_time"""
            self.interrupt_time = 0
        if self.elapsed_time_test():
            self.refresh_project_folder_content()
        self.elapsed_time += 1
        self.inactive_time += 1


    def refresh_project_folder_content(self):

        self.proj_info = survey_project_folder()


    def  zero_timers(self):
        self.process_time = 0
        self.interrupt_time = 0


    def project_info_updater(self):
        info = self.parsed_title_info()
        window_id = info["ID"]
        if self.window_id_validity_test():
            """switch to new project"""
            self.current_id_tracked = window_id
            self.project_text = info["TEXT"]
        else:
            """TRACK PROJECT 0000 WHEN THE WINDOW TITLE IS NOT VALID"""
            self.current_id_tracked = 0

    def inactive_triggered(self):
        if self.process_time > 1:
            self.write_sql()
            write(f"INACTIVE")
        else:
            self.current_project = ''
            self.current_id_tracked = 0
            self.process_time = 0

    def elapsed_time_test(self):
        if self.elapsed_time % (survey_interval) == 0:

            return True
        else:
            return False

    def inactive_cap_test(self):
        if self.inactive_time >= inactive_cap * 60:
            return True
        else:
            return False

    def process_commit_interval_test(self):
        if self.process_time >= commit_interval * 60:
            return True
        else:
            return False

    def interrupt_delay_test(self):
        if self.interrupt_time >= interrupt_delay * 60:
            return True
        else:
            return False

    def interrupt_test(self):
        window_id = self.parsed_title_info().get("ID", 0)
        # print(window_id)

        if int(self.current_id_tracked) != int(window_id):

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

    def window_id_validity_test(self):
        window_info = self.parsed_title_info()
        window_id = window_info.get("ID", 0)
        title_score = window_info.get("SCORE", 0)
        if window_id in list(self.proj_info.keys()):
            if title_score >= 1:
                return True
            else:
                return False
        else:
            return False

    def parsed_title_info(self):
        """keys: ID, TEXT, SCORE"""
        result = {}
        window_title = self.get_title()
        id = re.findall(r'\d+', window_title)
        if id:
            wid = id[0]
        else:
            wid = 0
        result.update({"ID": wid})
        result.update({"TEXT": [i.lower() for i in re.findall(r"[A-Za-z]+", window_title)]})

        project_text = self.proj_info.get(wid)
        print(project_text)
        if project_text:
            for i in project_text:
                for j in result["TEXT"]:
                    if i == j:
                        result["SCORE"] = result.get("SCORE", 0) + 1
                    else:
                        result["SCORE"] = result.get("SCORE", 0)
        else:
            result["SCORE"] = result.get("SCORE", 0)
        print(f"result: {result['SCORE']}")
        return result

    def track(self):
            r.report()
            self.timer_manager()

    def closing(self):

        self.write_sql()
        self.cur.close()
        release_lock()

if __name__ == '__main__':

    try:
        tracker = Tracker()
        while True:
            tracker.track()
            time.sleep(1)
        # timer = threading.Timer(commit_interval * 60, tracker.track())
        # timer.start()
        # timer.join()

    except Exception as argument:
        logging.exception("Error occured while executing Time tracker")
        write_log(argument)



