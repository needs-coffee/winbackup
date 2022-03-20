# Winbackup
- Backup windows folders to 7z files
- Backup user folders and also plex media server, onenote, hyper-v and VirtualBox
- Encryption with AES256 optional.
- file format - host_user_yyyy-mm-dd_folder.7z

Installation
------------


Usage
-----
```shell
winbackup D:/backup_path
```

Tests
-----
To run unitests:
run from the project directory (same as the readme)
```shell
python -m unittest discover tests -v
```
create a test for each subclass

Build
-----
```shell
python -m build
```

About
-----
Creation date: 2021
Modified date: 20-03-2022
Dependencies: colorama, tqdm, Send2trash, humanize

For finding windows paths there is a section of code in configsaver from https://gist.github.com/mkropat/7550097 covered under the MIT Licence copyright [mkropat](https://gist.github.com/mkropat/7550097)

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