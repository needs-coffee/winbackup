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
import logging
from argparse import ArgumentParser, RawTextHelpFormatter
from . import __version__, __license__, __copyright__
from . import winbackup

DEFAULT_LOG_LEVEL = logging.INFO

def get_commandline_arguments() -> dict:
    """
    Parse command line arguments.
    """
    helpstring = """
    Backupscript for windows.
    Backs up user folders to 7z archives.
    Can also back up Plex Media Server, Hyper-V VMs and VirtualBox VMs
    
    winbackup version {}
    This program comes with ABSOLUTELY NO WARRANTY. 
    This is free software, and you are welcome to redistribute it 
    under certain conditions, see the GPLv3 Licence file attached.
    {} - Licence: {} """.format(__version__, __copyright__, __license__)

    parser = ArgumentParser(description=helpstring, formatter_class=RawTextHelpFormatter)
    parser.add_argument("path", type=str, help="The Path that should contain the backup", nargs="?")
    parser.add_argument('-a', '--all', help="Backup all options selectable.", action="store_true")
    parser.add_argument('-c', '--configfile', help="supply a configuration file.", action="store_true")
    parser.add_argument('-C', '--create-configfile', help="Generate default configuration file. If no path given will save to CWD.", action="store_true")
    parser.add_argument('-i', '--interactive-config', help="Generate a configuration file interactively", action="store_true")
    parser.add_argument('-v', '--verbose', help="Enable verbose logging. Log will initially output to the CWD.", action="store_true") #?store_const
    parser.add_argument('-V', '--version', action='version', version=__version__)
    args = vars(parser.parse_args())
    return args


def cli():
    cli_args = get_commandline_arguments()
    
    path = cli_args['path']
    if cli_args['verbose']:
        log_level = logging.DEBUG
    else:
        log_level = DEFAULT_LOG_LEVEL

    win_backup = winbackup.WinBackup(log_level)
    if cli_args['configfile']:
        win_backup.run_from_config_file(path)
    elif cli_args['create_configfile']:
        win_backup.generate_blank_configfile(path)
    elif cli_args['interactive_config']:
        win_backup.interactive_config_builder(path)
    else:
        win_backup.cli(path)
    

if __name__ == '__main__':
    sys.exit(cli())