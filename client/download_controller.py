__author__ = 'zeemi'
import requests
# test_worker_thread_should_get_namedtuple

class DownloadController(object):

    def __init__(self, queue):
        self.current_task = queue.get()

    def download_file(self, current_task):
        response = requests.get(current_task.uri, auth=current_task.auth)
