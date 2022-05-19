# Winbackup

![PyPI](https://img.shields.io/pypi/v/winbackup) ![GitHub release (latest by date including pre-releases)](https://img.shields.io/github/v/release/needs-coffee/winbackup?include_prereleases) ![GitHub](https://img.shields.io/github/license/needs-coffee/winbackup) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/winbackup) [![Downloads](https://pepy.tech/badge/winbackup)](https://pepy.tech/project/winbackup) ![GitHub Workflow Status (branch)](https://img.shields.io/github/workflow/status/needs-coffee/winbackup/TestRunner/main?label=build%20%28main%29) ![GitHub Workflow Status (branch)](https://img.shields.io/github/workflow/status/needs-coffee/winbackup/TestRunner/dev?label=build%20%28dev%29)

A python package to back up user files on Windows to 7z archives. Useful for offsite or cloud backups and backups can be optionally encrypted with AES256. Archives can be Optionally split archives into smaller archives for easier management. As well as user files can backup Plex Media Server, Hyper-V Virtual Machines and VirtualBox Virtual Machines.

- embeds 7za to perform compression
- optional AES256 encryption
- Archives produced are full backups - no incremental backups at present
- Archives saved in the format - host_user_yyyy-mm-dd_folder.7z
- Tested on Windows 10, Python 3.7+ (not compatible with macOS or Linux)

Installation
------------
Installation is from a package on GitHub Releases or from [pip](https://pypi.org/project/winbackup/) with ``pip install winbackup``

Usage
-----
Interactive CLI:
```shell
winbackup D:/backup_path
```

Run from configuration file:
```shell
winbackup -c ./winbackup_config.yaml
```

Create configuration file
-----
Can also be run using a configuration file. To generate a blank configuration file use ```winbackup -C```
or ```winbackup --create-configfile```. This config file must be modified before use with valid paths or will raise an exception whe run.

To generate a configuration file interactively run ```winbackup -i``` or ```winbackup --interactive-config```. This file can be run without modification for later use.

Tests
-----
To run unitests
```shell
python -m unittest discover tests -v
python -m pytest tests -v 
```

Build Packages
-----
```shell
python -m build
```

About
-----
Creation date: 2021  
Modified date: 03-05-2022  
Dependencies: colorama, tqdm, Send2trash, humanize, PyYAML


Licence
-------
This code is licensed under the GNU GPLv3 Licence.
Included dependencies and code are covered by their own licence - check project pages for details.

- For finding windows paths there is a section of code in configsaver from https://gist.github.com/mkropat/7550097 covered under the MIT Licence copyright [mkropat](https://gist.github.com/mkropat/7550097)
- [7z](https://www.7-zip.org/) - covered by the L-GPL licence available [here](https://www.7-zip.org/license.txt)
- [winfetch](https://github.com/kiedtl/winfetch) - under MIT Licence 


```
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
```