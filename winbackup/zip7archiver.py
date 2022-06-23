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
        real_path = os.path.dirname(os.path.realpath(__file__))
        self.zip7_path = os.path.join(real_path, "bin", "7z", "7z.exe")
        self.onenote_ex_path = os.path.join(
            real_path,
            "OneNoteMdExporter",
            "OneNoteMdExporter.exe",
        )
        self.onenote_ex_files_path = os.path.join(real_path, "OneNoteMdExporter")

    @staticmethod
    def _get_size(path: str) -> int:
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
        logging.debug(f"Size: {total_bytes} bytes for path: {path} ")
        return total_bytes

    def _get_paths_size(self, paths: Union[str, list]) -> int:
        total_bytes = 0
        if type(paths) == str:
            total_bytes = self._get_size(paths)
        elif type(paths) == list:
            for path in paths:
                total_bytes += self._get_size(path)
        else:
            raise TypeError("path must be str or list of str")
        logging.debug(
            f"Total size of paths - {total_bytes} bytes "
            + f"({total_bytes/1048576:0.0f} MiB)",
        )
        return total_bytes

    @staticmethod
    def _archiver(filename: str, cmd_args: list, quiet: bool = False) -> tuple:
        b_size_line = ""
        a_size_line = ""
        # run the backup task with a tqdm progress bar.
        if filename.endswith(".tar"):
            desc_stub = "Tarball"
        else:
            desc_stub = "Compress"
        try:
            logging.debug(f"cli args - {' '.join(cmd_args)}")
            with subprocess.Popen(
                cmd_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                shell=False,
                bufsize=1,
                universal_newlines=True,
                errors="ignore",
            ) as p:
                if not quiet:
                    with tqdm(
                        total=100,
                        colour="Cyan",
                        leave=False,
                        desc=f" {desc_stub}ing ",
                        unit="%",
                    ) as pbar:
                        logging.debug("progress bar started")
                        for (
                            line
                        ) in p.stdout:  # cp1252 decoded string, ignore invalid chars like 0x81
                            if len(line.strip()) != 0:
                                logging.debug("archive line output: " + line.strip())
                            if "Add new data to archive: " in line:
                                b_size_line = line.split("Add new data to archive: ")[1].strip()  # fmt: skip
                                tqdm.write(
                                    Fore.CYAN
                                    + f" >> Data to {desc_stub}: {b_size_line}"
                                    + Style.RESET_ALL
                                )
                                logging.debug(f"{filename} Data to {desc_stub}: {b_size_line}")
                            if "Archive size: " in line:
                                a_size_line = line.split("Archive size: ")[1].strip()
                                tqdm.write(
                                    Fore.CYAN
                                    + f" >> {desc_stub}ed Size : {a_size_line}"
                                    + Style.RESET_ALL
                                )
                                logging.debug(f"{filename} {desc_stub}ed Size: {a_size_line}")
                            if "%" in line:
                                pbar.update(int(line.split("%")[0].strip()) - pbar.n)
                else:
                    for line in p.stdout:
                        if "Add new data to archive: " in line:
                            b_size_line = line.split("Add new data to archive: ")[1].strip()
                        if "Archive size: " in line:
                            a_size_line = line.split("Archive size: ")[1].strip()
                        if len(line.strip()) != 0:
                            logging.debug("archive line output: " + line.strip())
        except Exception as e:
            logging.debug(f"Exception: {e}", exc_info=True, stack_info=True)
            if not quiet:
                print(
                    Fore.RED
                    + f" XX - Failed to archive {filename}. Set log level to debug for info."
                    + Style.RESET_ALL
                )
            logging.error(f"Failed to archive {filename}. Set log level to debug for info.")
            raise e
        before_bytes = int(b_size_line.split("bytes")[0].split()[-1].strip())
        after_bytes = int(a_size_line.split("bytes")[0].split()[-1].strip())
        return before_bytes, after_bytes

    def backup_folder(
        self,
        zip_filename: str,
        input_paths: Union[str, list],
        out_folder: str,
        password: str = "",
        dict_size: str = "192m",
        mx_level: int = 9,
        full_path: bool = False,
        split: bool = True,
        quiet: bool = False,
        tar_before_7z: bool = False,
        extra_tar_flags: list = [],
        extra_7z_flags: list = [],
    ) -> tuple:
        """
        Main function for creating 7z archives.
        Uses TQDM to display the progress to the console.
        Parameters:
        - filename       : filename of the created archive
        - input_paths    : string or list - path(s) of the folder to be added to the archive
        - out_folder     : where the 7z files are output
        - password       : optional password for AES encryption - if empty string encryption is disabled
        - dict_size      : string representing the LZMA2 dictionary size
        - mx_level       : LZMA2 compression level  0-9 (9 is max)
        - full_path      : archive will store the full path to the archived files, useful if multiple directories from several volumes
        - split          : if the archives should be split into separate files if larger than FAT32 limit.
        - quiet          : dont print progress
        - tar_before_7z  : tarball input files before compressing
        - extra_tar_flags: extra flags to pass with the tar function (if used)
        - extra_7z_flags : extra flags to pass with the 7z function

        Returns:
        - before_size, after_size : tuple of before/after as int in bytes
        """
        # validate inputs
        if not type(zip_filename) == str:
            raise TypeError("Filename must be a string")
        if type(input_paths) == str:
            if not os.path.exists(input_paths):
                raise FileNotFoundError()
        elif type(input_paths) == list:
            for path in input_paths:
                if not os.path.exists(path):
                    raise FileNotFoundError()
        else:
            raise TypeError("input_paths must be string or list")
        if type(out_folder) == str:
            if not os.path.exists(out_folder):
                raise FileNotFoundError()
        else:
            raise TypeError("output path must be a string")

        # 7z normally disables progress reporting when output redirected, bsp1 fixes this.
        base_args = [
            self.zip7_path,
            "a",
        ]
        base_7z_args = [
            "-t7z",
            "-m0=lzma2",
            f"-md={dict_size}",
            f"-mx={str(mx_level)}",
            "-bsp1",
        ]
        base_tar_args = [
            "-ttar",
            "-bsp1",
        ]
        zip_args = base_args + base_7z_args + extra_7z_flags
        tar_args = base_args + base_tar_args + extra_tar_flags
        tar_filename = zip_filename[:-3] + ".tar"
        out_zip_path = os.path.join(out_folder, zip_filename)
        out_tar_path = os.path.join(out_folder, tar_filename)
        logging.debug(f"Base zip_args -> {' '.join(zip_args)}")
        logging.debug(f"Base tar_args -> {' '.join(tar_args)}")
        logging.debug(f"7z path       -> {out_zip_path}")
        logging.debug(f"tar path      -> {out_tar_path}")

        # get input filesize
        path_size = self._get_paths_size(input_paths)

        # parse split limit
        split_size_bytes = 4290772992
        logging.debug(f"Archive Split size -> {split_size_bytes:,} bytes")

        # add additional flags
        if split:
            # only split if input files are bigger than the split size.
            if path_size >= split_size_bytes:
                logging.debug(f"Path size > split limit - Splitting {zip_filename}")
                zip_args.append("-v4092m")
            else:
                logging.debug(f"Path size < split limit - Not Splitting {zip_filename}")
        if len(password) != 0:
            zip_args.append("-mhe=on")
            zip_args.append(f"-p{password}")
        if full_path:
            zip_args.append("-spf2")

        # add output archive path
        tar_args.append(out_tar_path)
        zip_args.append(out_zip_path)

        # convert input paths to list
        if type(input_paths) is str:
            input_cmd_args = [input_paths]
        elif type(input_paths) is list:
            input_cmd_args = input_paths
        else:
            raise ValueError

        try:
            if tar_before_7z:
                full_tar_args = tar_args + input_cmd_args
                full_7z_args = zip_args + [out_tar_path]
                before_tar_bytes, after_tar_bytes = self._archiver(tar_filename, full_tar_args, quiet)  # fmt: skip
                before_7z_bytes, after_7z_bytes = self._archiver(zip_filename, full_7z_args, quiet)  # fmt: skip
                logging.debug(f"tar size: {before_tar_bytes} --> {after_tar_bytes} bytes")
                logging.debug(f"7z size : {before_7z_bytes} --> {after_7z_bytes} bytes")
                try:
                    logging.debug(f"Deleting tar from -> {out_tar_path}")
                    send2trash(out_tar_path)
                except Exception as e:
                    logging.error(f"Could not delete {out_tar_path} - Exception {e}")
                before_bytes = before_tar_bytes
                after_bytes = after_7z_bytes
            else:
                full_7z_args = zip_args + input_cmd_args
                before_bytes, after_bytes = self._archiver(zip_filename, full_7z_args, quiet)
                logging.debug(f"7z size : {before_bytes} -> {after_bytes} bytes")
        except Exception as e:
            raise e

        logging.info(
            f"Backup {zip_filename} complete. Size: {humanize.naturalsize(before_bytes, True)}"
            + f" >> {humanize.naturalsize(after_bytes, True)}"
            + f" (Compressed to {(after_bytes/before_bytes)*100:0.1f}% of input size)"
        )
        return before_bytes, after_bytes

    def backup_onenote_files(self, out_folder: str, password: str = "") -> None:
        """
        CURRENTLY NOT WORKING CORRECTLY.
        Needs OneNote 2016 (not Microsoft Store OneNote), Word 2016 and OneNoteMdExporter.
        """

        working_dir = os.getcwd()

        if not os.path.isdir(os.path.join(out_folder, "onenote")):
            os.mkdir(os.path.join(out_folder, "onenote"))
            os.mkdir(os.path.join(out_folder, "onenote", "md"))
            os.mkdir(os.path.join(out_folder, "onenote", "joplin"))

        # backup MD mode
        try:
            print(Fore.CYAN)
            os.chdir(self.onenote_ex_files_path)
            subprocess.run(
                [
                    "powershell.exe",
                    self.onenote_ex_path,
                    "--all-notebooks",
                    "-f 1",
                    "--no-input",
                ]
            )
            subprocess.run(
                [
                    "powershell.exe",
                    "move",
                    os.path.join(self.onenote_ex_files_path, "Output", "*"),
                    os.path.join(out_folder, "onenote", "md"),
                ]
            )
            send2trash(os.path.join(self.onenote_ex_files_path, "Output"))
        except Exception as e:
            print(Fore.RED + f" xx unable to export as md. exception {e}" + Style.RESET_ALL)
        finally:
            os.chdir(working_dir)
            print(Style.RESET_ALL)

        # backup joplin style
        try:
            print(Fore.CYAN)
            os.chdir(self.onenote_ex_files_path)
            subprocess.run(
                [
                    "powershell.exe",
                    self.onenote_ex_path,
                    "--all-notebooks",
                    "-f 2",
                    "--no-input",
                ]
            )
            subprocess.run(
                [
                    "powershell.exe",
                    "move",
                    os.path.join(self.onenote_ex_files_path, "Output", "*"),
                    os.path.join(out_folder, "onenote", "joplin"),
                ]
            )
            send2trash(os.path.join(self.onenote_ex_files_path, "Output"))
        except Exception as e:
            print(
                Fore.RED + f" xx unable to export as joplin. exception {e}" + Style.RESET_ALL
            )
        finally:
            os.chdir(working_dir)
            print(Style.RESET_ALL)

        # backup to 7z
        self.backup_folder(
            "onenote",
            os.path.join(out_folder, "onenote"),
            out_folder,
            password,
            dict_size="128m",
        )
        send2trash(os.path.join(out_folder, "OneNote"))

    def backup_hyperv(self) -> None:
        pass


if __name__ == "__main__":
    print("backup folder")
    os.mkdir(os.path.join(".", "temp"))

    logging.basicConfig(
        filename=os.path.join(".", "temp", "test.log"),
        encoding="utf-8",
        filemode="a",
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.DEBUG,
    )

    archiver = Zip7Archiver()
    archiver.backup_folder("test_archive", ".", "./temp", password="")
    print("Complete.")

    print(Fore.GREEN + " > " + "Cleanup?" + " (y/n): " + Style.RESET_ALL, end="")
    reply = str(input()).lower().strip()
    if reply.lower() in ("yes", "y"):
        send2trash(os.path.join(".", "temp"))
        print("Cleaned up temp dir.")
    else:
        print("not cleaning up - remove temp directory manually")
    sys.exit()
