__author__ = 'zeemi'
import yaml
import pytest
import builtins
from mock import mock_open, patch


def test_configurator_should_store_config_file_path(configurator, config_file_path):
    assert configurator.config_file_path == config_file_path


def test_configurator_should_store_configurable_parameters_list(configurator, configurable_parameters):
    assert configurator.configurable_parameters == configurable_parameters


def test_getting_configuration_from_file(configurator, configuration, config_file_path):
    mocked_open = mock_open(read_data=yaml.dump(configuration))
    with patch.object(builtins, 'open', mocked_open):
        ext_cfg = configurator.get_external_config()
        assert ext_cfg == configuration
    mocked_open.assert_called_once_with(config_file_path)


def test_cmdline_configuration_should_be_stored_first_in_cfg_list(configurator_cls, configuration):
    configurator = configurator_cls(cmdline_options=configuration)
    mocked_open = mock_open(read_data=yaml.dump({}))
    with patch.object(builtins, 'open', mocked_open):
        configurator.process_config()
    assert configurator.cfg_list[0] == configuration


def test_filtering_parameters_during_get_config_from_cmdline_options(configurator_cls, configuration):
    cmdline_options = configuration.copy()
    cmdline_options.update(Debug=True)
    configurator = configurator_cls(cmdline_options)
    assert configurator.get_cmdline_config() == configuration


def test_external_configuration_should_be_stored_second_in_cfg_list(configurator, configuration):
    mocked_open = mock_open(read_data=yaml.dump(configuration))
    with patch.object(builtins, 'open', mocked_open):
        configurator.process_config()
    assert configurator.cfg_list[1] == configuration


def test_cmdline_cfg_should_override_ext_file_cfg(configurator_cls):
    EXT_CFG = {'interval': 'aaa',
                    'user': 'aaa',
                    'passwd': 'aaa',
                    'parallel_downloads': 'aaa'}

    CMDL_CFG = {'interval': 'zzz',
                   'passwd': 'zzz',
                   'parallel_downloads': 'zzz'}

    configurator = configurator_cls(cmdline_options=CMDL_CFG)
    with patch.object(builtins, 'open', mock_open(read_data=yaml.dump(EXT_CFG))):
        cfg = configurator.process_config()
    assert cfg['interval']=='zzz'
    assert cfg['user']=='aaa'
    assert cfg['passwd']=='zzz'
    assert cfg['parallel_downloads']=='zzz'

def test_configurator_raises_bad_configuration_error_when_parameter_is_missing(configurator):
    from client.client import BadConfigurationError
    with patch.object(builtins, 'open', mock_open(read_data=yaml.dump({}))):
       with pytest.raises(BadConfigurationError):
            cfg = configurator.process_config()

# ------------ resources ------------


@pytest.fixture
def configuration():
    return {'interval': 'aaa',
            'user':   'aaa',
            'passwd': 'aaa',
            'parallel_downloads': 'aaa'}

@pytest.fixture
def configurable_parameters():
    return ['user', 'passwd', 'interval', 'parallel_downloads']

@pytest.fixture
def config_file_path():
    return './config.yaml'


@pytest.fixture
def configurator(configurator_cls):
    return configurator_cls(cmdline_options={})


@pytest.fixture
def configurator_cls():
    from client.client import Configurator
    return Configurator

