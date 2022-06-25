#!/usr/bin/env python3

##
## tests for configagent module
##

import unittest
import os
from tempfile import TemporaryDirectory
import winbackup.configagent
import winbackup.windowspaths


class TestValidOutput(unittest.TestCase):
    def setUp(self) -> None:
        self.config_agent = winbackup.configagent.ConfigAgent()
        self.windows_paths = winbackup.windowspaths.WindowsPaths()

    def test_update_config_paths(self):
        response = self.config_agent.update_config_paths(self.windows_paths.get_paths())
        self.assertTrue(type(response["10_documents"]["path"]) == str)

    def test_add_item_key_inserted(self):
        test_item = {
            "name": "TESTITEM",
            "type": "folder",
            "path": "./testpath",
            "dict_size": "192m",
        }
        response = self.config_agent.add_item("99_testitem", test_item)
        self.assertTrue(response["99_testitem"])

    def test_add_item_key_has_expected_path(self):
        test_item = {
            "name": "TESTITEM",
            "type": "folder",
            "path": "./testpath",
            "dict_size": "192m",
        }
        response = self.config_agent.add_item("99_testitem", test_item)
        self.assertTrue(response["99_testitem"]["path"] == "./testpath")

    def test_add_item_raises_typeerror_on_invalid_key_type(self):
        test_item = {
            "name": "TESTITEM",
            "type": "folder",
            "path": "./testpath",
            "dict_size": "192m",
        }
        with self.assertRaises(TypeError):
            self.config_agent.add_item(99, test_item)

    def test_add_item_raises_typeerror_on_invalid_value_type(self):
        test_item = "testinvalid"
        with self.assertRaises(TypeError):
            self.config_agent.add_item("99_testitem", test_item)

    def test_add_item_raises_valueerror_with_invalid_configitem_key(self):
        test_item = {
            "name": "TESTITEM",
            "type": "folder",
            "path": "./testpath",
            "dict_size": "192m",
            "notallowed": "notallowed",
        }
        with self.assertRaises(ValueError):
            self.config_agent.add_item("99_testitem", test_item)

    def test_add_item_raises_valueerror_with_invalid_configitemid(self):
        test_item = {
            "name": "TESTITEM",
            "type": "folder",
            "path": "./testpath",
            "dict_size": "192m",
        }
        with self.assertRaises(ValueError):
            self.config_agent.add_item("invalidtestitemid", test_item)

    def test_add_item_raises_valueerror_with_no_item_name(self):
        test_item = {
            "name": None,
            "type": "folder",
            "path": "./testpath",
            "dict_size": "192m",
        }
        with self.assertRaises(ValueError):
            self.config_agent.add_item("99_testitem", test_item)

    def test_add_item_raises_valueerror_with_no_item_path(self):
        test_item = {
            "name": "TESTITEM",
            "type": "folder",
            "path": None,
            "dict_size": "192m",
        }
        with self.assertRaises(ValueError):
            self.config_agent.add_item("99_testitem", test_item)

    def test_get_target_config_returns_config(self):
        response = self.config_agent.get_target_config()
        self.assertTrue(response["10_documents"]["name"] == "Documents")

    def test_get_global_config_returns_config(self):
        response = self.config_agent.get_global_config()
        self.assertTrue(response["encryption_enabled"] is False)

    def test_get_output_root_path(self):
        response = self.config_agent.get_output_root_path()
        self.assertTrue(response == self.config_agent._global_config["output_root_dir"])

    def test_get_encryption_password(self):
        response = self.config_agent.get_encryption_password()
        self.assertTrue(response == self.config_agent._global_config["encryption_password"])

    def test_set_encryption_password(self):
        self.config_agent.set_encryption_password("Testpassword")
        response = self.config_agent.get_encryption_password()
        self.assertTrue(response == "Testpassword")

    def test_validate_target_config(self):
        test_config = {
            "01_config": {
                "name": "System Config",
                "type": "special",
                "path": None,
                "enabled": False,
                "dict_size": "192m",
                "mx_level": 9,
                "full_path": False,
            },
            "10_documents": {
                "name": "Documents",
                "type": "folder",
                "path": ".",
                "enabled": False,
                "dict_size": "192m",
                "mx_level": 9,
                "full_path": False,
            },
        }
        self.assertTrue(self.config_agent.validate_target_config(test_config))

    def test_validate_target_config_invalid_target_id(self):
        test_config = {
            "invalidconfigid": {
                "name": "System Config",
                "type": "special",
                "path": None,
                "enabled": False,
                "dict_size": "192m",
                "mx_level": 9,
                "full_path": False,
            },
            "10_documents": {
                "name": "Documents",
                "type": "folder",
                "path": ".",
                "enabled": False,
                "dict_size": "192m",
                "mx_level": 9,
                "full_path": False,
            },
        }
        self.assertFalse(self.config_agent.validate_target_config(test_config))

    def test_validate_target_config_invalid_target_invalid_configitem_key(self):
        test_config = {
            "01_config": {
                "name": "System Config",
                "type": "special",
                "path": None,
                "enabled": False,
                "dict_size": "192m",
                "mx_level": 9,
                "full_path": False,
            },
            "10_documents": {
                "namesinvalid": "Documents",
                "type": "folder",
                "path": ".",
                "enabled": False,
                "dict_size": "192m",
                "mx_level": 9,
                "full_path": False,
            },
        }
        self.assertFalse(self.config_agent.validate_target_config(test_config))

    def test_validate_target_config_invalid_target_invalid_mxlevel(self):
        test_config = {
            "01_config": {
                "name": "System Config",
                "type": "special",
                "path": None,
                "enabled": False,
                "dict_size": "192m",
                "mx_level": 9,
                "full_path": False,
            },
            "10_documents": {
                "name": "Documents",
                "type": "folder",
                "path": ".",
                "enabled": False,
                "dict_size": "192m",
                "mx_level": 99,
                "full_path": False,
            },
        }
        self.assertFalse(self.config_agent.validate_target_config(test_config))

    def test_validate_target_config_invalid_target_invalid_dictsize(self):
        test_config = {
            "01_config": {
                "name": "System Config",
                "type": "special",
                "path": None,
                "enabled": False,
                "dict_size": "192m",
                "mx_level": 9,
                "full_path": False,
            },
            "10_documents": {
                "name": "Documents",
                "type": "folder",
                "path": ".",
                "enabled": False,
                "dict_size": "xx192m",
                "mx_level": 99,
                "full_path": False,
            },
        }
        self.assertFalse(self.config_agent.validate_target_config(test_config))

    def test_validate_target_config_invalid_target_path(self):
        test_config = {
            "01_config": {
                "name": "System Config",
                "type": "special",
                "path": None,
                "enabled": False,
                "dict_size": "192m",
                "mx_level": 9,
                "full_path": False,
            },
            "10_documents": {
                "name": "Documents",
                "type": "folder",
                "path": None,
                "enabled": False,
                "dict_size": "192m",
                "mx_level": 99,
                "full_path": False,
            },
        }
        self.assertFalse(self.config_agent.validate_target_config(test_config))

    def test_validate_target_config_blank_config(self):
        self.assertFalse(self.config_agent.validate_target_config())

    def test_validate_global_config(self):
        test_config = {
            "encryption_enabled": False,
            "encryption_password": "",
            "output_root_dir": ".",
        }
        self.assertTrue(self.config_agent.validate_global_config(test_config))

    def test_validate_global_config_invalid_missing_required(self):
        test_config = {
            "encryption_enabled": False,
            "encryption_password": "",
        }
        self.assertFalse(self.config_agent.validate_global_config(test_config))

    def test_validate_global_config_invalid_value(self):
        test_config = {
            "encryption_enabled": False,
            "encryption_password": 99,
            "output_root_dir": ".",
        }
        self.assertFalse(self.config_agent.validate_global_config(test_config))

    def test_validate_global_config_invalid_output_path(self):
        test_config = {
            "encryption_enabled": False,
            "encryption_password": "test",
            "output_root_dir": "./fake",
        }
        self.assertFalse(self.config_agent.validate_global_config(test_config))

    def test_validate_global_config_blank_config(self):
        self.assertFalse(self.config_agent.validate_global_config())

    def test_save_YAML_config(self):
        with TemporaryDirectory() as temp_directory:
            response = self.config_agent.save_YAML_config(
                os.path.join(temp_directory, "test.yaml")
            )

            with self.subTest(msg="config path is real path"):
                self.assertTrue(os.path.isfile(response))
            with self.subTest(msg="test file has expected content"):
                with open(response, "r") as fin:
                    read_string = fin.read()
                    self.assertTrue("backup_targets" in read_string)

    def test_save_YAML_config_invalid_given_directory(self):
        with TemporaryDirectory() as temp_directory:
            with self.assertRaises(IsADirectoryError):
                self.config_agent.save_YAML_config(os.path.join(temp_directory))

    def test_save_YAML_config_invalid_extension(self):
        with TemporaryDirectory() as temp_directory:
            with self.assertRaises(ValueError):
                self.config_agent.save_YAML_config(
                    os.path.join(temp_directory, "test.invalid")
                )

    def test_parse_YAML_config(self):
        test_config = {
            "01_config": {
                "name": "System Config",
                "type": "special",
                "path": None,
                "enabled": False,
                "dict_size": "192m",
                "mx_level": 9,
                "full_path": False,
            },
            "10_documents": {
                "name": "Documents",
                "type": "folder",
                "path": ".",
                "enabled": False,
                "dict_size": "192m",
                "mx_level": 9,
                "full_path": False,
            },
        }
        with TemporaryDirectory() as temp_directory:
            save_path = self.config_agent.save_YAML_config(
                os.path.join(temp_directory, "test.yaml"), test_config
            )
            global_config, target_config = self.config_agent.parse_YAML_config_file(save_path)
        with self.subTest("test globalconfig"):
            self.assertTrue(global_config["encryption_enabled"] is False)
        with self.subTest("test targetconfig"):
            self.assertTrue(target_config["10_documents"]["type"] == "folder")


