from re import sub
import os
import pickle
from .misc import get_nested_key
from .module import Module
from .mode import EngineMode

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def camelCase(s):
    s = sub(r"(_|-)+", " ", s).title().replace(" ", "")
    return "".join([s[0].lower(), s[1:]])


open_recorder = []
global_ledger = {}


class Replay(Module):
    def __init__(self, childModule):
        super().__init__(
            inputSignals=childModule.inputSignals,
            outputSchema=childModule.outputSchema,
            name=f"Replay ({childModule._name})",
        )
        self.child = childModule
        self.moduleName = camelCase(childModule._name)

    def start(self, data):
        global open_recorder, global_ledger
        if not open_recorder:
            fileName = get_nested_key("config.recorder.file", data) or "default.pickle"

            with open(fileName, "rb") as f:
                global_ledger = pickle.load(f)

        if self.moduleName not in global_ledger:
            logger.critical(
                f"Cannot replay module {self.child._name} as it was not serialized into provided file."
            )
            exit()

        self.currentIndex = 1
        return global_ledger[self.moduleName][0]

    def step(self, data):
        global open_recorder, global_ledger
        if self.currentIndex < len(global_ledger[self.moduleName]) - 1:
            result = global_ledger[self.moduleName][self.currentIndex]
        else:
            result = {}
        self.currentIndex += 1

        if self.currentIndex == len(global_ledger[self.moduleName]) - 1:
            return result, EngineMode.TERMINATE

        return result

    def stop(self, data):
        return global_ledger[self.moduleName][-1]


class Recorder(Module):
    def __init__(self, childModule):
        super().__init__(
            inputSignals=childModule.inputSignals,
            outputSchema=childModule.outputSchema,
            name=f"Recorder ({childModule._name})",
        )
        self.child = childModule

    def start(self, data):
        global global_ledger, open_recorder

        self.moduleName = camelCase(self.child._name)

        global_ledger[self.moduleName] = []
        open_recorder.append(self)

        result = self.child.start(data)
        global_ledger[self.moduleName].append(result)
        return result

    def step(self, data):
        global global_ledger
        result = self.child.step(data)

        global_ledger[self.moduleName].append(result)

        return result

    def stop(self, data):
        global open_recorder, global_ledger

        # Remove ourselves from the list of open records
        open_recorder.remove(self)

        fileName = get_nested_key("config.recorder.file", data) or "default.pickle"

        result = self.child.stop(data)
        global_ledger[self.moduleName].append(result)

        # If there is none left (we were the last), store the global ledger
        if not open_recorder:
            directory = os.path.dirname(
                fileName
            )  # Extract the directory part of the path
            if not os.path.exists(directory):
                os.makedirs(
                    directory, exist_ok=True
                )  # Create all intermediate directories

            print("Writing global ledger to ", fileName)
            with open(fileName, "wb") as f:
                pickle.dump(global_ledger, f)

        return result
