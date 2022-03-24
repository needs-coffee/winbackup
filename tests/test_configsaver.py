#!/usr/bin/env python3

##
## tests for configsaver module
##

import unittest
import os
import winbackup.configsaver


class TestValidReturnValue(unittest.TestCase):

    def setUp(self) -> None:
        self.config_saver = winbackup.configsaver.ConfigSaver()


    def test_command_runner(self):
        response = self.config_saver._command_runner(['powershell.exe', 'Write-Output', 'Test']).strip()
        self.assertTrue(response == 'Test')

    def test_set_videos_directory_path(self):
        test_path = 'C:/Users'
        self.config_saver.set_videos_directory_path(test_path)
        self.assertTrue(self.config_saver.videos_path == test_path)

    def test_save_config_files(self):
        temp_path = ''
        response = self.config_saver.save_config_files(temp_path)


class TestReturnType(unittest.TestCase):

    def setUp(self) -> None:
        self.config_saver = winbackup.configsaver.ConfigSaver()


    def test_command_runner_returns_str(self):
        self.assertTrue(type(self.config_saver._command_runner(['powershell.exe', 'Write-Output', 'Test'])) == str)




if __name__ == '__main__':
    unittest.main(verbosity=2)