class TestReturnType(unittest.TestCase):
    def setUp(self) -> None:
        self.config_agent = winbackup.configagent.ConfigAgent()
        self.windows_paths = winbackup.windowspaths.WindowsPaths()

    def test_update_config_paths_returns_dict(self):
        response = self.config_agent.update_config_paths(self.windows_paths.get_paths())
        self.assertTrue(type(response) == dict)

    def test_update_config_paths_returns_nested_dict(self):
        response = self.config_agent.update_config_paths(self.windows_paths.get_paths())
        for k, v in response.items():
            with self.subTest(f"test {k} config_item is dict"):
                self.assertTrue(type(v) == dict)

    def test_add_item_returns_dict(self):
        test_item = {
            "name": "TESTITEM",
            "type": "folder",
            "path": "./testpath",
            "dict_size": "192m",
        }
        response = self.config_agent.add_item("99_test", test_item)
        self.assertTrue(type(response) == dict)

    def test_get_target_config_returns_dict(self):
        response = self.config_agent.get_target_config()
        self.assertTrue(type(response) == dict)

    def test_get_global_config_returns_dict(self):
        response = self.config_agent.get_global_config()
        self.assertTrue(type(response) == dict)

    def test_get_output_root_path_returns_str(self):
        response = self.config_agent.get_output_root_path()
        self.assertTrue(type(response) == str)

    def test_set_output_root_path_returns_dict(self):
        response = self.config_agent.set_output_root_path("./test")
        self.assertTrue(type(response) == dict)

    def test_get_encryption_password_returns_str(self):
        response = self.config_agent.get_encryption_password()
        self.assertTrue(type(response) == str)

    def test_set_encryption_password_path_returns_dict(self):
        response = self.config_agent.set_encryption_password("test")
        self.assertTrue(type(response) == dict)

    def test_validate_target_config_returns_bool(self):
        test_config = {
            "01_config": {
                "name": "System Config",
                "type": "special",
                "path": None,
                "enabled": False,
                "dict_size": "192m",
                "mx_level": 9,
                "full_path": False,
            },
            "10_documents": {
                "name": "Documents",
                "type": "folder",
                "path": ".",
                "enabled": False,
                "dict_size": "192m",
                "mx_level": 9,
                "full_path": False,
            },
        }
        response = self.config_agent.validate_target_config(test_config)
        self.assertTrue(type(response) == bool)

    def test_validate_global_config_returns_bool(self):
        test_config = {
            "encryption_enabled": False,
            "encryption_password": "",
            "output_root_dir": ".",
        }
        response = self.config_agent.validate_global_config(test_config)
        self.assertTrue(type(response) == bool)

    def test_save_YAML_config_returns_str(self):
        test_config = {
            "01_config": {
                "name": "System Config",
                "type": "special",
                "path": None,
                "enabled": False,
                "dict_size": "192m",
                "mx_level": 9,
                "full_path": False,
            },
            "10_documents": {
                "name": "Documents",
                "type": "folder",
                "path": ".",
                "enabled": False,
                "dict_size": "192m",
                "mx_level": 9,
                "full_path": False,
            },
        }
        with TemporaryDirectory() as temp_directory:
            response = self.config_agent.save_YAML_config(
                os.path.join(temp_directory, "test.yaml"), test_config
            )
        self.assertTrue(type(response) == str)

    def test_parse_YAML_config_returns_tuple_of_dicts(self):
        test_config = {
            "01_config": {
                "name": "System Config",
                "type": "special",
                "path": None,
                "enabled": False,
                "dict_size": "192m",
                "mx_level": 9,
                "full_path": False,
            },
            "10_documents": {
                "name": "Documents",
                "type": "folder",
                "path": ".",
                "enabled": False,
                "dict_size": "192m",
                "mx_level": 9,
                "full_path": False,
            },
        }
        with TemporaryDirectory() as temp_directory:
            path = self.config_agent.save_YAML_config(
                os.path.join(temp_directory, "test.yaml"), test_config
            )
            response = self.config_agent.parse_YAML_config_file(path)
        with self.subTest("test is tuple"):
            self.assertTrue(type(response) == tuple)
        for item in response:
            with self.subTest("check items are dicts"):
                self.assertTrue(type(item) == dict)


if __name__ == "__main__":
    unittest.main(verbosity=2)
