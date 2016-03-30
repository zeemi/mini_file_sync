from collections import namedtuple
import json

__author__ = 'zeemi'
from threading import Thread
import argparse
import requests
import argparse
import sys
import logging


from .configurator import Configurator
from requests_oauthlib import OAuth1
from queue import Queue


class FileSyncC(object):

    def set_logging(self):
        import http.client as http_client
        http_client.HTTPConnection.debuglevel=1
        logging.basicConfig()
        logging.getLogger().setLevel(logging.DEBUG)
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True

    def parse_args(self, args):
        parser = argparse.ArgumentParser(description='FileSyncClient')
        parser.add_argument('--interval', type=int, help='number of seconds between checking incoming transfer', required=False)
        parser.add_argument('--user', type=str, help='user', required=False)
        parser.add_argument('--passwd', type=str, help='password', required=False)
        parser.add_argument('--parallel_downloads', type=int, help='number of allowed parallel downloads', required=False)
        parser.add_argument('--server_address', type=str, help='url of server which is buffering files', required=False)
        return {k : v for k, v in vars(parser.parse_args(args)).items() if v is not None}

    def evaluate_configuration(self, cmdline_options):
        from requests.auth import HTTPBasicAuth
        configurator = Configurator()
        cfg = configurator.process_config(cmdline_options)
        self.server_address = cfg['server_address']
        self.auth = HTTPBasicAuth(username=cfg['user'], password=cfg['passwd'])
        self.interval = cfg['interval']
        self.parallel_downloads=cfg['parallel_downloads']

    def check_pending_files(self):
        '''
        consumer (client) - application, proxy,
        service provider (server),
        user (resource owner).
        '''
        # from requests.auth import HTTPDigestAuth
        # auth = OAuth1(client_key='YOUR_APP_KEY',
        #               client_secret='YOUR_APP_SECRET',
        #               resource_owner_key='USER_OAUTH_TOKEN',
        #               resource_owner_secret='USER_OAUTH_TOKEN_SECRET')
        response = requests.get(self.server_address, auth=self.auth)
        try:
            data = json.loads(response.text)
            PendingFile = namedtuple('PendingFile', ['id', 'uri','size','checksum'])
            for file in data:
                pending_file = PendingFile(**file)
                self.pending_files_queue.put(pending_file)
        except ValueError:
            logging.warn('corrupted data receive in pending_files_list: %s'%response.text)
        return response

    def start_polling_thread(self):
        t = Thread(target=self.polling)
        t.start()

    def polling(self):
        from time import sleep
        while True:
            self.check_pending_files()
            logging.debug("Get pending files list")
            sleep(self.interval)

    def start(self):
        self.evaluate_configuration(self.parse_args(sys.argv[1:]))
        self.set_logging()
        self.check_pending_files()
        self.create_pending_files_queue()
        self.start_polling_thread()

    def create_pending_files_queue(self):
        self.pending_files_queue = Queue()

    def create_workers_threads(self):
        self.workers_threads = []
        for n in range(self.parallel_downloads):
            t = Thread(target=lambda x:print(x), args=(self.pending_files_queue,))
            t.deamon = True
            t.start()
            self.workers_threads.append(t)


if __name__ == '__main__':
    fsc = FileSyncC()
    fsc.start()
