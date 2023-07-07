import unittest
from timeTracker import *

c_name = socket.gethostname()
log_file = f"ttracker_2-{c_name}_test.log"
lock_file_path = "script_2.lock"
database_path = r'F:\Dropbox\_Programming\timeTracker\timeTracker_2-{}_test.sqlite'.format(c_name)

tracker= Tracker()
with open("test_data.json", "r") as f:
    pass
    # data = r.read()

class timeTracker_2_test(unittest.TestCase):

    # def test_count(self):
    #     counter = 5
    #     t = counter
    #     result = 0
    #     while t >= 0:
    #         t -= 1
    #         count(result)
    #     self.assertEquals(result, counter)

    def test_inactive_cap_test(self):
        tracker.inactive_cap = 1/60
        tracker.inactive_time = 1
        result = tracker.inactive_cap_test()
        self.assertTrue(result)

    def test_interrupt_delay_test(self):
        tracker.interrupt_delay = 1/60
        tracker.interrupt_time = 1
        result = tracker.interrupt_delay_test()
        self.assertTrue(result)
    def test_interrupt_test(self):
        pass
    def test_parsed_title_info(self):

        info = tracker.parsed_title_info()
        self.assertEquals(info["ID"], "NO ID")
        self.assertEquals(info["TEXT"], "")
        self.assertEquals(info["SCORE"], 0)

    def test_process_commit_interval_test(self):
        tracker.commit_interval = 1/60
        tracker.process_time = 1
        result = tracker.process_commit_interval_test()
        self.assertTrue(result)

    def test_project_interrupt_updater(self):
        pass

    def test_window_validity_test(self):
        pass




if __name__ == "__main__":
    unittest.main()