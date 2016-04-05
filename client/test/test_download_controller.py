__author__ = 'zeemi'
import pytest
import requests_mock


def test_worker_thread_should_be_initialized_with_queue(download_controller_cls, queue_with_one_pending_file):
    dc = download_controller_cls(queue_with_one_pending_file)


def test_task_should_be_downloaded(download_controller_cls, queue_with_one_pending_file, pending_file_task, credentials):
    dc = download_controller_cls(queue_with_one_pending_file)
    with requests_mock.mock() as m:
        m.get("http://test.pl/resources/1", text='111111111111111111111111111',
              request_headers={'Authorization': credentials['_basic_auth_str'] })
        dc.download_file(pending_file_task)
    assert m.called


@pytest.fixture
def download_controller_cls():
    from client.download_controller import DownloadController
    return DownloadController

@pytest.fixture
def credentials():
    from requests.auth import _basic_auth_str
    credentials ={'user':'user1','passwd':'passwd1'}
    credentials['_basic_auth_str']=_basic_auth_str(credentials['user'],credentials['passwd'])
    return credentials


@pytest.fixture
def pending_file_task_def(credentials):
    from requests.auth import HTTPBasicAuth
    return {"id": "01", "uri": "http://test.pl/resources/1", "size": 100, "checksum": "200",
            'auth': HTTPBasicAuth(username=credentials['user'], password=credentials['passwd'])}

@pytest.fixture
def queue_with_one_pending_file(pending_file_task):
    from queue import Queue
    q = Queue()
    q.put(pending_file_task)
    return q

@pytest.fixture
def pending_file_task(pending_file_task_def):
    from client.client import PendingFile
    return PendingFile(**pending_file_task_def)