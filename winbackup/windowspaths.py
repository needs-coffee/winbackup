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

import os
import sys
import ctypes
import ctypes.wintypes
import logging
from uuid import UUID

## from https://gist.github.com/mkropat/7550097 
## user https://github.com/mkropat
## below GUID class is under MIT licence copyright  Michael Kropat (mkropat)
class GUID(ctypes.Structure):   # [1]
    _fields_ = [
        ("Data1", ctypes.wintypes.DWORD),
        ("Data2", ctypes.wintypes.WORD),
        ("Data3", ctypes.wintypes.WORD),
        ("Data4", ctypes.wintypes.BYTE * 8)
    ] 

    def __init__(self, uuid_):
        ctypes.Structure.__init__(self)
        self.Data1, self.Data2, self.Data3, self.Data4[0], self.Data4[1], rest = uuid_.fields
        for i in range(2, 8):
            self.Data4[i] = rest>>(8 - i - 1)*8 & 0xff
## end MIT licenced code

class WindowsPaths:
    def __init__(self) -> None:
        """
        Returns the paths of user/system folders based on the win32 API
        Returns the current used folder path, not the default folder path.
        i.e. if the user default videos folder has been changed, it will return the new path.
        """

        ##
        # CISDL - old api method, deprecated since vista
        self.SHGFP_TYPE_CURRENT = 0 # get the current folder location not the default one
        self.CSIDL_PERSONAL = 5 # documents directory
        self.CSIDL_MYPICTURES = 39
        self.CSIDL_MYVIDEO = 14
        self.CSIDL_MYMUSIC = 13
        self.CSIDL_LOCAL_APPDATA = 28
        self.CSIDL_DESKTOPDIRECTORY = 16

        #https://docs.microsoft.com/en-us/windows/win32/shell/knownfolderid
        # guids from windows API (KnownFolderID)
        self.FOLDERID_DOCUMENTS = "{FDD39AD0-238F-46AF-ADB4-6C85480369C7}"
        self.FOLDERID_PICTURES = "{33E28130-4E1E-4676-835A-98395C3BC3BB}"
        self.FOLDERID_VIDEOS = "{18989B1D-99B5-455B-841C-AB7C74E4DDFC}"
        self.FOLDERID_MUSIC = "{4BD8D571-6D19-48D3-BE97-422220080E43}"
        self.FOLDERID_LOCALAPPDATA = "{F1B32785-6FBA-4FCF-9D55-7B8E7F157091}"
        self.FOLDERID_ROAMINGAPPDATA = "{3EB685DB-65F9-4CF6-A03A-E3EF65729F3D}"
        self.FOLDERID_DESKTOP = "{B4BFCC3A-DB2C-424C-B029-7FE99A87C641}"
        self.FOLDERID_DOWNLOADS = "{374DE290-123F-4565-9164-39C4925E467B}"
        self.FOLDERID_SAVEDGAMES = "{4C5C32FF-BB9D-43b0-B5B4-2D72E54EAAA4}"
        self.FOLDERID_PUBLICDOCUMENTS = "{ED4824AF-DCE4-45A8-81E2-FC7965083634}"
        self.FOLDERID_PROGRAMDATA = "{62AB5D82-FDC1-4DC3-A9DD-070D1D495D97}"
        self.FOLDERID_PROGRAMFILES = "{905e63b6-c1bf-494e-b29c-65b732d3d21a}"
        self.FOLDERID_PROGRAMFILESX86 = "{7C5A40EF-A0FB-4BFC-874A-C0F2E0B9FA8E}"

        self.paths = {}

    def get_paths(self) -> dict:
        """
        uses the KnownFolderID API
        Returns a dictionary of windows paths -> directory_name:directory_path
        also stored internally as a dictionary in self.paths
        """
        paths = {
            "documents": self.get_windows_path(self.FOLDERID_DOCUMENTS),
            "pictures": self.get_windows_path(self.FOLDERID_PICTURES),
            "videos": self.get_windows_path(self.FOLDERID_VIDEOS),
            "music": self.get_windows_path(self.FOLDERID_MUSIC),
            "local_appdata": self.get_windows_path(self.FOLDERID_LOCALAPPDATA),
            "roaming_appdata": self.get_windows_path(self.FOLDERID_ROAMINGAPPDATA),
            "desktop": self.get_windows_path(self.FOLDERID_DESKTOP),
            "downloads": self.get_windows_path(self.FOLDERID_DOWNLOADS),
            "saved_games": self.get_windows_path(self.FOLDERID_SAVEDGAMES),
            "public_documents": self.get_windows_path(self.FOLDERID_PUBLICDOCUMENTS),
            "program_data": self.get_windows_path(self.FOLDERID_PROGRAMDATA),
            "program_files": self.get_windows_path(self.FOLDERID_PROGRAMFILES),
            "program_files_x86": self.get_windows_path(self.FOLDERID_PROGRAMFILESX86),
        }
        self.paths = paths
        return paths
        

    def get_windows_path(self, known_folder_id) -> str:
        """
        Takes a known_folder_id GUID as per win32 API and returns the folder path.
        SHGetKnownFolderPath is the current maintained version supported by windows
        not compatible with windows before vista.
        """
        #KF_FLAG_DEFAULT_PATH by default is not set, so will return the current, not default path
        # https://docs.microsoft.com/en-us/windows/win32/api/guiddef/ns-guiddef-guid
        path = ''

        # below function adapted from https://gist.github.com/mkropat/7550097 - MIT licence
        buf = ctypes.c_wchar_p(ctypes.wintypes.MAX_PATH)
        try:
            return_type = ctypes.windll.shell32.SHGetKnownFolderPath(
                                                ctypes.byref(GUID(UUID(known_folder_id))), 
                                                ctypes.wintypes.DWORD(0),
                                                ctypes.wintypes.HANDLE(0),
                                                ctypes.byref(buf))
            if return_type != 0:
                raise ValueError
            path = buf.value
            ctypes.windll.ole32.CoTaskMemFree(buf)
        
        except Exception as e:
            logging.debug(f'{e}')

        return path
    

    def get_download_path(self) -> str:
        """
        return the path of the downloads directory.
        This cannot use CSIDL as there is no ID for this.
        DEPRICATED METHOD
        dont use this registry key - there is a specific wanring in the registry
        """
        if os.name == 'nt':
            import winreg
            sub_key = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders'
            downloads_guid = '{374DE290-123F-4565-9164-39C4925E467B}'
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
                location = winreg.QueryValueEx(key, downloads_guid)[0]
            return location


    def get_saved_games_path(self) -> str:
        """
        return the path of the saved_games directory.
        This cannot use CSIDL as there is no ID for this.
        DEPRICATED METHOD
        dont use this registry key - there is a specific wanring in the registry
        """
        if os.name == 'nt':
            import winreg
            sub_key = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders'
            downloads_guid = '{4C5C32FF-BB9D-43B0-B5B4-2D72E54EAAA4}'
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
                location = winreg.QueryValueEx(key, downloads_guid)[0]
            return location


    def get_cisdl_windows_path(self, csidl) -> str:
        """
        DEPRICATED METHOD
        Depricated api since vista, also does not have all folders (downloads, savedgames)
        """
        buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(None, csidl, None, self.SHGFP_TYPE_CURRENT, buf)
        return buf.value



