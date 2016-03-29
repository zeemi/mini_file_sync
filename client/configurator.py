__author__ = 'zeemi'
import yaml

class Configurator:
    '''
    class responsible for saving configuration. Parameters passed with cmdline can override external file config.
    information defined here:
    - filepath to config file
    - list of configurable parameters
    '''

    def __init__(self):
        self.config_file_path = './config.yaml'
        self.cfg_list = []
        self.configurable_parameters = ['user',
                                        'passwd',
                                        'interval',
                                        'parallel_downloads',
                                        'server_address']

    def store_cmdline_options(self, cmdline_options):
        self.cmdline_options = cmdline_options

    def get_external_config(self):
        with open(self.config_file_path) as fh:
            return yaml.load(fh.read())

    def get_cmdline_config(self):
        return {k: v for k, v in self.cmdline_options.items() if k in self.configurable_parameters}

    def process_config(self, cmdline_options):
        self.store_cmdline_options(cmdline_options)
        self.cfg_list.append(self.get_cmdline_config())
        self.cfg_list.append(self.get_external_config())
        return self.eval_cfg()

    def eval_cfg(self):
        '''
        Method evaluate configuration based on position in self.cfg_list. Lower position means higher priority
        :return: final configuration
        '''
        result = {}
        for param in self.configurable_parameters:
            for config in self.cfg_list:
                if param in config:
                    result[param] = config[param]
                    break
            else:
                raise BadConfigurationError
        return result

class BadConfigurationError(Exception):
    pass
