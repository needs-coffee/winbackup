#!/usr/bin/env python3

##
## tests for configsaver module
##

import unittest
import os
import sys
from tempfile import TemporaryDirectory
import winbackup.systemconfigsaver


class TestValidOutput(unittest.TestCase):
    def setUp(self) -> None:
        self.config_saver = winbackup.systemconfigsaver.SystemConfigSaver()

    def test_command_runner(self):
        response = self.config_saver._command_runner(
            ["powershell.exe", "Write-Output", "Test"]
        ).strip()
        self.assertTrue(response == "Test")

    def test_set_videos_directory_path(self):
        test_path = "C:/Users"
        self.config_saver.set_videos_directory_path(test_path)
        self.assertTrue(self.config_saver.videos_path == test_path)

    def test_save_config_files(self):
        """
        Tests saves config files to disk and return value is a path
        """
        with TemporaryDirectory() as temp_directory:
            null_dev = open(os.devnull, "w")
            sys.stdout = null_dev
            response = self.config_saver.save_config_files(temp_directory)
            sys.stdout = sys.__stdout__
            null_dev.close()
            files = [file for file in os.listdir(temp_directory)]
            num_files = len(files)
            with self.subTest(msg="Number of files"):
                self.assertTrue(num_files >= 9)
            with self.subTest(msg=".ssh directory copied if exists"):
                if os.path.exists(os.path.join(os.path.expanduser("~"), ".ssh")):
                    self.assertTrue(os.path.isdir(os.path.join(temp_directory, ".ssh")))
                else:
                    self.assertFalse(os.path.isdir(os.path.join(temp_directory, ".ssh")))
            with self.subTest(msg="config path is real path"):
                self.assertTrue(os.path.isdir(response))

    def test_save_winfetch(self):
        """
        Will test a single line in the winfetch file that should always exist.
        """
        with TemporaryDirectory() as temp_directory:
            self.config_saver.save_winfetch(temp_directory)
            with open(os.path.join(temp_directory, "winfetch_output.txt"), "r") as fin:
                for line in fin.readlines():
                    if line.startswith("OS:"):
                        self.assertTrue("Windows" in line)

    def test_save_installed_programs(self):
        """
        Will test a single line in the installed programs file that should always exist.
        """
        with TemporaryDirectory() as temp_directory:
            self.config_saver.save_installed_programs(temp_directory)
            with open(os.path.join(temp_directory, "installed_programs.csv"), "r") as fin:
                for line in fin.readlines():
                    if line.startswith("DisplayName"):
                        self.assertTrue("DisplayVersion" in line)

    def test_save_global_python_packages(self):
        with TemporaryDirectory() as temp_directory:
            self.config_saver.save_global_python_packages(temp_directory)
            with open(os.path.join(temp_directory, "python_packages.txt"), "r") as fin:
                line = fin.readlines()[0]
                self.assertTrue("Python" in line)

    def test_save_choco_packages(self):
        with TemporaryDirectory() as temp_directory:
            self.config_saver.save_choco_packages(temp_directory)
            with open(os.path.join(temp_directory, "choco_packages.txt"), "r") as fin:
                line = fin.readlines()[0]
                self.assertTrue("Chocolatey" in line)

    def test_save_vscode_extensions(self):
        with TemporaryDirectory() as temp_directory:
            self.config_saver.save_vscode_extensions(temp_directory)
            self.assertTrue(
                os.path.exists(os.path.join(temp_directory, "vscode_extensions.txt"))
            )

    def test_save_path_env(self):
        with TemporaryDirectory() as temp_directory:
            self.config_saver.save_path_env(temp_directory)
            self.assertTrue(os.path.exists(os.path.join(temp_directory, "path.txt")))

    @unittest.skipIf(not os.path.exists(os.path.join(os.path.expanduser('~'), '.ssh')), ".SSH Does not exist")  # fmt: skip
    def test_save_ssh_directory(self):
        with TemporaryDirectory() as temp_directory:
            self.config_saver.save_ssh_directory(temp_directory)
            self.assertTrue(os.path.isdir(os.path.join(temp_directory, ".ssh")))

    def test_videos_directory_filenames(self):
        with TemporaryDirectory() as temp_directory:
            videos_path = temp_directory
            self.config_saver.save_videos_directory_filenames(temp_directory, videos_path)
            with open(os.path.join(temp_directory, "videos_tree.txt"), "r") as fin:
                line = fin.readlines()[0]
                self.assertTrue("Folder" in line)

    def test_save_file_associations(self):
        with TemporaryDirectory() as temp_directory:
            self.config_saver.save_file_associations(temp_directory)
            self.assertTrue(
                os.path.exists(os.path.join(temp_directory, "file_associations.txt"))
            )

    def test_save_drivers(self):
        with TemporaryDirectory() as temp_directory:
            self.config_saver.save_drivers(temp_directory)
            with open(os.path.join(temp_directory, "drivers.txt"), "r") as fin:
                line = fin.readlines()[1]
                self.assertTrue("Module Name" in line)

    def test_save_systeminfo(self):
        with TemporaryDirectory() as temp_directory:
            self.config_saver.save_systeminfo(temp_directory)
            with open(os.path.join(temp_directory, "systeminfo.txt"), "r") as fin:
                line = fin.readlines()[1]
                self.assertTrue("Host Name:" in line)

    @unittest.skip("unfinished")
    def test_save_battery_report(self):
        pass


class TestReturnType(unittest.TestCase):
    def setUp(self) -> None:
        self.config_saver = winbackup.systemconfigsaver.SystemConfigSaver()

    def test_command_runner_returns_str(self):
        response = self.config_saver._command_runner(
            ["powershell.exe", "Write-Output", "Test"]
        )
        self.assertTrue(type(response) == str)

    def test_save_config_files_returns_str(self):
        with TemporaryDirectory() as temp_directory:
            null_dev = open(os.devnull, "w")
            sys.stdout = null_dev
            response = self.config_saver.save_config_files(temp_directory)
            sys.stdout = sys.__stdout__
            null_dev.close()
            self.assertTrue(type(response) == str)


if __name__ == "__main__":
    unittest.main(verbosity=2)
