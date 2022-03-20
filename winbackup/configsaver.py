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
from send2trash import send2trash
from colorama import Fore, Back, Style, init
import logging
import shutil

class ConfigSaver:
    def __init__(self, config_save_path=None) -> None:
        """
        config save path should be an empty folder to save all  config files/folders to.
        within the winbackup script -> create 'config' folder, save config, 7z config, delete config folder (?send2trash).
        """
        self.config_save_path = config_save_path
        # with importlib.resources.path('winbackup', 'scripts') as p:
        #     self.winfetch_path = os.path.join(p)
        self.winfetch_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'scripts', 'winfetch.ps1')
        self.winfetch_config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'scripts', 'config.ps1')
        self.installed_prog_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'scripts', 'installed_programs.ps1')
        self.videos_path = os.path.join(os.path.expanduser('~'), 'Videos')


    @staticmethod
    def _command_runner(shell_commands: list) -> str:
        return_data = subprocess.run(shell_commands, stdout=subprocess.PIPE).stdout.decode('utf-8',errors='ignore')
        return return_data


    def set_videos_directory_path(self, videos_path) -> None:
        self.videos_path = videos_path


    def save_config_files(self, out_path=None) -> str:
        """
        save all the configuration elements.
        Returns the path the files were saved to.
        """
        if out_path == None:
            out_path = self.config_save_path

        self.save_winfetch(out_path)
        self.save_installed_programs(out_path)
        self.save_global_python_packages(out_path)
        self.save_choco_packages(out_path)
        self.save_vscode_extensions(out_path)
        self.save_path_env(out_path)
        self.save_ssh_directory(out_path)
        self.save_videos_directory_filenames(out_path)
        self.save_file_associations(out_path)
        self.save_drivers(out_path)
        self.save_systeminfo(out_path)
        self.save_battery_report(out_path)

        return out_path


    def save_winfetch(self, out_path) -> None:
        winfetch_output = self._command_runner(['powershell.exe', self.winfetch_path, 
                                                '-noimage', 
                                                '-stripansi', 
                                                '-configpath', 
                                                self.winfetch_config_path]).replace('\r\n','\n')
        with open(os.path.join(out_path,'winfetch_output.txt'),'w') as out_file:
            out_file.write(winfetch_output)
        print(' > Winfetch saved.')
        logging.info('config_backup - Winfetch Saved.')


    def save_installed_programs(self, out_path) -> None:
        installed_output = self._command_runner(['powershell.exe', self.installed_prog_path]).replace('\r\n','\n')
        with open(os.path.join(out_path,'installed_programs.txt'),'w') as out_file:
            out_file.write(installed_output)
        print(' > Installed Programs saved.')
        logging.info('config_backup - Installed Programs Saved.')


    def save_global_python_packages(self, out_path) -> None:
        try:
            py_version = self._command_runner(['powershell.exe', 'python', '-V']).replace('\r\n', '\n')
            pip_output = self._command_runner(['powershell.exe' ,'pip', 'freeze']).replace('\r\n', '\n')
            pip_output = py_version + pip_output
            with open(os.path.join(out_path, 'python_packages.txt'),'w') as out_file:
                out_file.write(pip_output)
            print(' > Global Python Packages saved.')
            logging.info('config_backup - Global Python Packages Saved.')
        except:
            print(Fore.RED + ' xx unable to backup global python packages' + Style.RESET_ALL)
            logging.warning('config_backup - Unable to save global python packages.')


    def save_choco_packages(self, out_path) -> None:
        try:
            choco_output = self._command_runner(['powershell.exe', 'choco', 
                                                'list', '--local-only']).replace('\r\n','\n')
            with open(os.path.join(out_path, 'choco_packages.txt'),'w') as out_file:
                out_file.write(choco_output)
            print(' > Choco Packages saved.')
            logging.info('config_backup - Choco Pacakges Saved.')
        except:
            print(Fore.RED + ' xx unable to backup choco packages.' + Style.RESET_ALL)
            logging.warning('config_backup - Unable to save choco packages.')


    def save_vscode_extensions(self, out_path) -> None:
        try:
            choco_output = self._command_runner(['powershell.exe', 'code', '--list-extensions']).replace('\r\n', '\n')
            with open(os.path.join(out_path, 'vscode_extensions.txt'),'w') as out_file:
                out_file.write(choco_output)
            print(' > VSCode Extensions saved.')
            logging.info('config_backup - Vscode extensions Saved.')
        except:
            print(Fore.RED + ' xx unable to backup VSCode extensions.' + Style.RESET_ALL)
            logging.warning('config_backup - Unable to save VSCode extensions packages.')


    def save_path_env(self, out_path) -> None:
        path_list = os.environ['PATH'].split(';')
        with open(os.path.join(out_path,'path.txt'),'w') as out_file:
            for path in path_list:
                fixed_path = path.replace('\\','/')
                out_file.write(fixed_path + '\n')
        print(' > Path env saved.')
        logging.info('config_backup - Path env Saved.')


    def save_ssh_directory(self, out_path) -> None:
        try:
            ssh_path = os.path.join(os.path.expanduser('~'),'.ssh')
            logging.debug(f'ssh path {ssh_path}')
            if os.path.exists(ssh_path):
                shutil.copytree(ssh_path, os.path.join(out_path, '.ssh'))
                print(' > .ssh folder saved.')
                logging.info('config_backup - .ssh folder Saved.')
            else:
                print(' > .ssh folder does not exist - skipping')
                logging.info('config_backup - .ssh folder does not exist, skipping.')
        except Exception as e:
            logging.debug(f'exception: {e}')
            print(Fore.RED + ' xx unable to backup .ssh folder.' + Style.RESET_ALL)
            logging.warning('config_backup - unable to backup .ssh folder.')


    def save_videos_directory_filenames(self, out_path) -> None:
        installed_output = self._command_runner(['powershell.exe', 'tree', self.videos_path]).replace('\r\n','\n')
        with open(os.path.join(out_path, 'videos_tree.txt'),'w') as out_file:
            out_file.write(installed_output)
        print(' > Videos file list saved.')
        logging.info('config_backup - Video Files list Saved.')


    def save_file_associations(self, out_path) -> None:
        try:
            file_assoc = self._command_runner(['powershell.exe', 'cmd', '/c', 'assoc']).replace('\r\n', '\n')
            with open(os.path.join(out_path, 'file_associations.txt'), 'w') as out_file:
                out_file.write(file_assoc)
            print(' > File associations saved.')
            logging.info('config_backup - file associations Saved.')
        except:
            print(Fore.RED + ' xx unable to backup file associations.' + Style.RESET_ALL)
            logging.warning('config_backup - unable to save file associations.')


    def save_drivers(self, out_path) -> None:
        try:
            drivers = self._command_runner(['powershell.exe', 'driverquery']).replace('\r\n', '\n')
            with open(os.path.join(out_path, 'drivers.txt'), 'w') as out_file:
                out_file.write(drivers)
            print(' > Drivers saved.')
            logging.info('config_backup - Drivers Saved.')
        except:
            print(Fore.RED + ' xx unable to backup drivers.' + Style.RESET_ALL)
            logging.warning('config_backup - Unable to save Drivers.')


    def save_systeminfo(self, out_path) -> None:
        try:
            sysinfo = self._command_runner(['powershell.exe', 'systeminfo']).replace('\r\n', '\n')
            with open(os.path.join(out_path, 'systeminfo.txt'), 'w') as out_file:
                out_file.write(sysinfo)
            print(' > Systeminfo saved.')
            logging.info('config_backup - Systeminfo Saved.')
        except:
            print(Fore.RED + ' xx unable to backup systeminfo.' + Style.RESET_ALL)
            logging.warning('config_backup - Unable to save systeminfo.')
        

    def save_battery_report(self, out_path) -> None:
        try:
            shell_commands = ['powershell.exe', 'powercfg', 
                                '/batteryreport', '/output', 
                                os.path.join(out_path,'batteryreport.html')]
            batreport = subprocess.run(
                            shell_commands, 
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE).stderr.decode('utf-8', errors='ignore').replace('\r\n', '\n')

            if not 'Unable to perform operation.' in batreport:
                print(' > battery report saved.')
                logging.info('config_backup - battery report Saved.')
            else:
                print(Fore.RED + ' xx unable to backup battery report (is this a battery powered device?)' + Style.RESET_ALL)
                logging.warning('config_backup - Unable to save battery report (is this a battery powered device?).')
        except:
            print(Fore.RED + ' xx unable to backup battery report.' + Style.RESET_ALL)
            logging.warning('config_backup - Unable to save battery report - Exception occured.')        


if __name__ == '__main__':
    logging.basicConfig(stream= sys.stdout,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        level = logging.DEBUG)

    # ?use pathlib to recursivley create path without if statement
    if not os.path.isdir(os.path.join('.','tmp_test', 'config')):
        os.makedirs(os.path.join('.', 'tmp_test', 'config'))

    config_saver = ConfigSaver(os.path.join('tmp_test', 'config'))
    print(f'winfetch path {config_saver.winfetch_path}')
    print(f'Videos path: {config_saver.videos_path}')
    config_saver.set_videos_directory_path(os.path.join('D:/', 'Videos'))
    config_saver.save_config_files()
    print('Complete.')

    print(Fore.GREEN + ' > ' + 'Cleanup?' +' (y/n): ' + Style.RESET_ALL, end='')
    reply = str(input()).lower().strip()
    if reply.lower() in ('yes', 'y'):
        send2trash(os.path.join('.', 'tmp_test'))
        print('Cleaned up temp dir.')
    else:
        print('not cleaning up - remove temp directory manually')
    sys.exit()