if __name__ == "__main__":
    logging.basicConfig(stream= sys.stdout,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    level = logging.DEBUG)

    windows_paths = WindowsPaths()

    print('CISDL paths')
    print(f'Documents  : {windows_paths.get_cisdl_windows_path(windows_paths.CSIDL_PERSONAL)}')
    print(f'Pictures   : {windows_paths.get_cisdl_windows_path(windows_paths.CSIDL_MYPICTURES)}')
    print(f'Videos     : {windows_paths.get_cisdl_windows_path(windows_paths.CSIDL_MYVIDEO)}')
    print(f'Music      : {windows_paths.get_cisdl_windows_path(windows_paths.CSIDL_MYMUSIC)}')
    print(f'appdata    : {windows_paths.get_cisdl_windows_path(windows_paths.CSIDL_LOCAL_APPDATA)}')
    print(f'Destkop    : {windows_paths.get_cisdl_windows_path(windows_paths.CSIDL_DESKTOPDIRECTORY)}')
    print(f'Downloads  : {windows_paths.get_download_path()}')
    print(f'savedgames : {windows_paths.get_saved_games_path()}')
    print()

    print('get_paths method')
    paths = windows_paths.get_paths()
    print(f'Documents    : {paths["documents"]}')
    print(f'Pictures     : {paths["pictures"]}')
    print(f'Videos       : {paths["videos"]}')
    print(f'Music        : {paths["music"]}')
    print(f'appdata      : {paths["local_appdata"]}')
    print(f'Destkop      : {paths["desktop"]}')
    print(f'Downloads    : {paths["downloads"]}')
    print(f'savedgames   : {paths["savedgames"]}')
    print(f'pub doc      : {paths["public_documents"]}')
    print(f'prog data    : {paths["program_data"]}')
    print(f'prog files   : {paths["program_files"]}')
    print(f'prog files86 : {paths["program_files_x86"]}')
    print()

    print('Complete.')
    sys.exit()