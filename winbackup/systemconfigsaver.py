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

import sys
import os
import subprocess
from colorama import Fore, Style
import logging
import traceback
import shutil

class SystemConfigSaver:
    def __init__(self, config_save_path=None) -> None:
        """
        Saves system configuration to files for backup.
        Config save path should be an empty folder to save all config files/folders to.
        Within the winbackup script -> create 'config' folder, save config, 7z config, delete config folder.
        """
        self.config_save_path = config_save_path
        self.winfetch_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'scripts', 'winfetch.ps1')
        self.winfetch_config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'scripts', 'config.ps1')
        self.installed_prog_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'scripts', 'installed_programs.ps1')
        self.videos_path = os.path.join(os.path.expanduser('~'), 'Videos')


    @staticmethod
    def _command_runner(shell_commands:list) -> str:
        logging.debug(f'Command runner cmds: {shell_commands}')
        return subprocess.run(shell_commands, stdout=subprocess.PIPE).stdout.decode('utf-8', errors='ignore')


    def set_videos_directory_path(self, videos_path:str) -> None:
        logging.debug(f'Video path set: {videos_path}')
        self.videos_path = videos_path


    def save_config_files(self, out_path:str=None, quiet:bool=False) -> str:
        """
        Save all the configuration elements.
        Returns the path the files were saved to.
        """
        if out_path == None:
            out_path = self.config_save_path

        if quiet:
            null_dev = open(os.devnull, 'w')
            sys.stdout = null_dev

        self.save_winfetch(out_path)
        self.save_installed_programs(out_path)
        self.save_global_python_packages(out_path)
        self.save_choco_packages(out_path)
        self.save_vscode_extensions(out_path)
        self.save_path_env(out_path)
        self.save_ssh_directory(out_path)
        self.save_videos_directory_filenames(out_path, self.videos_path)
        self.save_file_associations(out_path)
        self.save_drivers(out_path)
        self.save_systeminfo(out_path)
        self.save_battery_report(out_path)

        if quiet:
            sys.stdout = sys.__stdout__
            null_dev.close()
        
        return out_path


    def save_winfetch(self, out_path:str) -> None:
        winfetch_output = self._command_runner(['powershell.exe', self.winfetch_path, 
                                                '-noimage', 
                                                '-stripansi', 
                                                '-configpath', 
                                                self.winfetch_config_path]).replace('\r\n', '\n')
        with open(os.path.join(out_path,'winfetch_output.txt'), 'w') as out_file:
            out_file.write(winfetch_output)
        print(' > Winfetch saved.')
        logging.info('Winfetch Saved.') 


    def save_installed_programs(self, out_path:str) -> None:
        installed_output = self._command_runner(['powershell.exe', self.installed_prog_path]).replace('\r\n', '\n')
        installed_output = installed_output.split('\n', 1)[1].strip()
        with open(os.path.join(out_path,'installed_programs.csv'), 'w') as out_file:
            out_file.write(installed_output)
        print(' > Installed Programs saved.')
        logging.info('Installed Programs Saved.')


    def save_global_python_packages(self, out_path:str) -> None:
        try:
            py_version = self._command_runner(['powershell.exe', 'python', '-V']).replace('\r\n', '\n')
            pip_output = self._command_runner(['powershell.exe' ,'pip', 'freeze']).replace('\r\n', '\n')
            pip_output = py_version + pip_output
            with open(os.path.join(out_path, 'python_packages.txt'), 'w') as out_file:
                out_file.write(pip_output)
            print(' > Global Python Packages saved.')
            logging.info('Global Python Packages Saved.')
        except Exception as e:
            print(Fore.RED + ' XX Unable to backup global python packages' + Style.RESET_ALL)
            logging.warning(f'Unable to save global python packages. Exception: {e}')


    def save_choco_packages(self, out_path:str) -> None:
        try:
            choco_output = self._command_runner(['powershell.exe', 
                                        'choco',  'list', '--local-only']).replace('\r\n', '\n')
            with open(os.path.join(out_path, 'choco_packages.txt'), 'w') as out_file:
                out_file.write(choco_output)
            print(' > Choco Packages saved.')
            logging.info('Choco Packages Saved.')
        except Exception as e:
            print(Fore.RED + ' XX Unable to backup choco packages.' + Style.RESET_ALL)
            logging.warning(f'Unable to save choco packages. Exception: {e}')


    def save_vscode_extensions(self, out_path:str) -> None:
        try:
            choco_output = self._command_runner(['powershell.exe', 'code', '--list-extensions']).replace('\r\n', '\n')
            with open(os.path.join(out_path, 'vscode_extensions.txt'), 'w') as out_file:
                out_file.write(choco_output)
            print(' > VSCode Extensions saved.')
            logging.info('VSCode extensions Saved.')
        except Exception as e:
            print(Fore.RED + ' XX Unable to backup VSCode extensions.' + Style.RESET_ALL)
            logging.warning(f'Unable to save VSCode extensions packages. Exception: {e}')


    def save_path_env(self, out_path:str) -> None:
        path_list = os.environ['PATH'].split(';')
        with open(os.path.join(out_path,'path.txt'), 'w') as out_file:
            for path in path_list:
                fixed_path = path.replace('\\', '/')
                out_file.write(fixed_path + '\n')
        print(' > Path env saved.')
        logging.info('Path env Saved.')


    def save_ssh_directory(self, out_path:str) -> None:
        try:
            ssh_path = os.path.join(os.path.expanduser('~'), '.ssh')
            logging.debug(f'ssh path {ssh_path}')
            if os.path.exists(ssh_path):
                shutil.copytree(ssh_path, os.path.join(out_path, '.ssh'))
                print(' > .ssh folder saved.')
                logging.info('.ssh folder Saved.')
            else:
                print(' > .ssh folder does not exist - skipping')
                logging.info('.ssh folder does not exist, skipping.')
        except Exception as e:
            print(Fore.RED + ' XX Unable to backup .ssh folder.' + Style.RESET_ALL)
            logging.warning(f'Unable to backup .ssh folder. Exception: {e}')


    def save_videos_directory_filenames(self, out_path:str, videos_path:str) -> None:
        logging.debug(f'Videos file list directory: {videos_path}')
        response = self._command_runner(['powershell.exe', 'tree', videos_path]).replace('\r\n', '\n')
        with open(os.path.join(out_path, 'videos_tree.txt'), 'w') as out_file:
            out_file.write(response)
        print(' > Videos file list saved.')
        logging.info('Video Files list Saved.')


    def save_file_associations(self, out_path:str) -> None:
        try:
            file_assoc = self._command_runner(['powershell.exe', 'cmd', '/c', 'assoc']).replace('\r\n', '\n')
            with open(os.path.join(out_path, 'file_associations.txt'), 'w') as out_file:
                out_file.write(file_assoc)
            print(' > File associations saved.')
            logging.info('File associations Saved.')
        except Exception as e:
            print(Fore.RED + ' XX Unable to backup file associations.' + Style.RESET_ALL)
            logging.warning(f'Unable to save file associations. Exception: {e}')


    def save_drivers(self, out_path:str) -> None:
        try:
            drivers = self._command_runner(['powershell.exe', 'driverquery']).replace('\r\n', '\n')
            with open(os.path.join(out_path, 'drivers.txt'), 'w') as out_file:
                out_file.write(drivers)
            print(' > Drivers saved.')
            logging.info('Drivers Saved.')
        except Exception as e:
            print(Fore.RED + ' XX Unable to backup drivers.' + Style.RESET_ALL)
            logging.warning(f'Unable to save Drivers. Exception: {e}')


    def save_systeminfo(self, out_path:str) -> None:
        try:
            sysinfo = self._command_runner(['powershell.exe', 'systeminfo']).replace('\r\n', '\n')
            with open(os.path.join(out_path, 'systeminfo.txt'), 'w') as out_file:
                out_file.write(sysinfo)
            print(' > Systeminfo saved.')
            logging.info('Systeminfo Saved.')
        except Exception as e:
            print(Fore.RED + ' XX Unable to backup systeminfo.' + Style.RESET_ALL)
            logging.warning(f'Unable to save systeminfo. Exception: {e}')
        

    def save_battery_report(self, out_path:str) -> None:
        try:
            shell_commands = ['powershell.exe', 'powercfg', 
                                '/batteryreport', '/output', 
                                os.path.join(out_path, 'batteryreport.html')]
            batreport = subprocess.run(
                            shell_commands, 
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE).stderr.decode('utf-8', errors='ignore').replace('\r\n', '\n')

            if not 'Unable to perform operation.' in batreport:
                print(" > Battery report saved.")
                logging.info("Battery report Saved.")
            elif 'media pool is empty' in batreport:
                print(" - skipping battery report - this is not a battery powered device.")
                logging.info("skipping battery report - this is not a battery powered device.")
            else:
                print(Fore.RED + " XX unable to save battery report with unknown error (Is this a battery powered device?)" + Style.RESET_ALL)
                logging.error("Unable to save battery report with unknown error (Is this a battery powered device?)")
                logging.debug(f"battery report response unknown: {batreport}")
                raise ValueError("unknown response from batreport")
        except Exception as e:
            print(Fore.RED + ' XX unable to backup battery report.' + Style.RESET_ALL)
            logging.warning(f'Unable to save battery report. Exception: {e}')        
            logging.debug(traceback.format_exc())


if __name__ == '__main__':

    from send2trash import send2trash
    logging.basicConfig(stream= sys.stdout,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        level = logging.DEBUG)

    # ?use pathlib to recursively create path without if statement
    if not os.path.isdir(os.path.join('.','tmp_test', 'config')):
        os.makedirs(os.path.join('.', 'tmp_test', 'config'))

    config_saver = SystemConfigSaver(os.path.join('tmp_test', 'config'))
    print(f'winfetch path {config_saver.winfetch_path}')
    print(f'Videos path: {config_saver.videos_path}')
    config_saver.set_videos_directory_path(os.path.join('D:/', 'Videos'))
    config_saver.save_config_files()
    print('Complete.')

    print(Fore.GREEN + ' > ' + 'Cleanup?' +' (y/n): ' + Style.RESET_ALL, end='')
    reply = str(input()).lower().strip()
    if reply.lower() in {'yes', 'y'}:
        send2trash(os.path.join('.', 'tmp_test'))
        print('Cleaned up temp dir.')
    else:
        print('not cleaning up - remove temp directory manually')
    sys.exit()