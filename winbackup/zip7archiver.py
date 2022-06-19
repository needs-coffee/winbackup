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
from colorama import Fore, Style
from send2trash import send2trash
from typing import Union
import humanize


class Zip7Archiver:
    def __init__(self):
        """
        Class exposing 7z compression methods for creating the 7z and tar archives.
        """
        self.zip7_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'bin', '7z', '7z.exe')
        self.onenotemdexporter_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'OneNoteMdExporter', 'OneNoteMdExporter.exe')
        self.onenotemdexporter_files_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'OneNoteMdExporter')


    @staticmethod
    def _get_path_size(path:str) -> int:
        """
        Calculate the size of a directory tree and return size in bytes.
        """
        total_bytes = 0
        for path, dir, files in os.walk(path):
            for file in files:
                try:
                    total_bytes += os.path.getsize(os.path.join(path, file))
                except Exception as e:
                    logging.error(f"Get pathsize exception - Path: {path} Exception: {e}")
        logging.debug(f"Pathsize: {path} Size: {total_bytes}")
        return total_bytes


    def backup_folder(self, filename:str, in_folder_path:Union[str,list], out_folder:str, 
                    password:str='', dict_size:str='192m', mx_level:int=9, full_path:bool=False, 
                    split:bool=True, split_force:bool=False, quiet:bool=False) -> tuple[int, int]:
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
        - split_force    : don't check if archive will be larger than FAT32 limit, just force splitting.
        
        Returns:
        - before_size, after_size : tuple of before compresssion size and after compression size as int
        """
        # base args for all types
        # 7z normally disables progress reporting when output redirected, bsp1 fixes this.
        cmd_args = [self.zip7_path, 'a', '-t7z', '-m0=lzma2', f'-md={dict_size}', f'-mx={str(mx_level)}', '-bsp1']
            # add additional arguments depending on function arguments

        if not type(filename) == str:
            raise TypeError("Filename must be a string")

        if type(in_folder_path) == str:
            if not os.path.exists(in_folder_path):
                raise FileNotFoundError() 
        elif type(in_folder_path) == list:
            for path in in_folder_path:
                if not os.path.exists(path):
                    raise FileNotFoundError()
        else:
            raise TypeError("in_folder_path must be string or list")

        if type(out_folder) == str:
            if not os.path.exists(out_folder):
                raise FileNotFoundError()
        else:
            raise TypeError("output path must be a string")

        # add additional flags
        if split or split_force:
            if split_force:
                logging.debug(f"split_force specified - {filename} will be split.")
                cmd_args.append('-v4092m')
            else:
                # only split if the output directory will be larger than the volume size. 
                # Always split if a list of paths are given.
                if type(in_folder_path) is str:
                    path_size = self._get_path_size(in_folder_path)
                    if path_size >= 4290772992:
                        logging.debug(f"Splitting - {filename} is > split limit of 4092m (path size: {path_size/1048576:0.0f} MiB).")
                        cmd_args.append('-v4092m')
                    else:
                        logging.debug(f"Not Splitting - {filename} is < split limit of 4092m (path size: {path_size/1048576:0.0f} MiB).")
                else:
                    logging.debug("List of paths given - Splitting.")
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

        before_size_line = ''
        after_size_line = ''
        # run the backup task with a tqdm progress bar.
        try:
            with subprocess.Popen(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                shell=False, bufsize=1, universal_newlines=True, errors='ignore') as p:
                if not quiet:
                    with tqdm(total=100, colour='Cyan', leave=False, desc=f' Compressing ', unit='%') as pbar:
                        logging.debug("progress bar started")
                        for line in p.stdout: #cp1252 decoded string, ignore invalid chars like 0x81
                            if len(line.strip()) != 0:
                                logging.debug("backup_folder line output: " + line.strip())
                            if "Add new data to archive: " in line:
                                before_size_line = line.split('Add new data to archive: ')[1].strip()
                                tqdm.write(Fore.CYAN + f" >> Data to compress: {before_size_line}" + Style.RESET_ALL)
                                logging.debug(f"{filename} Data to compress: {before_size_line}")
                            if "Archive size: " in line:
                                after_size_line = line.split('Archive size: ')[1].strip()
                                tqdm.write(Fore.CYAN + f" >> Compressed Size : {after_size_line}" + Style.RESET_ALL)
                                logging.debug(f"{filename} Compressed Size: {after_size_line}")
                            if "%" in line:
                                pbar.update(int(line.split('%')[0].strip()) - pbar.n)
                else:
                    for line in p.stdout:
                        if "Add new data to archive: " in line:
                            before_size_line = line.split('Add new data to archive: ')[1].strip()
                        if "Archive size: " in line:
                            after_size_line = line.split('Archive size: ')[1].strip()
                        if len(line.strip()) != 0:
                            logging.debug("Backup line output: " + line.strip())
                        
        except Exception as e:
            logging.debug(f"Exception: {e}", exc_info=True, stack_info=True)
            if not quiet:
                print(Fore.RED + f" XX - Failed to backup {filename}. Set log level to debug for info." + Style.RESET_ALL)
            logging.error(f'Failed to backup {filename}. Set log level to debug for info.')

        before_size_bytes = int(before_size_line.split('bytes')[0].split()[-1].strip()) 
        after_size_bytes = int(after_size_line.split('bytes')[0].split()[-1].strip())
        logging.debug(f"Backup size in bytes. Before: {before_size_bytes} after: {after_size_bytes}")
        logging.info(f"Backup {filename} complete. Size: {humanize.naturalsize(before_size_bytes, True)}" +
                        f" >> {humanize.naturalsize(after_size_bytes, True)}" + 
                        f" (Compressed to {(after_size_bytes/before_size_bytes)*100:0.1f}% of input size)")

        return before_size_bytes, after_size_bytes


    def backup_plex_folder(self, filename:str, in_folder_path:str, out_folder:str, 
                        password:str='', dict_size:str='128m', mx_level:int=5, quiet:bool=False) -> tuple[int, int]:
        # From testing - backing up plex database mx9 md128m takes 10gb of ram, mx9 md192m fails memory allocation on 16gb pc.
        #plex server files should be tarballed before compression as compressing disk files causes issues when restoring.
        tar_filename = filename[:-3] + '.tar'

        # create tar with tqdm progress bar
        cmd_args = [self.zip7_path, 'a', '-ttar', '-bsp1', '-xr!Cache*', '-xr!Updates', '-xr!Crash*', 
                    os.path.join(out_folder, tar_filename), in_folder_path]
        
        with subprocess.Popen(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False,
                            bufsize=1, universal_newlines=True, errors='ignore') as p:
            if not quiet:
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
            else:
                for line in p.stdout:
                    if len(line.strip()) != 0:
                        logging.debug("Backup line output: " + line.strip())
        
        # compress the tar
        before_size, after_size = self.backup_folder(filename, os.path.join(out_folder, tar_filename), out_folder, 
                                                password, dict_size=dict_size, mx_level=mx_level, full_path=False, 
                                                split=True, split_force=True, quiet=quiet)

        # delete the tar file
        send2trash(os.path.join(out_folder,tar_filename))

        return before_size, after_size


    def backup_onenote_files(self, out_folder:str, password:str='') -> None:
        """
        CURRENTLY NOT WORKING CORRECTLY.
        Needs OneNote 2016 (not Microsoft Store OneNote), Word 2016 and OneNoteMdExporter.
        """

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