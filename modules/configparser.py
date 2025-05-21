import argparse
import yaml
import os

def set_nested_key(key, value, dict):
  while True:
    splt = key.split('.')
    if len(splt) == 1:
      dict[key] = value
      return
    
    dict = dict[splt[0]]
    key = ".".join(splt[1:])

class ConfigParser():
  def __init__(self, argumentParser = None):
    self.name = "Argument Parser"
    self.parser = argumentParser or argparse.ArgumentParser()
    self.parser.add_argument("--cfg", action="store", help="Config file to parse", default="config.yml")
    self.config = None
    pass

  def start(self, data):
    # Start with an empty namespace
    self.config = { "config": argparse.Namespace() }

    # Parse command line arguments into it, just to get the config file
    self.parser.parse_args(namespace=self.config["config"])

    cfgFile = self.config["config"].cfg
    if not os.path.exists(cfgFile):
      if cfgFile != "config.yml":
        print(f"Could not file configuration file {cfgFile}")
        exit()
    else:
      with open(cfgFile) as f:
        try:
          cfg = yaml.safe_load(f)
          self.config = { "config": argparse.Namespace(**cfg) }
        except yaml.YAMLError as exc:
          print(exc)
          exit()

    # Parse command line arguments again to (potentially) overwrite the parameters from the configuration file
    args = vars(self.parser.parse_args())
    dct = vars(self.config["config"])
    for key, value in args.items():
      if value is None:
        continue
      
      set_nested_key(key, value, dct)
    
    self.config["config"] = argparse.Namespace(**dct)

  def step(self, data):
    return self.config

  def stop(self, data):
    pass