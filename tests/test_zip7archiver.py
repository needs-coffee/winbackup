#!/usr/bin/env python3

##
## tests for zip7archiver module
##

import unittest
import os
import tempfile
import winbackup.zip7archiver


class TestValidArchive(unittest.TestCase):
    def setUp(self) -> None:
        self.archiver = winbackup.zip7archiver.Zip7Archiver()
        self.temp_directory = tempfile.TemporaryDirectory()
        self.temp_path = os.path.join(self.temp_directory.name)
        self.testdir_path = self._fill_temp_dir_with_files(self.temp_path)

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def _fill_temp_dir_with_files(self, path) -> None:
        subfolder_path = os.path.join(path, "test1")
        os.mkdir(subfolder_path)
        for i in range(1, 1000, 1):
            with open(os.path.join(subfolder_path, f"test_{i}.txt"), "wb") as fout:
                fout.write(os.urandom(32768))
        return subfolder_path

    def test_backup_folder(self):
        filename = "test_backup.7z"
        self.archiver.backup_folder(
            filename,
            self.testdir_path,
            self.temp_path,
            password="",
            quiet=True,
        )
        self.assertTrue(os.path.isfile(os.path.join(self.temp_path, filename)))

    def test_backup_folder_tar_before(self):
        filename = "test_plex_backup.7z"
        self.archiver.backup_folder(
            filename,
            self.testdir_path,
            self.temp_path,
            password="",
            quiet=True,
            tar_before_7z=True,
        )
        # split force is currently set for plex server so files will end with a number
        self.assertTrue(os.path.isfile(os.path.join(self.temp_path, filename)))


class TestReturnType(unittest.TestCase):
    def setUp(self) -> None:
        self.archiver = winbackup.zip7archiver.Zip7Archiver()
        self.temp_directory = tempfile.TemporaryDirectory()
        self.temp_path = self.temp_directory.name
        self.testdir_path = self._fill_temp_dir_with_files(self.temp_path)

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def _fill_temp_dir_with_files(self, path) -> None:
        subfolder_path = os.path.join(path, "test1")
        os.mkdir(subfolder_path)
        for i in range(1, 1000, 1):
            with open(os.path.join(subfolder_path, f"test_{i}.txt"), "wb") as fout:
                fout.write(os.urandom(32768))
        return subfolder_path

    def test_get_path_size_returns_int(self):
        response = self.archiver._get_path_size(self.testdir_path)
        self.assertTrue(type(response) == int)

    def test_backup_folder_returns_tuple(self):
        response = self.archiver.backup_folder(
            "test_backup_return.7z", self.testdir_path, self.temp_path, password="", quiet=True
        )
        self.assertTrue(type(response) == tuple)


if __name__ == "__main__":
    unittest.main(verbosity=2)
