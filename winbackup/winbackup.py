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
import sys
import signal
import shutil
import logging
import ctypes
import getpass
import hashlib
import subprocess
import traceback
from io import StringIO
from datetime import datetime
from send2trash import send2trash
from colorama import Fore, Back, Style, init
from pathlib import Path
import humanize

from . import systemconfigsaver
from . import zip7archiver
from . import windowspaths
from . import configagent
from . import __version__

init(autoreset=False)

class WinBackup:
    def __init__(self, log_level) -> None:
        """
        Backup windows files to 7z archives
        """
        self.archiver = zip7archiver.Zip7Archiver()
        self.config_saver = systemconfigsaver.SystemConfigSaver()
        self.windows_paths = windowspaths.WindowsPaths()
        self.config_agent = configagent.ConfigAgent()

        self.log_buffer = StringIO()
        self.log_level = log_level
        self.logger_tempfile = self._start_logger(log_level)   
    
        self.paths = self.windows_paths.get_paths()
        self.config_agent.update_config_paths(self.paths)
        self.config_agent.encryption_password = ''
        self.start_time = datetime.now()
        self.hyperv_paths_script = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'scripts', 'hyperv_paths.ps1')

        self.config_saver.set_videos_directory_path(self.config_agent._target_config['14_videos']['path'])

        ## ** Plex Specific setup
        plex_config_item = {
            'name': 'Plex Server', 
            'type': 'special', 
            'path': os.path.join(self.paths['local_appdata'], 'Plex Media Server'), 
        }
        if os.path.exists(os.path.join(self.paths['local_appdata'], 'Plex Media Server')):
            logging.debug('Plex item added to config')
            self.config_agent.add_item('30_plexserver', plex_config_item)

        ## ** virtualbox specific setup
        virtualbox_config_item = {
            'name': 'VirtualBox VMs', 
            'path': os.path.join(os.path.expanduser('~'), 'VirtualBox VMs'), 
            'dict_size': '128m', 
        }
        if os.path.exists(os.path.join(os.path.expanduser('~'), 'VirtualBox VMs')):
            logging.debug('VirtualboxVMs item added to config')
            self.config_agent.add_item('31_virtualboxvms', virtualbox_config_item)

        ## ** HyperV specific setup
        hyperv_config_item = {
            'name': 'HyperV VMs', 
            'type': 'folder', 
            'path': None, 
            'dict_size': '128m', 
            'full_path': True
        }
        if self.check_if_admin() and self._hyperv_possible():
            logging.debug('HyperV item added to config')
            hyperv_config_item['path'] = self._get_hyperv_paths()
            self.config_agent.add_item('32_hypervvms', hyperv_config_item)
 
        ## ** onenote specific setup
        ## 33_onenote
        ## default compression settings, to be implemented 

    @staticmethod
    def _command_runner(shell_commands:list) -> str:
        logging.debug(f'Command runner cmds: {shell_commands}')
        return subprocess.run(shell_commands, stdout=subprocess.PIPE).stdout.decode('utf-8', errors='ignore')


    def _ctrl_c_handler(self, signum, frame):
        print()
        print(Fore.RED + " Ctrl-C received - Exiting." + Style.RESET_ALL)
        sys.exit(1)        


    def cli_get_output_root_path(self) -> str:
        """
        check the first argument is a real path, if not exit
        if is a path - return path
        """
        loop_limit = 5
        while (1):
            print(Fore.GREEN + 
                " Backup output directory: " + Style.RESET_ALL, end='')
            reply = str(input()).strip()
            logging.debug(f"Path reply {reply}")
            if os.path.isdir(reply):
                path = os.path.abspath(reply)
                break
            else:    
                print(Fore.RED + " Output directory must be a real path. Ctrl+C to exit." + Style.RESET_ALL)
                loop_limit -= 1
                logging.debug(f"loop limit = {loop_limit}")
            if loop_limit <= 0:
                print(Fore.RED + " ERROR - Too many incorrect attempts. Exiting" + Style.RESET_ALL)
                sys.exit(1)
        logging.debug(f"CLI path given: {path}")
        return path



    def _start_logger(self, log_level) -> None:
        """
        if log level is debug, write logger to file in pwd unless a backup is run, then move file to backup output dir    
        if log level is info or above, write logger to buffer and flush to disk in backup output dir when backup is run.
        """

        #get the root logger
        logger = logging.getLogger()
        logger.setLevel(log_level)


        if log_level == logging.DEBUG:
            log_format = "%(asctime)s - %(levelname)s [%(module)s:%(funcName)s:%(lineno)d] -> %(message)s"
            log_handler = logging.FileHandler(os.path.join(os.getcwd(), 'winbackup.log'),
                                                mode='w',
                                                encoding='utf-8')
        else:
            log_format = "%(asctime)s - %(levelname)s -> %(message)s"
            log_handler = logging.StreamHandler(self.log_buffer)

        formatter = logging.Formatter(log_format)
        log_handler.setFormatter(formatter)
        logger.addHandler(log_handler)
        logging.debug("Log Handler Started")


    def _redirect_logger(self, out_path, log_level) -> None:
        logging.debug("Log Handler Redirect Started")
        logger = logging.getLogger()
        
        # remove root log handlers
        for handler in logger.handlers:
            logger.removeHandler(handler)
            handler.close()
        
        logger.setLevel(log_level)
        if log_level == logging.DEBUG:
            # move temp log in cwd to output path
            shutil.move(os.path.join(os.getcwd(), 'winbackup.log'), 
                        os.path.join(out_path, 'winbackup.log'))
            # create new handler to append to the new log location
            log_format = "%(asctime)s - %(levelname)s [%(module)s:%(funcName)s:%(lineno)d] -> %(message)s"
        else:
            # write the log buffer to disk and close the buffer
            with open(os.path.join(out_path, 'winbackup.log'), 'w', encoding='utf-8') as fout:
                self.log_buffer.seek(0)
                shutil.copyfileobj(self.log_buffer, fout)
                self.log_buffer.close()
            log_format = "%(asctime)s - %(levelname)s -> %(message)s"
                               
        # create new handler to append the rest of the log in the output dir
        log_handler = logging.FileHandler(os.path.join(out_path, 'winbackup.log'),
                                mode='a',
                                encoding='utf-8')
        formatter = logging.Formatter(log_format)
        log_handler.setFormatter(formatter)
        logger.addHandler(log_handler)
        logging.debug(f"Log Handler Redirected to: {os.path.join(out_path, 'winbackup.log')}")


    def _hyperv_possible(self) -> bool:
        """
        the vmcompute service is required by hyper-v, so check if it exists.
        """
        response = self._command_runner(['powershell.exe', 'Get-Service', 'vmcompute']).split('\r\n')[0]
        if "Cannot find any service with service name" in response:
            return False
        else:
            return True


    def _onenote_possible(self) -> bool:
        #placeholder
        return False


    def _plex_server_running(self) -> bool:
        response = self._command_runner(['powershell.exe', 'Get-Process', '"Plex Media Server"']).split('\r\n')[0]
        if "Cannot find a process with the name" in response:
            return False
        else:
            return True


    def _get_hyperv_paths(self) -> list:
        """
        Needs to be run as admin
        """
        response = self._command_runner(['powershell.exe', self.hyperv_paths_script]).split('\r\n')
        paths = list(filter(None, response))
        if 'is not recognized as a name of a cmdlet' in paths[0]:
            logging.error('HyperV not installed')
        elif 'You do not have the required permission' in paths[0]:
            logging.error('HyperV tools need to be run as admin.')
            raise PermissionError("HyperV needs to be run as admin")
        else:
            logging.debug(f"HyperV Paths: {paths}")
        return paths


    @staticmethod
    def check_if_admin() -> bool:
        """
        Returns if the program is executed with admin privileges. 
        """
        try:
            is_admin = bool(ctypes.windll.shell32.IsUserAnAdmin() != 0)
        except:
            is_admin = False
        return is_admin


    @staticmethod
    def _yes_no_prompt(question:str) -> bool:
        while (1):
            print(Fore.GREEN + " > " + question + " (y/n): " + Style.RESET_ALL, end='')
            reply = str(input()).lower().strip()
            if reply in {'yes', 'ye', 'y'}:
                return True
            elif reply in {'no', 'n'}:
                return False
            else:
                print(Fore.RED + " Only yes or no permitted. Ctrl+C to exit." + Style.RESET_ALL)


    @staticmethod
    def _create_filename(output_dir_name:str) -> str:
        pcname = os.environ['COMPUTERNAME']
        uname = getpass.getuser()
        date_str = datetime.now().strftime("%Y-%m-%d")
        return f'{pcname}_{uname}_{date_str}_{output_dir_name}.7z'


    @staticmethod
    def _create_output_directory(output_dir:str) -> tuple:
        """
        takes the tgt output dir and creates an output path
        returns the path and folder_name and a flag indicating if the path needed created.
        """
        path_created = False
        pcname = os.environ['COMPUTERNAME']
        uname = getpass.getuser()
        date_str = datetime.now().strftime("%Y-%m-%d")
        output_folder_name = f'{pcname}_{uname}_{date_str}'
        output_path = os.path.join(output_dir, output_folder_name)

        if not os.path.exists(output_path):
            os.mkdir(output_path)
            path_created = True

        return output_path, output_folder_name, path_created


    @staticmethod
    def _save_file_hashes(out_path:str) -> None:
        hashes_list = []
        for file in os.listdir(out_path):
            if not file.endswith('.log') and not file.endswith('.txt'):
                h = hashlib.sha256()
                b = bytearray(128*1024)
                mv = memoryview(b)
                with open(os.path.join(out_path, file), 'rb', buffering=0) as f:
                    for n in iter(lambda: f.readinto(mv), 0):
                        h.update(mv[:n])
                hashes_list.append((file, h.hexdigest()))
                logging.debug(f" Hash {file} {h.hexdigest()}")
        with open(os.path.join(out_path, 'sha256.txt'), 'w') as hash_file:
            for item in hashes_list:
                hash_file.write(f'{item[0]} {item[1]}\n')


    def _recursive_loop_check(self, target_path:str, config:dict) -> bool:
        """
        Returns True if the output directory is a child of a backup directory.
        """
        backup_dirs = []
        for key, target in config.items():
            if target['enabled']:               
                if type(target['path']) == str:
                    backup_dirs.append(target['path'])
                elif type(target['path']) == list:
                    backup_dirs += target['path']

        for path in backup_dirs:
            if Path(path) in Path(target_path).parents:
                return True
        return False


    def cli_header(self, output_path:str, output_folder_name:str, start_time:datetime) -> None:
        print(Fore.BLACK + Back.WHITE + " WINDOWS BACKUP - v" + __version__ + " " + Style.RESET_ALL)
        print(Fore.GREEN + f" Backup started at     : " + Style.RESET_ALL + f" {start_time.strftime('%Y-%m-%d %H:%M')}")
        print(Fore.GREEN + f" Output filename style : " + Style.RESET_ALL + f" {self._create_filename('example')}")
        print(Fore.GREEN + f" Output folder         : " + Style.RESET_ALL + f" {output_path}")
        print(Fore.GREEN + f" Archives folder name  : " + Style.RESET_ALL + f" {output_folder_name}")
        print()
        print(" A new folder will be created in the specified output folder with the above archive folder name pattern.")
        print(" All produced archives and files will be placed in this new folder.")
        print()


    def cli_config(self, config:dict) -> dict:
        new_config = config.copy()
        for key, target in sorted(config.items()):
            new_config[key]['enabled'] = self._yes_no_prompt(f"Backup {target['name']}?")
        print()
        return new_config


    def cli_get_password(self) -> str:
        passwd = ''
        while(1):
            print(Fore.GREEN + f" > Password for encryption (leave blank to disable) : " + Style.RESET_ALL, end='')
            passwd = getpass.getpass(prompt='')
            if len(passwd) == 0:
                print(" No password provided. 7z files produced will not be encrypted.")
                break
            else:
                print(Fore.GREEN + f" > Confirm encryption password: " + Style.RESET_ALL, end='')
                passwd_confirm = getpass.getpass(prompt='')
                if passwd == passwd_confirm:
                    logging.info("Archives will be encrypted.")
                    print(f" Passwords match. 7z archives will be AES256 encrypted with the given password.")
                    print(f" The archive headers will be encrypted (Filenames will be encrypted).")
                    break
                else:
                    print(Fore.RED + f" > passwords don't match - try again. " + Style.RESET_ALL)
        print()
        return passwd
    

    def cli_config_summary(self, config:dict, passwd:str, path_created:bool) -> None:
        print(Fore.BLACK + Back.WHITE + " ** CONFIG SUMMARY ** " + Style.RESET_ALL + Fore.GREEN)
        for key, target in sorted(config.items()):
            print(f" Backup {target['name']:<14} - {'Yes' if target['enabled']==True else 'No'}")
            logging.info(f"Config > {target['name']} - {target['enabled']}")
        print(f" Encryption            - {'No' if len(passwd)==0 else 'Yes'}")
        print(Style.RESET_ALL)
    
        if len(passwd) <= 12 and len(passwd)!= 0:
            print(Fore.YELLOW + f" !! CAUTION - The given password is short. Consider a longer password." + Style.RESET_ALL)
            logging.debug(f"The given password is short ({len(passwd)} chars). Consider a longer password.")
        if not path_created:
            print(Fore.YELLOW + " !! CAUTION - Output directory already exists - Contents may be destroyed if you proceed." + Style.RESET_ALL)
            logging.info(f"Output directory already exists - Contents may be destroyed if you proceed.")
        if '30_plexserver' in config:
            if config['30_plexserver']['enabled'] and self._plex_server_running():
                print(Fore.YELLOW + " !! CAUTION - Plex Media Server is running - Recommend stopping Plex Server before backing up." + Style.RESET_ALL)
                logging.info("Plex Media Server is running - Recommend stopping Plex Server before backing up.")
        if '32_hypervvms' in config:
            if config['32_hypervvms']['enabled']:
                print(Fore.YELLOW + " !! CAUTION - HyperV has been enabled - Please check VMs are stopped before running." + Style.RESET_ALL)
                logging.info("HyperV has been enabled - Please check VMs are stopped before running.")
        if self._hyperv_possible() and not self.check_if_admin():
            print(Fore.CYAN + " -- INFO - HyperV detected on system. To backup HyperV run winbackup as admin." + Style.RESET_ALL)
            logging.info("HyperV detected on system. To backup HyperV run winbackup as admin.")

        print(Fore.CYAN + " -- INFO - Archives produced are split into 4092Mb volumes (FAT32 limitation)." + Style.RESET_ALL)
        print()      

    @staticmethod
    def remove_existing_archive(filename, path):
        paths_to_remove = [os.path.join(path, file) for file in os.listdir(path) if file.startswith(filename)]
        logging.debug(f"existing archives to be removed before backing up: {len(paths_to_remove)}")
        for path in paths_to_remove:
            try:
                send2trash(path)
                logging.debug(f"deleted file: {path}")
            except Exception as e:
                logging.error(f"could not delete file: {path}, exception {e}")
                logging.debug(traceback.format_exc())


    def backup_run(self, config:dict, out_path:str, passwd:str, quiet:bool=False) -> None:
        for key, target in sorted(config.items()):
            if target['enabled']:
                if not quiet: 
                    print(Fore.GREEN + f" >>> Backing up {target['name']} ... " + Style.RESET_ALL)
                logging.info(f"Backup starting - {target['name']}")
                filename = self._create_filename(target['name'].replace(' ', ''))

                if target['type'] == 'folder':
                    try:
                        self.remove_existing_archive(filename, out_path)
                        self.archiver.backup_folder(filename,
                                                    target['path'], out_path, passwd, dict_size=target['dict_size'], 
                                                    mx_level=target['mx_level'], full_path=target['full_path'], quiet=quiet)
                    except Exception as e:
                        logging.error(f"backup {filename} failed. Exception: {e}")
                        print(Fore.RED + f" XX - Backup {filename} failed. See logs."  + Style.RESET_ALL)
                else:
                    if key == '01_config':
                        config_path = os.path.join(out_path, 'config')
                        os.mkdir(config_path)
                        self.remove_existing_archive(filename, out_path)
                        self.config_saver.save_config_files(config_path, quiet=quiet)
                        try: 
                            self.archiver.backup_folder(filename,
                                                    config_path, out_path, passwd, dict_size=target['dict_size'], 
                                                    mx_level=target['mx_level'], full_path=target['full_path'], quiet=quiet)
                        except Exception as e:
                            logging.error(f"backup {filename} failed. Exception: {e}")
                            print(Fore.RED + f" XX - Backup {filename} failed. See logs."  + Style.RESET_ALL)
                        
                        send2trash(config_path)
                        
                    elif key == '30_plexserver':
                        try:
                            self.archiver.backup_plex_folder(self._create_filename(target['name'].replace(' ','')),
                                                        target['path'], out_path, passwd, dict_size=target['dict_size'],
                                                        mx_level=target['mx_level'], quiet=quiet)
                        except Exception as e:
                            logging.error(f"backup {filename} failed. Exception: {e}")
                            print(Fore.RED + f" XX - Backup {filename} failed. See logs."  + Style.RESET_ALL)                                                        

                    # elif key == '33_onenote':
                    #     pass
                if not quiet:
                    print(f" >> {target['name']} saved to 7z - {filename}")
                logging.debug(f"Backup finished for - {target['name']} - filename: {filename}")
        if not quiet: 
            print()
            print(Fore.GREEN + " >>> Saving File hashes ... " + Style.RESET_ALL)
        self._save_file_hashes(out_path)
        if not quiet: 
            print(" >> SHA-256 hashes of all archive files saved to sha256.txt")
            logging.info("SHA-256 hashes of all archive files saved to sha256.txt")

        if not len(passwd) == 0:
            with open(os.path.join(out_path, "Archives_are_encrypted.txt"), 'w') as file:
                file.write("7z Archives in this folder are encrypted.")


    def cli_exit(self, out_path:str, start_time:datetime) -> None:
        duration = datetime.now() - start_time
        backup_size = self.archiver._get_path_size(out_path)
        print()
        logging.debug(f"humanize completion time {humanize.naturaldelta(duration)}")
        logging.info(f"Backup completed in {duration}")
        logging.info(f"Total backup size {backup_size} ({humanize.naturalsize(backup_size, True)})")
        print(Fore.WHITE + f" Completed in {humanize.naturaldelta(duration)}" + Style.RESET_ALL)
        print(Fore.WHITE + f" Total backup size {humanize.naturalsize(backup_size, True)}")
        print(Fore.GREEN + f" Backups done! " + Style.RESET_ALL)


    def generate_blank_configfile(self, path=None):
        if not path:
            path = os.getcwd()
        if os.path.isdir(path):
            path = os.path.join(os.path.abspath(path), 'winbackup_config.yaml')
        if self._yes_no_prompt(f"Save default configuration to {path}?"):
            save_path = self.config_agent.save_YAML_config(path)
            print(f"Default config winbackup_config.yaml saved to {save_path}")


    def interactive_config_builder(self, target_path:str) -> None:
        """
        Build a custom config from the interactive script but save as config file to path
        """
        print(Fore.BLACK + Back.WHITE + " WINDOWS BACKUP - v" + __version__ + " " + Style.RESET_ALL)
        print(Fore.GREEN + f" Interactive configuration builder" + Style.RESET_ALL)
        if not target_path:
            target_path = os.getcwd()
        if os.path.isdir(target_path):
            target_path = os.path.join(os.path.abspath(target_path), 'winbackup_config.yaml')
        print(Fore.GREEN + f" Generated configuration file will be saved to: " + Style.RESET_ALL + f"{target_path}")
        print()
        

        self.config_agent.target_config = self.cli_config(self.config_agent.target_config)
        password = self.cli_get_password()
        if not len(password) == 0:
            self.config_agent.encryption_password = password
            self.config_agent.global_config['encryption_enabled'] = True
        try:
            save_path = self.config_agent.save_YAML_config(target_path)
            logging.debug(f"Interactive Configuration successfully saved to: {save_path}")
            print(Fore.GREEN + f" Configuration successfully saved to: " + Style.RESET_ALL + f"{save_path}")
        except Exception as e:
            logging.critical(f"could not save the configuration generated - exception {e}")
            logging.critical(traceback.format_exc())
            print(Fore.RED + " XX - Could not save configuration file. See logs. Exiting." + Style.RESET_ALL)
            sys.exit(1)
        

    def run_from_config_file(self, path:str) -> None:
        if path:
            if os.path.exists(path) and path.lower().endswith(('.yaml', '.yml')):
                logging.debug("Valid config path given")
                path = os.path.abspath(path)
            else:
                logging.critical(f"Config file does not exist or is not a YAML file at {path}. Exiting.")
                print(Fore.RED + f" XX - Config file does not exist or is not a YAML file at {path}. Exiting." + Style.RESET_ALL)
                sys.exit(1)
        else:
            logging.critical(f"Must give path to configuration file, none given. Exiting.")
            print(Fore.RED + f" XX - Must give path to configuration file. Exiting." + Style.RESET_ALL)
            sys.exit(1)

        try:
            global_config, target_config = self.config_agent.parse_YAML_config_file(path)
            logging.debug(f'config successfully loaded from file at {path}')
        except Exception as e:
            logging.critical(f"could not load config from file {path}. Exiting. Exception {e}")
            logging.critical(traceback.format_exc())
            print(Fore.RED + " XX - Could not load config from file. See logs. Exiting." + Style.RESET_ALL)
            sys.exit(1)

        self.cli(self.config_agent.output_root_dir, config_set=True)


    def cli(self, root_path=None, config_set:bool=False) -> None:
        signal.signal(signal.SIGINT, self._ctrl_c_handler)
        logging.debug(f"sigint connected to ctrl_c_handler")

        if not root_path:
            self.config_agent.output_root_dir = self.cli_get_output_root_path()
        else:
            if not os.path.isdir(root_path):                
                print(Fore.RED + " Output directory must be a real path. Exiting." + Style.RESET_ALL)
                logging.critical(f"given path {root_path} is not a real path. Exiting")
                sys.exit(1)
            self.config_agent.output_root_dir = os.path.abspath(root_path)
        self.output_path, self.output_folder_name, self.path_created = self._create_output_directory(self.config_agent.output_root_dir)

        self._redirect_logger(self.output_path, self.log_level)

        logging.info("WINDOWS BACKUP - v" + __version__)
        logging.info(f"Output Folder: {self.output_path}") 
        logging.debug(f"Output Root Dir: {self.config_agent.output_root_dir}")
        logging.debug(f"Output path: {self.output_path}")
        logging.debug(f"Output folder name: {self.output_folder_name}")
        logging.debug(f"path created? {self.path_created}")

        self.cli_header(self.output_path, self.output_folder_name, self.start_time)

        if not config_set:
            logging.debug(f"Config not set - getting config interactively")
            self.config_agent.target_config = self.cli_config(self.config_agent.target_config)
            self.config_agent.encryption_password = self.cli_get_password()
            if len(self.config_agent.encryption_password) != 0:
                self.config_agent.global_config['encryption_enabled'] = True
        else:
            logging.debug(f"Config already set - using config from config_agent")
            if self.config_agent.global_config['encryption_enabled'] and len(self.config_agent.encryption_password) == 0:
                logging.debug(f"encryption enabled but key length 0 - get password from cli")
                self.config_agent.encryption_password = self.cli_get_password()
            else:
                logging.debug(f"encryption disabled or password set - skip getting from cli")
       
        if self._recursive_loop_check(self.output_path, self.config_agent.target_config):
            print(Fore.RED + " XX - Output path is a child of a path that will be backed up. This will case an infinite loop. Choose a different path." + Style.RESET_ALL)
            logging.critical("Output path is a child of path that will be backed up. This will case an infinite loop. Choose a different path.")
            print(" Aborted. Exiting.")
            sys.exit(0)
       
        self.cli_config_summary(self.config_agent.target_config, 
                            self.config_agent.encryption_password, 
                            self.path_created)
       
        if not self._yes_no_prompt("Do you want to continue?"):
            logging.info("Backup cancelled after summary. Exiting.") 
            print(" Aborted. Exiting.")
            sys.exit(0)
       
        print('-' * 40)
        print()

        self.backup_run(self.config_agent.target_config, 
                        self.output_path, 
                        self.config_agent.encryption_password, 
                        False)
        self.cli_exit(self.output_path, self.start_time)
