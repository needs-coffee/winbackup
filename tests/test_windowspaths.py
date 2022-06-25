#!/usr/bin/env python3

##
## tests for windowspaths module
##

import unittest
import os
import winbackup.windowspaths


class TestValidPathsReturned(unittest.TestCase):
    def setUp(self) -> None:
        self.windows_paths = winbackup.windowspaths.WindowsPaths()

    def test_get_windows_path_documents(self):
        path = self.windows_paths.get_windows_path(self.windows_paths.FOLDERID_DOCUMENTS)
        self.assertTrue(os.path.isdir(path))

    def test_get_windows_path_pictures(self):
        path = self.windows_paths.get_windows_path(self.windows_paths.FOLDERID_PICTURES)
        self.assertTrue(os.path.isdir(path))

    def test_get_windows_path_videos(self):
        path = self.windows_paths.get_windows_path(self.windows_paths.FOLDERID_VIDEOS)
        self.assertTrue(os.path.isdir(path))

    def test_get_windows_path_music(self):
        path = self.windows_paths.get_windows_path(self.windows_paths.FOLDERID_MUSIC)
        self.assertTrue(os.path.isdir(path))

    def test_get_windows_path_localappdata(self):
        path = self.windows_paths.get_windows_path(self.windows_paths.FOLDERID_LOCALAPPDATA)
        self.assertTrue(os.path.isdir(path))

    def test_get_windows_path_roamingappdata(self):
        path = self.windows_paths.get_windows_path(self.windows_paths.FOLDERID_ROAMINGAPPDATA)
        self.assertTrue(os.path.isdir(path))

    def test_get_windows_path_desktop(self):
        path = self.windows_paths.get_windows_path(self.windows_paths.FOLDERID_DESKTOP)
        self.assertTrue(os.path.isdir(path))

    def test_get_windows_path_downloads(self):
        path = self.windows_paths.get_windows_path(self.windows_paths.FOLDERID_DOWNLOADS)
        self.assertTrue(os.path.isdir(path))

    def test_get_windows_path_savedgames(self):
        path = self.windows_paths.get_windows_path(self.windows_paths.FOLDERID_SAVEDGAMES)
        self.assertTrue(os.path.isdir(path))

    def test_get_windows_path_publicdocuments(self):
        path = self.windows_paths.get_windows_path(self.windows_paths.FOLDERID_PUBLICDOCUMENTS)
        self.assertTrue(os.path.isdir(path))

    def test_get_windows_path_programdata(self):
        path = self.windows_paths.get_windows_path(self.windows_paths.FOLDERID_PROGRAMDATA)
        self.assertTrue(os.path.isdir(path))

    def test_get_windows_path_programfiles(self):
        path = self.windows_paths.get_windows_path(self.windows_paths.FOLDERID_PROGRAMFILES)
        self.assertTrue(os.path.isdir(path))

    def test_get_windows_path_programfilesx86(self):
        path = self.windows_paths.get_windows_path(self.windows_paths.FOLDERID_PROGRAMFILESX86)
        self.assertTrue(os.path.isdir(path))


class TestReturnType(unittest.TestCase):
    def setUp(self) -> None:
        self.windows_paths = winbackup.windowspaths.WindowsPaths()

    def test_get_paths_returns_dict(self):
        self.assertTrue(type(self.windows_paths.get_paths() is dict))

    def test_get_windows_path_documents_returns_string(self):
        path = self.windows_paths.get_windows_path(self.windows_paths.FOLDERID_DOCUMENTS)
        self.assertTrue(type(path) == str)

    def test_get_windows_path_pictures_returns_string(self):
        path = self.windows_paths.get_windows_path(self.windows_paths.FOLDERID_PICTURES)
        self.assertTrue(type(path) == str)

    def test_get_windows_path_videos_returns_string(self):
        path = self.windows_paths.get_windows_path(self.windows_paths.FOLDERID_VIDEOS)
        self.assertTrue(type(path) == str)

    def test_get_windows_path_music_returns_string(self):
        path = self.windows_paths.get_windows_path(self.windows_paths.FOLDERID_MUSIC)
        self.assertTrue(type(path) == str)

    def test_get_windows_path_localappdata_returns_string(self):
        path = self.windows_paths.get_windows_path(self.windows_paths.FOLDERID_LOCALAPPDATA)
        self.assertTrue(type(path) == str)

    def test_get_windows_path_roamingappdata_returns_string(self):
        path = self.windows_paths.get_windows_path(self.windows_paths.FOLDERID_ROAMINGAPPDATA)
        self.assertTrue(type(path) == str)

    def test_get_windows_path_desktop_returns_string(self):
        path = self.windows_paths.get_windows_path(self.windows_paths.FOLDERID_DESKTOP)
        self.assertTrue(type(path) == str)

    def test_get_windows_path_downloads_returns_string(self):
        path = self.windows_paths.get_windows_path(self.windows_paths.FOLDERID_DOWNLOADS)
        self.assertTrue(type(path) == str)

    def test_get_windows_path_savedgames_returns_string(self):
        path = self.windows_paths.get_windows_path(self.windows_paths.FOLDERID_SAVEDGAMES)
        self.assertTrue(type(path) == str)

    def test_get_windows_path_publicdocuments_returns_string(self):
        path = self.windows_paths.get_windows_path(self.windows_paths.FOLDERID_PUBLICDOCUMENTS)
        self.assertTrue(type(path) == str)

    def test_get_windows_path_programdata_returns_string(self):
        path = self.windows_paths.get_windows_path(self.windows_paths.FOLDERID_PROGRAMDATA)
        self.assertTrue(type(path) == str)

    def test_get_windows_path_programfiles_returns_string(self):
        path = self.windows_paths.get_windows_path(self.windows_paths.FOLDERID_PROGRAMFILES)
        self.assertTrue(type(path) == str)

    def test_get_windows_path_programfilesx86_returns_string(self):
        path = self.windows_paths.get_windows_path(self.windows_paths.FOLDERID_PROGRAMFILESX86)
        self.assertTrue(type(path) == str)


if __name__ == "__main__":
    unittest.main(verbosity=2)
