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
import logging
from tqdm import tqdm
from colorama import Fore, Back, Style, init
from send2trash import send2trash
from typing import Union


class Zip7Archiver:
    def __init__(self):
        """
        Class exposing 7z compression methods for creating the 7z and tar archives.
        """
        self.zip7_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'bin', '7z', '7z.exe')
        self.onenotemdexporter_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'OneNoteMdExporter', 'OneNoteMdExporter.exe')
        self.onenotemdexporter_files_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'OneNoteMdExporter')


    @staticmethod
    def _get_path_size(path) -> int:
        """
        Calculate the size of a directory tree and return size in bytes.
        """
        total_bytes = 0
        for path, dir, files in os.walk(path):
            for file in files:
                try:
                    total_bytes += os.path.getsize(os.path.join(path, file))
                except Exception as e:
                    logging.debug(f'Get pathsize error - {e}')
        return total_bytes


    def backup_folder(self, filename:str, in_folder_path:Union[str,list], out_folder:str, 
                    password:str='', dict_size:str='192m', mx_level:int=9, full_path:bool=False, 
                    split:bool=True, split_force:bool=False) -> None:
        """
        Main function for creating 7z archives.
        Uses TQDM to display the progress to the console.
        Parameters:
        - filename       : filename of the created archive
        - in_folder_path : string or list - path(s) of the folder to be added to the archive
        - out_folder     : where the 7z files are output
        - password       : optional password for AES encryption - if empty string encryption is disabled
        - dict_size      : string representing the LZMA2 dictionary size
        - mx_level       : LZMA2 compression level  0-9 (9 is max)
        - full_path      : archive will store the full path to the archived files, useful if multiple directories from several volumes
        - split          : if the archives should be split into separate files if larger than FAT32 limit.
        - split_force    : dont check if archive will be larger than FAT32 limit, just force splitting.
        
        Returns:
        - None
        """
        # base args for all types
        # 7z normally disables progress reporting when output redirected, bsp1 fixes this.
        cmd_args = [self.zip7_path, "a", "-t7z", "-m0=lzma2", f"-md={dict_size}", f"-mx={str(mx_level)}", "-bsp1"]
            # add additional arguments depending on function arguments

        # add additional flags
        if split or split_force:
            if split_force:
                logging.debug(f'split_force specified - Backup {filename} Will Split.')
                cmd_args.append('-v4092m')
            else:
                # only split if the output directory will be larger than the volume size. 
                # Always split if a list of paths are given.
                if type(in_folder_path) is str:
                    path_size = self._get_path_size(in_folder_path)
                    if path_size >= 4290772992:
                        logging.debug(f'backup_folder - if split - Backup {filename} is > volume split limit of 4092m (path is {path_size/1048576:0.0f} MiB). Will Split.')
                        cmd_args.append('-v4092m')
                    else:
                        logging.debug(f"backup_folder - if split - Backup {filename} is < volume split limit of 4092m (path is {path_size/1048576:0.0f} MiB). Won't Split.")
                else:
                    logging.debug('backup_folder - if split - List of paths given, therefore split the archives.')
                    cmd_args.append('-v4092m')
        if len(password) != 0:
            cmd_args.append('-mhe=on')
            cmd_args.append(f'-p{password}')
        if full_path:
            cmd_args.append('-spf2')

        # add output archive path
        cmd_args.append(os.path.join(out_folder, filename))

        # add input paths
        if type(in_folder_path) is str:
            cmd_args.append(in_folder_path)
        elif type(in_folder_path) is list:
            cmd_args += in_folder_path
        else:
            raise ValueError

        # run the backup task with a tqdm progress bar.
        try:
            with subprocess.Popen(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                    shell=False, bufsize=1, universal_newlines=True) as p:
                with tqdm(total=100, colour='Cyan', leave=False, desc=f' Compressing ', unit='%') as pbar:
                    logging.debug('progress bar started')
                    for line in p.stdout:
                        if len(line.strip()) != 0:
                            logging.debug('backup_folder line output: ' + line.strip())
                        if "Add new data to archive: " in line:
                            tqdm.write(Fore.CYAN + f" >> Data to compress: {line.split('Add new data to archive: ')[1].strip()}" + Style.RESET_ALL)
                            logging.info(f"{filename} data to compress: {line.split('Add new data to archive: ')[1].strip()}")
                        if "Archive size: " in line:
                            tqdm.write(Fore.CYAN + f" >> Compressed Size : {line.split('Archive size: ')[1].strip()}" + Style.RESET_ALL)
                            logging.info(f"{filename} Compressed Size: {line.split('Archive size: ')[1].strip()}")
                        if "%" in line:
                            pbar.update(int(line.split('%')[0].strip()) - pbar.n)
        except Exception as e:
            logging.debug(f'backup_folder function raised exception: {e}')
            print(Fore.RED + f' XX - Failed to backup {filename}. Set log level to debug for info.' + Style.RESET_ALL)
            logging.error(f'backup_folder - Failed to backup {filename}. Set log level to debug for info.')


    def backup_plex_folder(self, filename:str, in_folder_path:str, out_folder:str, 
                            password:str='', dict_size:str='128m', mx_level:int=5) -> None:
        # From testing - backing up plex database mx9 md128m takes 10gb of ram, mx9 md192m fails memory allocation on 16gb pc.
        #plex server files should be tarballed before compression as compressing disk files causes issues when restoring.
        tar_filename = filename[:-3] + '.tar'

        # create tar with tqdm progress bar
        cmd_args = [self.zip7_path, "a", "-ttar", "-bsp1", "-xr!Cache*", "-xr!Updates", "-xr!Crash*", 
                    os.path.join(out_folder, tar_filename), in_folder_path]
        
        with subprocess.Popen(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False,
                            bufsize=1, universal_newlines=True) as p:
            with tqdm(total=100, colour='Cyan', leave=False, desc=f' Tarballing PMS ', unit='%') as pbar:
                for line in p.stdout:
                    if len(line.strip()) != 0:
                        logging.debug(line.strip())
                    if "Add new data to archive: " in line:
                        tqdm.write(Fore.CYAN + f" >> Data to tarball : {line.split('Add new data to archive: ')[1].strip()}" + Style.RESET_ALL)
                        logging.info(f"{filename} data to tarball: {line.split('Add new data to archive: ')[1].strip()}")
                    if "Archive size: " in line:
                        tqdm.write(Fore.CYAN + f" >> Tarball Size    : {line.split('Archive size: ')[1].strip()}" + Style.RESET_ALL)
                        logging.info(f"{filename} Tarball Size : {line.split('Archive size: ')[1].strip()}")
                    if "%" in line:
                        pbar.update(int(line.split('%')[0].strip()) - pbar.n)
        
        # compress the tar
        self.backup_folder(filename, os.path.join(out_folder, tar_filename), out_folder, 
                        password, dict_size=dict_size, mx_level=mx_level, full_path=False, 
                        split=True, split_force=True)

        # delete the tar file
        send2trash(os.path.join(out_folder,tar_filename))


    def backup_onenote_files(self, out_folder:str, password:str='') -> None:

        working_dir = os.getcwd()

        if not os.path.isdir(os.path.join(out_folder, 'onenote')):
            os.mkdir(os.path.join(out_folder, 'onenote'))
            os.mkdir(os.path.join(out_folder, 'onenote', 'md'))
            os.mkdir(os.path.join(out_folder, 'onenote', 'joplin'))

        # backup MD mode
        try:
            print(Fore.CYAN)
            os.chdir(self.onenotemdexporter_files_path)
            subprocess.run(['powershell.exe', self.onenotemdexporter_path, '--all-notebooks', '-f 1', '--no-input'])
            subprocess.run(['powershell.exe', 'move', 
                            os.path.join(self.onenotemdexporter_files_path,'Output','*'), 
                            os.path.join(out_folder, 'onenote', 'md')])
            send2trash(os.path.join(self.onenotemdexporter_files_path, 'Output'))
        except Exception as e:
            print(Fore.RED + f' xx unable to export as md. exception {e}' + Style.RESET_ALL)
        finally:
            os.chdir(working_dir)
            print(Style.RESET_ALL)

        # backup joplin style
        try:
            print(Fore.CYAN)
            os.chdir(self.onenotemdexporter_files_path)
            subprocess.run(['powershell.exe', self.onenotemdexporter_path, '--all-notebooks', '-f 2', '--no-input'])
            subprocess.run(['powershell.exe', 'move', 
                            os.path.join(self.onenotemdexporter_files_path,'Output','*'), 
                            os.path.join(out_folder, 'onenote', 'joplin')])
            send2trash(os.path.join(self.onenotemdexporter_files_path, 'Output'))
        except Exception as e:
            print(Fore.RED + f' xx unable to export as joplin. exception {e}' + Style.RESET_ALL)
        finally:
            os.chdir(working_dir)
            print(Style.RESET_ALL)

        #backup to 7z
        self.backup_folder('onenote', os.path.join(out_folder, 'onenote'), out_folder, password, dict_size='128m')
        send2trash(os.path.join(out_folder, 'OneNote'))


    def backup_hyperv(self) -> None:
        pass


    def backup_virtualbox(self) -> None:
        pass




if __name__ == '__main__':
    print('backup folder')
    os.mkdir(os.path.join('.', 'temp'))

    logging.basicConfig(filename=os.path.join('.', 'temp', 'test.log'),
                    encoding='utf-8',
                    filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    level = logging.DEBUG)
   
    archiver = Zip7Archiver()
    archiver.backup_folder('test_archive', '.', './temp', password='')
    print('Complete.')

    print(Fore.GREEN + ' > ' + 'Cleanup?' +' (y/n): ' + Style.RESET_ALL, end='')
    reply = str(input()).lower().strip()
    if reply.lower() in ('yes', 'y'):
        send2trash(os.path.join('.', 'temp'))
        print('Cleaned up temp dir.')
    else:
        print('not cleaning up - remove temp directory manually')
    sys.exit()