#
##
###########################################################################################
#                                                                                         #
#       file_handler                                                                      #
#                                                                                         #
#       (c) Vamegh Hedayati                                                               #
#                                                                                         #
#       Please see https://github.com/vamegh/pylibs                                       #
#                  https://github.com/vamegh/gauth/blob/master/gauth_libs/file_handler.py #
#                    for License Information                                              #
#                             GNU/LGPL                                                    #
###########################################################################################
##
#
#  file_handler - Handles most I/O file based operations

import json
import logging
import os
import sys
from shutil import copy2

try:
    from ruamel import yaml
except:
    import yaml


class FileHandler(object):
    def __init__(self):
        self.config_file = ''
        self.data = ''
        self.yaml_types = ["yaml", "yml", "yl"]
        self.json_types = ["json", "jsn", "js", "jn"]
        self.prop_types = ["bash", "properties", "property", "prop", "sh"]

    @staticmethod
    def file_exists(path):
        return os.path.isfile(path)

    @staticmethod
    def dir_exists(path):
        return os.path.isdir(path)

    def check_file_type(self, file_type=None):
        if file_type:
            file_type = file_type.lower()

        if not file_type:
            try:
                file_type = self.config_file.split('.')[-1].lower()
            except (TypeError, AttributeError, IOError, KeyError) as err:
                logging.warning("Cannot properly determine file Extension: Error: %s", str(err))
                print("Cannot properly determine file Extension: Error: %s", str(err))
        return file_type

    def copy_file(self, source=None, dest=None):
        self.make_dir(path=dest)
        if source and dest:
            copy2(source, dest, follow_symlinks=True)

    def make_dir(self, path=None):
        file_path, file_name = os.path.split(path)

        if file_path:
            if not self.dir_exists(file_path):
                logging.info("Creating Directory: %s", file_path)
                os.makedirs(file_path)

    def read_yaml(self, file_type=None):
        file_type = self.check_file_type(file_type=file_type)

        if file_type not in self.yaml_types:
            if file_type not in self.json_types:
                return False

        try:
            with open(self.config_file, "r") as config:
                yaml_data = yaml.safe_load(config)
            logging.debug("Returning yaml_data: %s", yaml_data)
            return yaml_data
        except (TypeError, IOError) as err:
            print("Skipping Yaml Import for: {}".format(self.config_file))
            pass
        return False

    def read_json(self, file_type=None):
        file_type = self.check_file_type(file_type=file_type)

        if file_type not in self.json_types:
            return False

        try:
            with open(self.config_file, "r") as config:
                json_data = json.loads(config)
            logging.debug("Returning json_data: %s", json_data)
            return json_data
        except (TypeError, IOError) as err:
            print("Skipping Json Import For: {}".format(self.config_file))
            pass
        return False

    def read_properties(self, file_type=None):
        file_type = self.check_file_type(file_type=file_type)

        if file_type not in self.prop_types:
            return False

        data = {}
        values = []
        try:
            with open(self.config_file, "r") as config:
                for line in config:
                    if line.startswith('#'):
                        continue
                    if len(line.strip()) == 0:
                        continue
                    if line.startswith('export'):
                        line = line.split(' ', 1)[1]
                    line = line.split('#', 1)[0]
                    line = line.rstrip()
                    values = line.split("=")
                    if len(values) > 2:
                        key = values.pop(0)
                        value = '='.join(values)
                    elif len(values) == 2:
                        key, value = line.split("=")
                    else:
                        print("I cannot parse the following line: {}, from file: {} :: Skipping it".format(line,
                                                                                                           self.config_file))
                        continue
                    if key.startswith('\'') and key.endswith('\''):
                        key = key[1:]
                        key = key[:-1]
                    if key.startswith('\"') and key.endswith('\"'):
                        key = key[1:]
                        key = key[:-1]
                    if value.startswith('\'') and value.endswith('\''):
                        value = value[1:]
                        value = value[:-1]
                    if value.startswith('\"') and value.endswith('\"'):
                        value = value[1:]
                        value = value[:-1]
                    data[key] = value
            return data
        except (TypeError, IOError) as err:
            pass
        return False

    def read_file(self, config_file=None, file_type=None):
        self.config_file = config_file
        file_type = self.check_file_type(file_type=file_type)
        config_data = self.read_yaml(file_type=file_type)
        if not config_data:
            config_data = self.read_json(file_type=file_type)
        if not config_data:
            config_data = self.read_properties(file_type=file_type)
        if not config_data:
            logging.warning("File appears to be empty, returning Null value")
            return None
            # raise ValueError("Error Cannot Read Config File: {} ... Aborting".format(config_file))
        return config_data

    def read_std_file(self, file_name=None):
        if not file_name:
            return None
        with open(file_name, "r") as data:
            file_data = data.readlines()
        return file_data

    def write_yaml(self, output_file=None, data=None):
        if not output_file or not data:
            logging.error("Error Data / Output File Not Provided")
            sys.exit(1)
        self.make_dir(path=output_file)
        with open(output_file, 'w') as output_file:
            output_file.write(yaml.safe_dump(data, default_flow_style=False,
                                             allow_unicode=True, encoding=None,
                                             explicit_start=True))

    def write_json(self, output_file=None, data=None):
        logging.debug(f'Creating: {output_file}')
        if not output_file:
            logging.error("Error Output File Not Provided")
            sys.exit(1)
        if data is None:
            logging.error("Error Data Not Provided")
            sys.exit(1)
        self.make_dir(path=output_file)
        # making sure all objects are json serialized - converting
        # anything not json compliant into a string - so we can then write
        # it out into a json config file.
        data = json.loads(json.dumps(data, default=str))
        with open(output_file, 'w') as output_file:
            json.dump(data, output_file, indent=4)

    def write_tf_properties(self, output_file=None, data=None):
        if not output_file or not data:
            logging.error("Error Data / Output File Not Provided")
            sys.exit(1)
        self.make_dir(path=output_file)
        with open(output_file, 'w') as output_file:
            for key, value in data.items():
                output_file.write("%s = %s\n" % (key, value))

    def write_properties(self, output_file=None, data=None):
        if not output_file or not data:
            logging.error("Error Data / Output File Not Provided")
            sys.exit(1)
        self.make_dir(path=output_file)
        with open(output_file, 'w') as output_file:
            for key, value in data.items():
                output_file.write("%s=%s\n" % (key, value))

    def write_quoted_properties(self, output_file=None, data=None):
        if not output_file or not data:
            logging.error("Error Data / Output File Not Provided")
            sys.exit(1)
        self.make_dir(path=output_file)
        with open(output_file, 'w') as output_file:
            for key, value in data.items():
                output_file.write("%s=\"%s\"\n" % (key, value))

    def write_env(self, output_file=None, data=None, options=None):
        if not output_file or not data:
            logging.error("Error Data / Output File Not Provided")
            sys.exit(1)
        self.make_dir(path=output_file)
        with open(output_file, 'w') as output_file:
            for key, value in data.items():
                if options.prefix:
                    key = '_'.join([options.prefix, key])
                if options.export:
                    output_file.write(f'export {key.upper()}="{value}"\n')
                else:
                    output_file.write(f'{key.upper()}={value}\n')

    def write_file(self, output_file=None, data=None, status=None, mode="w"):
        if not output_file or not data:
            logging.error("Error Data / Output File Not Provided")
            sys.exit(1)
        self.make_dir(path=output_file)
        with open(output_file, mode) as output_file:
            if isinstance(data, list):
                for value in data:
                    if status == "enable":
                        output_file.write("+%s\n" % (value))
                    elif status == "disable":
                        output_file.write("-%s\n" % (value))
                    else:
                        output_file.write("%s\n" % (value))
            else:
                output_file.write("%s\n" % (data))

