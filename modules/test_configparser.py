import unittest
from unittest.mock import patch, MagicMock
import argparse
import yaml
import os
from io import StringIO
from configparser import ConfigParser, set_nested_key
import logging

class MockedArgumentParser:
    def __init__(self, retVal):
        self.retVal = retVal

    def add_argument(self, *args, **kwargs):
        pass

    def parse_args(self, **kwargs):
        return self.retVal


class TestConfigParser(unittest.TestCase):
    @patch("builtins.open", new_callable=MagicMock)
    @patch("os.path.exists", return_value=True)
    @patch("yaml.safe_load")
    def test_start_with_valid_config(self, mock_yaml_load, mock_exists, mock_open):
        # Mocking the content of the YAML file
        mock_yaml_load.return_value = {"key1": "value1", "nested": {"key2": "value2"}}

        config_parser = ConfigParser(
            argumentParser=MockedArgumentParser(argparse.Namespace(cfg="config.yml"))
        )

        # Call start method with mock arguments
        config_parser.start(None)

        # Verify that the YAML file was opened
        mock_open.assert_called_once_with("config.yml", "r")
        # Verify yaml.safe_load was called
        mock_yaml_load.assert_called_once()

        # Verify file it checked for existence
        mock_exists.assert_called_once()

        # Assert that the config is updated with the parsed data
        self.assertEqual(config_parser.config["config"]["key1"], "value1")
        self.assertEqual(config_parser.config["config"]["nested"]["key2"], "value2")

    @patch("builtins.open", new_callable=MagicMock)
    @patch("os.path.exists", return_value=False)
    def test_start_with_missing_file(self, mock_exists, mock_open):
        # Set up mock to simulate a missing config file
        mock_open.side_effect = FileNotFoundError
        config_parser = ConfigParser(argumentParser=MockedArgumentParser(argparse.Namespace(cfg="other.yml")))

        # Catch the exit due to file not found
        with self.assertRaises(FileNotFoundError):
          config_parser.start(None)

    def test_set_nested_key(self):
        # Test that the value is set in the nested structure
        dct = {}
        set_nested_key("nested.key3", "new_value", dct)

        # Assert that the new value is correctly added to the nested structure
        self.assertEqual(dct["nested"]["key3"], "new_value")

    @patch("builtins.open", new_callable=MagicMock)
    @patch("os.path.exists", return_value=True)
    @patch("yaml.safe_load")
    def test_command_line_argument_overwrite(self, mock_yaml_load, mock_exists, mock_open):
        # Mock YAML content
        mock_yaml_load.return_value = {
            "key1": "value1",
            "key2": "value2"
        }

        config_parser = ConfigParser(argumentParser=MockedArgumentParser(argparse.Namespace(cfg="config.yml", key1="new_value")))
        config_parser.start(None)

        # Verify the overwritten value from command line args
        self.assertEqual(config_parser.config["config"]["key1"], "new_value")
        # Verify the key2 value remains the same from the YAML
        self.assertEqual(config_parser.config["config"]["key2"], "value2")


if __name__ == "__main__":
    unittest.main()
