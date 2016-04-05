from collections import namedtuple

__author__ = 'zeemi'
from mock import patch
import requests_mock
import pytest
import json

def test_parse_cmdline_parameters(file_sync_client, input_parameters):
    for k, v in input_parameters.items():
        parsed = file_sync_client.parse_args(['--%s' % k, str(v)])
        assert parsed == {k: v}, 'key=%s' % k


def test_input_parameters_should_be_send_to_configurator(file_sync_client, input_parameters):
    from client.configurator import Configurator
    with patch.object(Configurator, 'process_config', return_value=input_parameters) as mock_process_config:
        file_sync_client.evaluate_configuration(input_parameters)
    mock_process_config.assert_called_once_with(input_parameters)


def test_server_address_from_configurator_should_be_stored(configured_file_sync_client, input_parameters):
    assert configured_file_sync_client.server_address == input_parameters['server_address']


def test_auth_object_should_be_stored_after_configuration(configured_file_sync_client):
    from requests.auth import AuthBase
    assert isinstance(configured_file_sync_client.auth, AuthBase)


def test_server_polling_requests_should_use_auth_basic(configured_file_sync_client_with_queue, server_address,
                                                       pending_files_list_json, input_parameters):
    from requests.auth import _basic_auth_str
    expected_auth_value = _basic_auth_str(username=input_parameters['user'],password=input_parameters['passwd'])
    with requests_mock.mock() as m:
        m.get(server_address, text=pending_files_list_json, request_headers={'Authorization' : expected_auth_value })
        response = configured_file_sync_client_with_queue.check_pending_files()
    assert m.called
    assert response.text == pending_files_list_json

def test_check_pending_files_should_populate_pending_files_list_with_namedtuple(configured_file_sync_client_with_queue,
                                                                                server_address,
                                                                                pending_files_list_json,
                                                                                pending_file_class):
    auth = configured_file_sync_client_with_queue.auth
    expected_file1, expected_file2 = json.loads(pending_files_list_json)
    ef1, ef2 = pending_file_class(auth=auth, **expected_file1), \
               pending_file_class(auth=auth, **expected_file2)
    with requests_mock.mock() as m:
        m.get(server_address, text=pending_files_list_json)
        configured_file_sync_client_with_queue.check_pending_files()


    queue = configured_file_sync_client_with_queue.pending_files_queue
    assert not queue.empty()
    task1 = queue.get()
    assert not queue.empty()
    task2 = queue.get()
    assert queue.empty()
    # comparing namedtuple
    assert task1.id == expected_file1['id']
    assert task1.uri == expected_file1['uri']
    assert task1.size == expected_file1['size']
    assert task1.checksum == ef1.checksum

    assert task1 == ("01", "http://test.pl/resources/1", 100, "200", auth)
    assert task2 == ef2


def test_empty_pending_files_list_should_not_populate_queue(configured_file_sync_client_with_queue,
                                                            empty_pending_files_list_json,
                                                            server_address):
    with requests_mock.mock() as m:
        m.get(server_address, text=empty_pending_files_list_json)
        configured_file_sync_client_with_queue.check_pending_files()
    assert configured_file_sync_client_with_queue.pending_files_queue.empty()


def test_corrupted_json_in_pending_files_list_should_not_rise_error(configured_file_sync_client_with_queue,
                                                            server_address):
    with requests_mock.mock() as m:
        m.get(server_address, text='{fdasfx:ssf:ss]')
        configured_file_sync_client_with_queue.check_pending_files()
    assert configured_file_sync_client_with_queue.pending_files_queue.empty()

def test_invalid_parameters_in_pending_files_list_should_not_rise_error(configured_file_sync_client_with_queue,
                                                            server_address):
    with requests_mock.mock() as m:
        m.get(server_address, text='[{"id":"01", "uri":"http://test.pl/resources/1","wally": "owner" ,"size":100, "checks":"200"}')
        configured_file_sync_client_with_queue.check_pending_files()
    assert configured_file_sync_client_with_queue.pending_files_queue.empty()


def test_pending_file_queue_should_be_stored_in_client(configured_file_sync_client_with_queue):
    from queue import Queue
    assert isinstance(configured_file_sync_client_with_queue.pending_files_queue, Queue)


def test_client_should_create_configured_number_of_workers_threads(configured_file_sync_client, parallel_downloads):
    configured_file_sync_client.create_pending_files_queue()
    configured_file_sync_client.create_workers_threads()
    assert len(configured_file_sync_client.workers_threads) == parallel_downloads

# def test_server_polling_should_be_called_in_configured_intervals(configured_file_sync_client, polling_interval):
#     from client.client import FileSyncC
#     from time import sleep
#     with patch.object(FileSyncC, 'check_pending_files') as mock_check_pending_files:
#         configured_file_sync_client.start_polling_thread()
#         sleep(polling_interval*3+1)
#     from mock import call
#     mock_check_pending_files.assert_has_calls([call(),call(),call()])


def test_pending_file_object_should_have_all_information_for_downloading(pending_file_class):
    pending_file_class(**{"id":"01", "uri":"http://test.pl/resources/1", "size":100, "checksum":"200", "auth":"whatever"})

# ------------ resources ------------
@pytest.fixture
def file_sync_client():
    from client.client import FileSyncC
    return FileSyncC()


@pytest.fixture
def configured_file_sync_client(file_sync_client, input_parameters):
    from client.configurator import Configurator
    with patch.object(Configurator, 'process_config', return_value=input_parameters) as mock_process_config:
        file_sync_client.evaluate_configuration(input_parameters)
    return file_sync_client

@pytest.fixture
def configured_file_sync_client_with_queue(configured_file_sync_client):
    configured_file_sync_client.create_pending_files_queue()
    return configured_file_sync_client


@pytest.fixture
def server_address():
    return 'http://testserver.pl'


@pytest.fixture
def polling_interval():
    return 2


@pytest.fixture
def parallel_downloads():
    return 10


@pytest.fixture
def input_parameters(polling_interval, server_address, parallel_downloads):
    return {'interval': polling_interval,
            'user': 'someuser',
            'passwd': 'password',
            'parallel_downloads': parallel_downloads,
            'server_address': server_address}


@pytest.fixture
def pending_files_list_json():
        return '''[{"id":"01", "uri":"http://test.pl/resources/1", "size":100, "checksum":"200"},
               {"id":"02", "uri":"http://test.pl/resources/2", "size":100, "checksum":"300"}]'''

@pytest.fixture
def empty_pending_files_list_json():
    return '''[]'''


@pytest.fixture
def pending_files_parameters():
    return ['id', 'uri','size','checksum']


@pytest.fixture
def pending_file_class():
    from client.client import PendingFile
    return PendingFile
