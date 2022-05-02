# Winbackup

![PyPI](https://img.shields.io/pypi/v/winbackup) ![GitHub release (latest by date including pre-releases)](https://img.shields.io/github/v/release/needs-coffee/winbackup?include_prereleases) ![GitHub](https://img.shields.io/github/license/needs-coffee/winbackup) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/winbackup) [![Downloads](https://pepy.tech/badge/wifipasswords)](https://pepy.tech/project/winbackup)

- Backup user files on Windows to 7z Archives
- Useful for offsite/cloud backups of user files
- Encryption with AES256 optional.
- Archives are optionally split into smaller archives for easier management. 
- Backup user files and also Plex Media Server, Hyper-V Virtual Machines and VirtualBox Virtual Machines
- Archives saved in the format - host_user_yyyy-mm-dd_folder.7z
- Tested on Windows 10 (not compatible with macOS or Linux)

Installation
------------
Installation is from a package on GitHub Releases or from pip with ``pip install winbackup``

Usage
-----
Interactive CLI:
```shell
winbackup D:/backup_path
```

Tests
-----
To run unitests
```shell
python -m unittest discover tests -v
```

Build Packages
-----
```shell
python -m build
```

About
-----
Creation date: 2021
Modified date: 01-04-2022
Dependencies: colorama, tqdm, Send2trash, humanize

For finding windows paths there is a section of code in configsaver from https://gist.github.com/mkropat/7550097 covered under the MIT Licence copyright [mkropat](https://gist.github.com/mkropat/7550097)

- 7z 
- winfetch

Licence
-------
Copyright (C) 2021-2022 Joe Campbell  
 GNU GENERAL PUBLIC LICENSE (GPLv3)  

This program is free software: you can redistribute it and / or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY
without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see < https: // www.gnu.org/licenses/>.
