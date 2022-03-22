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
import logging
from argparse import ArgumentParser, RawTextHelpFormatter
from colorama import Fore, Back, Style, init
from . import __version__
from . import winbackup

LOG_LEVEL = logging.DEBUG

def get_commandline_arguments() -> dict:
    """
    Parse command line arguments.
    """
    helpstring = """
    windows_backup version {}
    Backupscript for windows.
    For backing up onenote - onenote for office and word need to be installed.
    """.format(__version__)

    parser = ArgumentParser(description=helpstring, formatter_class=RawTextHelpFormatter)
    parser.add_argument("path", type=str, help="The Path that should contain the output")
    parser.add_argument('-a', '--all', help="Backup all options selectable.", nargs="?", const=".", metavar='PATH')
    parser.add_argument('-v', '--verbose', help="enable verbose logging")
    parser.add_argument('-V', '--version', action='version', version=__version__)
    args = parser.parse_args()
    return args


def check_first_argument_is_path() -> str:
    """
    check the first argument is a real path, if not exit
    if is a path - return path
    """
    if len(sys.argv) == 1:
        print(Fore.RED + 'ERROR - First argument must be the output folder path' + Style.RESET_ALL)
        sys.exit(1)
    else:
        if os.path.isdir(sys.argv[1]):
           return os.path.abspath(sys.argv[1])

        else:
            print(Fore.RED + 'ERROR - first argument is not a valid folder' + Style.RESET_ALL)
            sys.exit(1)


def cli():
    # cli_args = get_commandline_arguments()
    output_path = check_first_argument_is_path()
    win_backup = winbackup.WinBackup(output_path, LOG_LEVEL)    
    win_backup.cli()
    

if __name__ == '__main__':
    sys.exit(cli())