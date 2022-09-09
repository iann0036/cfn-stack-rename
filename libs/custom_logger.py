#
##
############################################################################################
#                                                                                          #
#       custom_logger                                                                      #
#                                                                                          #
#       (c) Vamegh Hedayati                                                                #
#                                                                                          #
#       Please see https://github.com/vamegh/pylibs                                        #
#                  https://github.com/vamegh/gauth/blob/master/gauth_libs/custom_logger.py #
#                    for License Information                                               #
#                             GNU/LGPL                                                     #
############################################################################################
##
#
#  custom_logger - This adds custom formatting & colour output to the inbuilt python logging module

import logging, sys, os
import yaml
from datetime import datetime


def read_yaml(config_file):
    try:
        with open(config_file, "r") as config:
            yaml_data = yaml.safe_load(config)
        return yaml_data
    except (TypeError, IOError) as err:
        print("Skipping Yaml Import for: {}".format(config_file))
        pass
    return False


def color_map(color='', c_map={}):
    '''This is the colour map -- used to generate the various different colours,
       this can be moved to config files later.'''
    color_map = {
        'black': '\033[0;30m',
        'blue': '\033[0;34m',
        'cyan': '\033[0;36m',
        'green': '\033[0;32m',
        'grey': '\033[0;37m',
        'red': '\033[0;4;31m',
        'wht_red': '\033[0;4;47;31m',
        'lgt_red': '\033[1;31m',
        'wht_lgt_red': '\033[1;4;47;31m',
        'yellow': '\033[1;33m',
        'blk_ylw': '\033[1;4;40;33m',
        'drk_grey': '\033[1;30m',
        'white': '\033[1;37m',
        'reset': '\033[0m',
        'debug': 'drk_grey',
        'info': 'blue',
        'warning': 'yellow',
        'error': 'lgt_red',
        'critical': 'red',
        'lvl_debug': 'grey',
        'lvl_info': 'green',
        'lvl_warning': 'blk_ylw',
        'lvl_error': 'wht_red',
        'lvl_critical': 'wht_lgt_red',
    }
    if c_map:
        try:
            # requested_color = c_map[color].encode('ascii')
            requested_color = c_map[color]
            try:
                requested_color = c_map[requested_color]
            except:
                ''' this aint a recursive lookup '''
            return requested_color
        except:
            ''' We dont really care, we just want to catch the exception, if it fails
                it defaults back to the built-in color map ...
                print ("requested colour not in custom colour map defaulting to built-in")'''
    requested_color = color_map[color]
    try:
        requested_color = color_map[requested_color]
    except:
        ''' this aint a recursive lookup '''
    return requested_color


class LevelFilter(logging.Filter):
    '''
      levels are not properly being propagated to log file - this is the solution
    '''

    def __init__(self, level):
        self.level = level

    def filter(self, record):
        return record.levelno >= self.level


