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
import logging
import ctypes
import getpass
import hashlib
from datetime import datetime
from send2trash import send2trash
from colorama import Fore, Back, Style, init
from pathlib import Path
import humanize

from . import configsaver
from . import zip7archiver
from . import windowspaths
from . import __version__

init(autoreset=False)


class WinBackup:
    def __init__(self):
        """
        Backup windows files to 7z archives
        """
        self.archiver = zip7archiver.Zip7Archiver()
        self.config_saver = configsaver.ConfigSaver()
        self.windows_paths = windowspaths.WindowsPaths()
        self.paths = self.windows_paths.get_paths()
        self.output_path = ''
        self.passwd = ''

        # Each backup target is a dictionary, use the config list to interate over
        # name - target name, will also be used to derive the output folder name
        # type - special = specific backup function, folder = single folder target
        # path - backup target path
        # enabled - if the target will be backed up, default false for all
        # hidden - if a specific target is impossible, set as hidden and don't show in config
        # dict_size and mx_level - 7z dictionary size and compression level
        # full path - store the full path to the compressed files
        self.config = {
        '01_config': {'name': 'Config', 'type': 'special', 'path': None, 'enabled': False, 'hidden': False, 'dict_size': '192m', 'mx_level': 9, 'full_path': False},
        '10_documents': {'name': 'Documents', 'type': 'folder', 'path': self.paths['documents'], 'enabled': False, 'hidden': False, 'dict_size': '192m', 'mx_level': 9, 'full_path': False},
        '11_desktop': {'name': 'Desktop', 'type': 'folder', 'path': self.paths['desktop'], 'enabled': False, 'hidden': False, 'dict_size': '192m', 'mx_level': 9, 'full_path': False},
        '12_pictures': {'name': 'Pictures', 'type': 'folder', 'path': self.paths['pictures'], 'enabled': False, 'hidden': False, 'dict_size': '32m', 'mx_level': 5, 'full_path': False},
        '13_downloads': {'name': 'Downloads', 'type': 'folder', 'path': self.paths['downloads'], 'enabled': False, 'hidden': False, 'dict_size': '192m', 'mx_level': 9, 'full_path': False},
        '14_videos': {'name': 'Videos', 'type': 'folder', 'path': self.paths['videos'], 'enabled': False, 'hidden': False, 'dict_size': '32m', 'mx_level': 5, 'full_path': False},
        '15_music': {'name': 'Music', 'type': 'folder', 'path': self.paths['music'], 'enabled': False, 'hidden': False, 'dict_size': '32m', 'mx_level': 5, 'full_path': False},
        '16_savedgames': {'name': 'Saved Games', 'type': 'folder', 'path': self.paths['saved_games'], 'enabled': False, 'hidden': False, 'dict_size': '192m', 'mx_level': 9, 'full_path': False},
        '30_plexserver': {'name': 'Plex Server', 'type': 'special', 'path': os.path.join(self.paths['local_appdata'], 'Plex Media Server'), 'enabled': False, 'hidden': not self._plex_possible(self.paths), 'dict_size': '192m', 'mx_level': 9, 'full_path': False},
        '31_virtualboxvms': {'name': 'VirtualBox VMs', 'type': 'folder', 'path': os.path.join(os.path.expanduser('~'), 'VirtualBox VMs'), 'enabled': False, 'hidden': not self._virtualbox_possible(self.paths), 'dict_size': '128m', 'mx_level': 9, 'full_path': False},
        '32_hypervvms': {'name': 'HyperV VMs', 'type': 'folder', 'path': None, 'enabled': False, 'hidden': True, 'dict_size': '128m', 'mx_level': 9, 'full_path': True},
        '33_onenote': {'name': 'Onenote', 'type': 'folder', 'path': None, 'enabled': False, 'hidden': True, 'dict_size': '192m', 'mx_level': 9, 'full_path': False},
        }

        self.config_saver.set_videos_directory_path(self.config['14_videos']['path'])
        signal.signal(signal.SIGINT, self._ctrl_c_handler)


    def _ctrl_c_handler(self, signum, frame):
        print()
        print(Fore.RED + " Ctrl-C received - Exiting." + Style.RESET_ALL)
        sys.exit(1)        


    def _plex_possible(self, paths:list) -> bool:
        if os.path.exists(os.path.join(paths['local_appdata'], 'Plex Media Server')):
            return True
        else:
            return False


    def _virtualbox_possible(self, paths:list) -> bool:
        if os.path.exists(os.path.join(os.path.expanduser('~'), 'VirtualBox VMs')):
            return True
        else:
            return False


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
    def _create_output_directory(output_dir:str) -> tuple[str, str, bool]:
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


    def print_cli_header(self, output_path:str, output_folder_name:str, start_time:datetime) -> None:
        logging.info("WINDOWS BACKUP - v" + __version__)
        logging.info(f"Output Folder: {output_path}")

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
            if not target['hidden']:
                new_config[key]['enabled'] = self._yes_no_prompt(f"Backup {target['name']}?")
        print()
        return new_config


    def cli_get_password(self) -> str:
        passwd = ''
        while(1):
            print(Fore.GREEN + f" > Password for encryption : " + Style.RESET_ALL, end='')
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
    

    def cli_summary(self, config:dict, passwd:str, path_created:bool) -> None:
        print(Fore.BLACK + Back.WHITE + " ** CONFIG SUMMARY ** " + Style.RESET_ALL + Fore.GREEN)
        for key, target in sorted(config.items()):
            if not target['hidden']:
                print(f" Backup {target['name']:<12} - {'Yes' if target['enabled']==True else 'No'}")
                logging.info(f"Config > {target['name']} - {target['enabled']}")
        print(f" Encryption          - {'No' if len(passwd)==0 else 'Yes'}")
        print(Style.RESET_ALL)
    
        if len(passwd) <= 12 and len(passwd)!= 0:
            print(Fore.YELLOW + f" !! CAUTION - The given password is short. Consider a longer password." + Style.RESET_ALL)
        if not path_created:
            print(Fore.YELLOW + " !! CAUTION - The backup target is an existing directory - The existing contents of the directory may be destroyed if you proceed." + Style.RESET_ALL)
        print(" Archives produced are split into 4092Mb volumes (FAT32 limitation).")
        print()      
 

    def backup_run(self, config:dict, out_path:str, passwd:str, quiet:bool=False) -> None:
        for key, target in sorted(config.items()):
            if target['enabled']:
                if not quiet: 
                    print(Fore.GREEN + f" >>> Backing up {target['name']} ... " + Style.RESET_ALL)
                logging.info(f"Backup starting - {target['name']}")
                filename = self._create_filename(target['name'].replace(' ', ''))
              
                if target['type'] == 'folder':
                    self.archiver.backup_folder(filename,
                                                target['path'], out_path, passwd, dict_size=target['dict_size'], 
                                                mx_level=target['mx_level'], full_path=target['full_path'], quiet=quiet)
                else:
                    if key == '01_config':
                        config_path = os.path.join(out_path, 'config')
                        os.mkdir(config_path)
                        self.config_saver.save_config_files(config_path, quiet=quiet)
                        self.archiver.backup_folder(filename,
                                                    config_path, out_path, passwd, dict_size=target['dict_size'], 
                                                    mx_level=target['mx_level'], full_path=target['full_path'], quiet=quiet)
                        send2trash(config_path)
                        
                    elif key == '30_plexserver':
                        self.archiver.backup_plex_folder(self._create_filename(target['name'].replace(' ','')),
                                                    target['path'], out_path, passwd, dict_size=target['dict_size'],
                                                    mx_level=target['mx_level'], quiet=quiet)
                    elif key == '32_hypervvms':
                        pass
                    elif key == '33_onenote':
                        pass
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


    def _start_logger(self, log_level:int, output_path:str) -> None:
        if log_level == logging.DEBUG:
            log_format = '%(asctime)s - %(levelname)s [%(module)s:%(funcName)s:%(lineno)d] -> %(message)s'
        else:
            log_format = '%(asctime)s - %(levelname)s -> %(message)s'

        logging.basicConfig(filename=os.path.join(output_path, 'winbackup.log'), 
                encoding='utf-8',
                filemode='w', 
                format=log_format,
                level=log_level)


    def cli(self, output_root_dir:str, log_level:int=logging.INFO) -> None:
        output_path, output_folder_name, path_created = self._create_output_directory(output_root_dir)
        start_time = datetime.now()
        self.output_root_dir = output_root_dir
        self.output_path = output_path
        
        self._start_logger(log_level, output_path)
        self.print_cli_header(output_path, output_folder_name, start_time)
        self.config = self.cli_config(self.config)
        self.passwd = self.cli_get_password()
       
        if self._recursive_loop_check(output_path, self.config):
            print(Fore.RED + " XX - Output path is a child of a path that will be backed up. This will case an infinite loop. Choose a different path." + Style.RESET_ALL)
            logging.critical("Output path is a child of path that will be backed up. This will case an infinite loop. Choose a different path.")
            print(" Aborted. Exiting.")
            sys.exit(0)
       
        self.cli_summary(self.config, self.passwd, path_created)
       
        if not self._yes_no_prompt("Do you want to continue?"):
            logging.info("Backup cancelled after summary. Exiting.") 
            print(" Aborted. Exiting.")
            sys.exit(0)
       
        print('-' * 40)
        print()

        self.backup_run(self.config, self.output_path, self.passwd, False)
        self.cli_exit(output_path, start_time)
