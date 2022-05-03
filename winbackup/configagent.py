#!/usr/bin/env python3

# This program is free software: you can redistribute it and / or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY
# without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see < https: // www.gnu.org/licenses/>.

import os
import re
import sys
import yaml
import logging
import traceback
from platform import uname
from . import __version__
from datetime import datetime

class ConfigAgent:
    def __init__(self, paths=None) -> None:
        """
        For generating, modifying and parsing configuration for WinBackup
        Base config generated at init and modified via cli or from config file
        call update_config_paths before get_config to correctly set folder paths.
        config files are loaded and saved to YAML
        """

        ### target_config is a dictionary with target_id as key config_item dictionary as value
        ###  config_item dictionary keys:
        # name - target name, will also be used to derive the output folder name
        # type - folder = single folder target, special = specific backup function (reqiring specific methods) 
        # path - backup target path
        # enabled - if the target will be backed up, default false for all
        # dict_size and mx_level - 7z dictionary size and compression level (See 7z cli docs for explanation)
        # full path - store the full path to the compressed files. Defaults to relative paths.
        self._base_config_item = {
            'name': None,
            'type': 'folder',
            'path': None,
            'enabled': False,
            'dict_size': '192m',
            'mx_level': 9,
            'full_path': False
        }

        self._base_target_config = {
        '01_config': {'name': 'System Config', 'type': 'special', 'path': None, 'enabled': False, 'dict_size': '192m', 'mx_level': 9, 'full_path': False},
        '10_documents': {'name': 'Documents', 'type': 'folder', 'path': None, 'enabled': False, 'dict_size': '192m', 'mx_level': 9, 'full_path': False},
        '11_desktop': {'name': 'Desktop', 'type': 'folder', 'path': None, 'enabled': False, 'dict_size': '192m', 'mx_level': 9, 'full_path': False},
        '12_pictures': {'name': 'Pictures', 'type': 'folder', 'path': None, 'enabled': False, 'dict_size': '32m', 'mx_level': 5, 'full_path': False},
        '13_downloads': {'name': 'Downloads', 'type': 'folder', 'path': None, 'enabled': False, 'dict_size': '192m', 'mx_level': 9, 'full_path': False},
        '14_videos': {'name': 'Videos', 'type': 'folder', 'path': None, 'enabled': False, 'dict_size': '32m', 'mx_level': 4, 'full_path': False},
        '15_music': {'name': 'Music', 'type': 'folder', 'path': None, 'enabled': False, 'dict_size': '32m', 'mx_level': 4, 'full_path': False},
        '16_saved_games': {'name': 'Saved Games', 'type': 'folder', 'path': None, 'enabled': False, 'dict_size': '192m', 'mx_level': 9, 'full_path': False},
        }

        self._base_global_config = {
            'encryption_enabled': False,
            'encryption_password' : '',
            'output_root_dir': '.',
        }

        self._global_config = {}
        self._target_config = {}
        if paths:
            self._target_config = self.update_config_paths(paths)
        

    def update_config_paths(self, paths:dict, config:dict=None) -> dict:
        """
        Base config does not have folder paths configured. Call with paths dictionary to update config.
        Parameters:
        - paths  : dict of folder paths. Keys = text component of target id.
        - config : target_config to be updated. class variable used if not specified.
        Returns:
        - config : updated target_config.
        
        """

        if not config:
            if not self._target_config:
                config = self._base_target_config
            else:
                config = self._target_config
        
        ## add the paths into config
        updated_config = config.copy()
        for id in config.keys():
            try:
                if updated_config[id]['type'].lower() == 'folder':
                    updated_config[id]['path'] = paths[id.split('_', 1)[1].lower()]
                    logging.debug(f"Path updated -> {id} is {paths[id.split('_', 1)[1].lower()]}")
            except KeyError:
                logging.error(f"Path not found for {id}")
            except Exception as e:
                logging.error(f"Misc error updating path for {id} , exception {e}")
                logging.debug(traceback.format_exc())
                raise

        ## save the config to class and return
        self._target_config = updated_config
        return updated_config


    def add_item(self, config_item_id:str, config_item:dict, config:dict=None) -> dict:
        """
        Add a backup row to the config file. Missing config items in config_item_id will be added with defaults.
        Parameters:
        - config_item_id : key of the item, acts as an id format 00_name
        - config_item    : dictionary of the config items. 
        - config         : target_config dictionary to be added to. If not specified uses class variable.  
        Returns:
        - config         : new config with added item
        """
        #basic item validation before adding to config
        if not type(config_item_id) == str:
            raise TypeError(f"config_item_id {config_item_id} not valid. Must be of type str, is of type {type(config_item_id)}")
        if not type(config_item) == dict:
            raise TypeError(f"config_item {config_item} not valid. Must be of type dict, is of type {type(config_item)}")
        for key in config_item:
            if key not in {'name', 'type', 'path', 'enabled', 'dict_size', 'mx_level', 'full_path'}:
                raise ValueError(f"Key {key} in config_item not permitted.")

        if not re.match('(\d{2}_[a-z_]+)', config_item_id):
            raise ValueError(f"Invalid config_item_id: {config_item_id}. must be in the format 00_name or 00_long_name")
    

        if config_item['name'] == None:
            raise ValueError("Name is required for config_item to be added to target_config")
        if config_item['type'] == 'folder':
            if config_item['path'] == None:
                raise ValueError("path is required for config_item with type folder to be added to target_config")
       
        if not config:
            if not self._target_config:
                config = self._base_target_config
            else:
                config = self._target_config

        new_config_item = self._base_config_item.copy()
        new_config_item.update(config_item)
        logging.debug(f"config_item argument - {config_item}")
        logging.debug(f"combined config item - {new_config_item}")

        try:
            config[config_item_id] = new_config_item
        except Exception as e:
            logging.error(f"Could not add config_item {config_item_id} to config, exception {e}")
            logging.debug(traceback.format_exc())
            raise

        # sort config again to maintain expected order.
        sorted_config = {k:v for k,v in sorted(config.items())}
        self._target_config = sorted_config
        return sorted_config


    def get_target_config(self) -> dict:
        """
        Returns a config dict to be used by the backup functions for targets.
        """
        if not self._target_config:
            logging.warning("Called before folder paths set. Base target_config used. Paths must be set before attempting backup.")
            self._target_config = self._base_target_config
        return self._target_config


    def set_target_config(self, new_target_config:dict) -> None:
        """
        if the target_config is set - update
        if not - create from supplied config
        """
        config = self._target_config
        config.update(new_target_config)
        self._target_config = config


    def get_global_config(self) -> dict:
        """
        Returns the global config dictionary.
        """
        if not self._target_config:
            logging.warning("Called before output dir set. Output defaults to pwd.")
            self._global_config = self._base_global_config

        return self._global_config


    def set_global_config(self, new_global_config:dict) -> None:
        """
        if the global_config is set - update
        if not - create from supplied config
        """
        config = self._global_config
        config.update(new_global_config)
        self._global_config = config


    def get_output_root_path(self) -> str:
        """
        Returns the output root path from the global config.
        If the global config is not set, it is initialized from the base config.
        """
        if not self._global_config:
            self._global_config = self._base_global_config
        return self._global_config['output_root_dir']
        

    def set_output_root_path(self, path:str) -> dict:
        """
        Set the output path in the global config.
        Returns the global config.
        """
        if not type(path) == str:
            raise TypeError("Path must be of type str")
        if not self._global_config:
            self._global_config = self._base_global_config
        
        self._global_config['output_root_dir'] = path

        return self._global_config

    
    def get_encryption_password(self) -> str:
        """
        Return the encryption password from the global config.
        If the global config is not set, it is initialized from the base config.
        """
        if not self._global_config:
            self._global_config = self._base_global_config
        return self._global_config['encryption_password']
        

    def set_encryption_password(self, password:str) -> dict:
        """
        Sets the encryption key in the global config.
        Returns the global config.
        """
        if not type(password) == str:
            raise TypeError("Password must be of type str")
        if not self._global_config:
            self._global_config = self._base_global_config
        
        self._global_config['encryption_password'] = password

        return self._global_config


    def validate_target_config(self, config:dict=None) -> bool:
        """
        Validate the supplied config dictionary.
        Returns true if the config is valid
        returns false or raises error if the config is not valid.
        """
        valid_config_flag = True

        if not config:
            config = self._target_config
            if not config:
                logging.error("Target config not set.")
                return False
        
        ## check id's match format 00_name 00_long_name
        for id in config:
            if not re.match('(\d{2}_[a-z_]+)', id):
                logging.warning(f"Invalid Target ID for {id}. must be in the format 00_name or 00_long_name")
                print(f"Invalid Target ID for {id}. must be in the format 00_name or 00_long_name")
                valid_config_flag = False
            
        for id, config_item in config.items():
            ## check config_items have valid keys and that all keys are present.
            valid_keys = {'name', 'type', 'path', 'enabled', 'dict_size', 'mx_level', 'full_path'}
            for key, value in config_item.items():
                if key not in valid_keys:
                    logging.warning(f"Unknown Key {key} in config_item for {id}. This will be ignored.")
                    print(f"Unknown Key {key} in config_item for {id}. This will be ignored.")
                if key in valid_keys:
                    valid_keys.remove(key)
                # check valid key types 
                valid_type = True
                if key in  {'name', 'type', 'dict_size'}:
                    if type(value) != str:
                        valid_type = False
                if key in {'enabled', 'full_path'}:
                    if type(value) != bool:
                        valid_type = False
                if key in {'mx_level'}:
                    if type(value) != int:
                        valid_type = False
                if key in {'path'} and config_item['type'] == 'folder':
                    if type(value) not in {str, list}:
                        valid_type = False 
                if not valid_type:
                        logging.error(f"Invalid type ({type(value)} for {key} in config_item for {id}.")
                        print(f"Invalid type ({type(value)} for {key} in config_item for {id}.")
                        valid_config_flag = False

            if len(valid_keys) != 0:
                logging.error(f"Required keys {valid_keys} not in config_item for {id}.")
                print(f"Required keys {valid_keys} not in config_item for {id}.") 
                valid_config_flag = False

            ## check mx_level within 0-9
            if 'mx_level' in config_item:
                if not 0 <= config_item['mx_level'] <= 9:
                    logging.error(f"mx_level {config_item['mx_level']} for {id} not valid. Must be in range 0-9.")
                    print(f"mx_level {config_item['mx_level']} for {id} not valid. Must be in range 0-9.") 
                    valid_config_flag = False
            ## check dict_size is valid
            if 'dict_size' in config_item:
                if not re.match('(^\d+[bkmg]?$)', config_item['dict_size']):
                    logging.error(f"dict_size {config_item['dict_size']} for {id} not valid. Must int followed by quantifier in bkmg")
                    print(f"dict_size {config_item['dict_size']} for {id} not valid. Must int followed by quantifier in bkmg") 
                    valid_config_flag = False
            ## check paths in target_config exist and are readable
            if 'path' in config_item and config_item['path'] != None:
                path_value = config_item['path']
                test_paths = []
                if type(path_value) == str:
                    test_paths.append(path_value)
                else:
                    test_paths = path_value
                ## As long as the path is a directory the backup will run. 
                # If the target is not readable (according to access flags) the backup will continue but will probably fail - warn user.
                for path in test_paths:
                    if os.path.exists(path):
                        if os.path.isdir(path):
                            if not os.access(path, os.R_OK):
                                logging.warning(f"Target directory {path} for {id} exists but is not readable. Check access permissions.")
                                print(f"Target directory {path} for {id} exists but is not readable. Check access permissions.") 
                        else:
                            logging.error(f"Target path {path} for {id} exists but is not a directory. Backup target must be a directory.")
                            print(f"Target path {path} for {id} exists but is not a directory. Backup target must be a directory.") 
                            valid_config_flag = False
                    else:
                        logging.error(f"Target path {path} does not exist but was specified for {id}. Check configuration.")
                        print(f"Target path {path} does not exist but was specified for {id}. Check configuration.") 
                        valid_config_flag = False

        return valid_config_flag


    def validate_global_config(self, global_config:dict=None) -> bool:
        """
        validate the supplied global config values
        """
        valid_config_flag = True
        if not global_config:
            global_config = self._global_config
            if not global_config:
                logging.error("Global config not set.")
                return False

        for key in global_config:
            valid_keys = {'encryption_password', 'output_root_dir', 'encryption_enabled'}
            required_keys = {'output_root_dir'}
            if key not in valid_keys:
                logging.warning(f"Unknown Key {key} in global config. This will be ignored.")
                print(f"Unknown Key {key} in global config. This will be ignored.")
            if key in required_keys:
                required_keys.remove(key)

        if len(required_keys) != 0:
            for key in valid_keys:
                logging.error(f"Required key {key} not in global config.")
                print(f"Required key {key} not in global config.") 
                valid_config_flag = False

        for key, value in global_config.items():
            valid_type = True
            if key in  {'encryption_password', 'output_root_dir'}:
                if type(value) != str:
                    valid_type = False

            if not valid_type:    
                logging.error(f"Invalid type ({type(value)} for {key} in config_item for {id}.")
                print(f"Invalid type ({type(value)} for {key} in config_item for {id}.")
                valid_config_flag = False
            
        if 'output_root_dir' in global_config:
            if os.path.isdir(global_config['output_root_dir']):
                if not os.access(global_config['output_root_dir'], os.W_OK):
                    logging.warning(f"Output directory {global_config['output_root_dir']} is not writeable. Check access permissions.")
                    print(f"Output directory {global_config['output_root_dir']} is not writeable. Check access permissions.") 
                    valid_config_flag = False
            else:
                logging.error(f"Output Directory path {global_config['output_root_dir']} does not exist. Check configuration.")
                print(f"Output Directory path {global_config['output_root_dir']} does not exist. Check configuration.") 
                valid_config_flag = False

        return valid_config_flag


    def save_YAML_config(self, path:str, target_config:dict=None, global_config:dict=None) -> str:
        """
        Saves a YAML config to the chosen path for modification and use. 
        Returns the path where the config was saved
        """
        if not target_config:
            target_config = self._target_config
            if not target_config:
                target_config = self._base_target_config
                logging.warning(f"Saved config template does not have correct user paths. It is recommended to update config paths first.")

        if not global_config:
            global_config = self._global_config
            if not global_config:
                global_config = self._base_global_config

        if os.path.isdir(path):
            raise IsADirectoryError("Path must be to a file, not a directory")
    
        if not path.endswith(('.yaml', '.yml')):
            raise ValueError("File type saved must be YAML")
        
        ## combine dictionaries
        combined_config = {
            'global': global_config,
            'backup_targets': target_config
        }

        with open(os.path.join(path), 'w', newline='\n') as fout:

            ## write comments to file with winbackup version and windows version
            fout.write(f"# WinBackup config file \n# WinBackup Version {__version__}\n")
            fout.write(f"# Config file created: {datetime.today().strftime('%Y-%m-%d')} ")
            fout.write(f"on {uname().system} {uname().version} - {uname().node}\n")

            try:
                yaml.safe_dump(combined_config, fout, sort_keys=False, indent=2)
            except Exception as e:
                logging.error(f"could not dump configuration to yaml, exception {e}")
                            
        return path


    def parse_YAML_config_file(self, path:str) -> tuple[dict, dict]:
        """
        Parse the YAML config from file and return as a tuple of dictionaries (global, target)
        config file is also saved within class instance as self.config
        Validates config after loading - raises ValueError if config invalid.
        """
        ##load config
        with open(path, 'r') as fin:
            config = yaml.safe_load(fin)
        
        loaded_global_config = config['global']
        loaded_target_config = config['backup_targets']

        merged_global_config = self._base_global_config.copy()
        merged_global_config.update(loaded_global_config)
        if len(merged_global_config['encryption_password']) != 0:
            logging.debug(f'Encryption password from configfile is not empty, enable encryption')
            merged_global_config['encryption_enabled'] = True
        if not self.validate_global_config(loaded_global_config):
            raise ValueError(f"Invalid global config loaded from {path}")
        if not self.validate_target_config(loaded_target_config):
            raise ValueError(f"Invalid target config loaded from {path}")


        self._global_config = merged_global_config
        self._target_config = loaded_target_config

        return merged_global_config, loaded_target_config 


    encryption_password = property(get_encryption_password, set_encryption_password)
    output_root_dir = property(get_output_root_path, set_output_root_path)
    target_config = property(get_target_config, set_target_config)
    global_config = property(get_global_config, set_global_config)


if __name__ == "__main__":
    logging.basicConfig(stream= sys.stdout,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    level = logging.DEBUG)
    tmp_dir = os.path.join('.', 'tmp')
    if not os.path.exists(tmp_dir):
        os.mkdir(tmp_dir)
    import windowspaths
    win_paths = windowspaths.WindowsPaths()
    config_agent = ConfigAgent()
    config_agent.set_encryption_password('test')
    print(config_agent.output_root_dir)
    config_agent.update_config_paths(win_paths.get_paths())
    config_agent.save_YAML_config('./tmp/config.yaml')
    config_agent.parse_YAML_config_file('./tmp/config.yaml')

    sys.exit()