class CustomLog(logging.Formatter):
    '''This colours key elements from the logger, ie any element from the record'''

    def __init__(self, name='', config=None, *args, **kwargs):
        self.config = config
        self.name = name
        self.logger = ''
        try:
            self.color = config['color_map']
        except:
            self.color = ''
        try:
            self.logging_config = config['logging_config']
        except:
            self.logging_config = ''

        self._colors = {logging.DEBUG: color_map('debug', c_map=self.color),
                        logging.INFO: color_map('info', c_map=self.color),
                        logging.WARNING: color_map('warning', c_map=self.color),
                        logging.ERROR: color_map('error', c_map=self.color),
                        logging.CRITICAL: color_map('critical', c_map=self.color)}
        self._levels = {logging.DEBUG: color_map('lvl_debug', c_map=self.color),
                        logging.INFO: color_map('lvl_info', c_map=self.color),
                        logging.WARNING: color_map('lvl_warning', c_map=self.color),
                        logging.ERROR: color_map('lvl_error', c_map=self.color),
                        logging.CRITICAL: color_map('lvl_critical', c_map=self.color)}
        super(CustomLog, self).__init__(*args, **kwargs)

    def format(self, record):
        if self.config == 'disable_color':
            if self.name:
                record.levelname = self.name + " :: " + record.levelname
            return logging.Formatter.format(self, record)
        elif sys.stdout.isatty():
            record.msg = self._colors[record.levelno] + record.msg + color_map('reset')
            record.levelname = self._levels[record.levelno] + record.levelname + color_map('reset')
            return logging.Formatter.format(self, record)
        else:
            if self.name:
                record.levelname = self.name + " :: " + record.levelname
            return logging.Formatter.format(self, record)

    def exportLog(self, name=''):
        '''ColourLog method with no extra requirements - when we initialise the class we provide the config
           useful if we need to get access to the logger object, without having to pass configs through to this'''
        ## This makes the colourLog method completely redundant and that will be removed in due course.

        loglevel = 'INFO'
        self.logger = logging.getLogger()

        if not name:
            name = self.name
        if self.logging_config:
            try:
                loglevel = self.logging_config['log_level']
                loglevel = str.upper(self.loglevel)
            except:
                ''' loglevel defaults to INFO .. '''
            try:
                logfile = self.logging_config['log_file']
                log_path, log_file = os.path.split(logfile)
                time_stamp = datetime.utcnow().strftime("%Y-%m-%d_%H.%M")
                log_file = time_stamp + '_' + name + '_' + log_file
                logfile = os.path.join(log_path, log_file)
                if not os.path.exists(log_path):
                    os.makedirs(log_path)
                try:
                    file_handler = logging.FileHandler(logfile)
                    file_handler.setLevel(loglevel)
                    file_style = CustomLog(name,
                                           'disable_color',
                                           '%(pathname)s - %(funcName)s - line:%(lineno)d :: %(asctime)s :: %(levelname)s :: %(message)s')
                    file_handler.setFormatter(file_style)
                    self.logger.addHandler(file_handler)
                except:
                    ''' we dont really care, -- just skip the logging file method entirely'''
                    print("Unexpected error:", sys.exc_info()[0])
                    print("skipping log file ...")
            except:
                ''' probably log_file key doesnt exist ... '''
                ''' its fine we ignore this if log_file isnt defined. '''
                print("Unexpected error:", sys.exc_info()[0])
                print("skipping log file ...")

        self.logger.setLevel(loglevel)
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(loglevel)
        stream_style = CustomLog(name, config, '%(asctime)s - %(module)s - %(levelname)s - %(message)s')
        stream_handler.setFormatter(stream_style)
        self.logger.addHandler(stream_handler)
        return self.logger

    def colourLog(self, name='', config=None):
        '''ColourLog method'''
        ''' this is exactly the same as colourLog function below -- except its a class method - both methods work '''

        custom_color_map = config['color_map']
        logging_config = config['logging_config']
        self.logger = logging.getLogger()

        if logging_config:
            try:
                loglevel = logging_config['log_level']
                loglevel = str.upper(self.loglevel)
            except:
                ''' loglevel defaults to INFO .. '''
                loglevel = 'INFO'
            try:
                logfile_level = logging_config['log_file_level']
                logfile_level = str.upper(logfile_level)
            except:
                ''' logfile_level defaults to DEBUG .. '''
                logfile_level = 'DEBUG'
            try:
                logfile = logging_config['log_file']
                log_path, log_file = os.path.split(logfile)
                time_stamp = datetime.utcnow().strftime("%Y-%m-%d_%H.%M")
                log_file = time_stamp + '_' + name + '_' + log_file
                logfile = os.path.join(log_path, log_file)
                if not os.path.exists(log_path):
                    os.makedirs(log_path)
                try:
                    file_handler = logging.FileHandler(logfile)
                    file_style = CustomLog(name,
                                           'disable_color',
                                           '%(pathname)s - %(funcName)s - line:%(lineno)d :: %(asctime)s :: %(levelname)s :: %(message)s')
                    file_handler.setFormatter(file_style)
                    # file_handler.addFilter(LevelFilter(logfile_level))
                    file_handler.setLevel(logfile_level)
                    self.logger.addHandler(file_handler)
                except:
                    ''' we dont really care, -- just skip the logging file method entirely'''
                    print("Unexpected error:", sys.exc_info()[0])
                    print("skipping log file ...")
            except:
                ''' probably log_file key doesnt exist ... '''
                ''' its fine we ignore this if log_file isnt defined. '''
                print("Unexpected error:", sys.exc_info()[0])
                print("skipping log file ...")

        self.logger.setLevel(loglevel)
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(loglevel)
        stream_style = CustomLog(name, config, '%(asctime)s - %(module)s - %(levelname)s - %(message)s')
        stream_handler.setFormatter(stream_style)
        self.logger.addHandler(stream_handler)
        return self.logger

    def __del__(self):
        '''print "CustomLog Closed ..."'''


def colourLog(name='', config=None, config_file=None):
    """Call this to initiate CustomLog"""

    if config_file:
        config = read_yaml(config_file)

    loglevel = 'INFO'
    try:
        custom_color_map = config['color_map']
    except (TypeError, KeyError):
        pass
    try:
        logging_config = config['logging_config']
    except (TypeError, KeyError):
        logging_config = None

    ## pushing directly to root logger, ideally we would want to log
    ## per function / class call but that is just too much code to modify for now
    logger = logging.getLogger()
    if logging_config:
        try:
            loglevel = logging_config['log_level']
            loglevel = str.upper(loglevel)
        except (KeyError, ValueError, AttributeError):
            loglevel = 'INFO'

        try:
            logfile_level = logging_config['log_file_level']
            logfile_level = str.upper(logfile_level)
        except (KeyError, ValueError, AttributeError):
            logfile_level = 'DEBUG'

        try:
            logfile = logging_config['log_file']
            log_path, log_file = os.path.split(logfile)
            time_stamp = datetime.utcnow().strftime("%Y-%m-%d_%H.%M")
            logfile = time_stamp + '_' + name + '_' + log_file
            if log_path:
                logfile = os.path.join(log_path, logfile)
            print("Logging to: {}".format(logfile))
        except (KeyError, ValueError, AttributeError):
            ''' probably log_file key is missing '''
            print("skipping log file ...")

        try:
            if log_path:
                if not os.path.exists(log_path):
                    os.makedirs(log_path)
        except (OSError):
            # its fine we can ignore this . '''
            print("Please Make sure you have write access to: %s :: skipping log path creation..." % log_path)

        try:
            file_handler = logging.FileHandler(logfile)
            file_style = CustomLog(name,
                                   'disable_color',
                                   '%(pathname)s - %(funcName)s - line:%(lineno)d :: %(asctime)s :: %(levelname)s :: %(message)s')
            file_handler.setFormatter(file_style)
            # file_handler.addFilter(LevelFilter(logfile_level))
            file_handler.setLevel(logfile_level)
            logger.addHandler(file_handler)
        except:
            # just skip the logging file method entirely
            pass

    logger.setLevel(loglevel)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(loglevel)
    stream_style = CustomLog(name, config, '%(asctime)s - %(module)s - %(levelname)s - %(message)s')
    stream_handler.setFormatter(stream_style)
    logger.addHandler(stream_handler)
    return logger
