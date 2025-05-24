import argparse
import yaml
import os
from .module import Module

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def set_nested_key(key, value, dict):
    while True:
        splt = key.split(".")
        if len(splt) == 1:
            dict[key] = value
            return

        if splt[0] not in dict:
            dict[splt[0]] = {}  # Initialisiere das Dictionary, falls nicht vorhanden

        dict = dict[splt[0]]
        key = ".".join(splt[1:])


class ConfigParser(Module):
    def __init__(self, argumentParser=None):
        super().__init__(
            outputSchema={
                "type": "object",
                "properties": {"config": {}},
            },
            name="Argument Parser",
        )

        self.parser = argumentParser or argparse.ArgumentParser()
        self.parser.add_argument(
            "--cfg", action="store", help="Config file to parse", default="config.yml"
        )
        self.config = None
        pass

    def start(self, data):
        # Parse command line arguments into it, just to get the config file
        namespace = self.parser.parse_args()
        self.config = {"config": {}}
        # Get the config file
        cfgFile = namespace.cfg
        if not os.path.exists(cfgFile):
            if cfgFile != "config.yml":
                # logger.error(f"Could not find configuration file {cfgFile}")
                raise FileNotFoundError()
        else:
            with open(cfgFile, "r") as f:
                try:
                    cfg = yaml.safe_load(f)
                    self.config = {"config": cfg}
                except yaml.YAMLError as exc:
                    # logger.error(f"Cannot load configuration file: {exc}")
                    raise exc

        # Parse command line arguments again to (potentially) overwrite the parameters from the configuration file
        args = vars(self.parser.parse_args())
        dct = self.config["config"]
        for key, value in args.items():
            if value is None:
                continue

            set_nested_key(key, value, dct)

        return self.config

    def step(self, data):
        return self.config

    def stop(self, data):
        pass
