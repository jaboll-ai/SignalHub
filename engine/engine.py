from enum import Enum
from .galy import process_galy, remove_galy_streams
from .misc import get_nested_key
from .galyQT import run_qt_eventloop, qt_quit

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EngineMode(Enum):
    RUN = (1,)
    TERMINATE = 2


class Engine:
    def __init__(self, modules, signals):
        self.modules = modules
        self.signals = signals

        pass
    
    def _step_callback_from_qt(self):
         data, mode = self.step(self.data)

         if mode == EngineMode.TERMINATE:
             qt_quit()             

         self.data = process_galy(data)

    def run(self, data):
        # Init all module
        for module in self.modules:
            if not module.check_initialized():
                logging.critical(f"Module {module.name} did not call super constructor")
                exit()

            module.start(data)

        # Pass execution to QT
        self.data = data
        run_qt_eventloop(self._step_callback_from_qt)

        # Shutdown all module
        for module in self.modules:
            module.stop(data)

        return data

    def _strip_down_input_signal(self, data, inputSignals):
        stripped_data = {}

        if not inputSignals:
            return

        for key in inputSignals:
            stripped_data[key] = get_nested_key(key, data)

        return stripped_data

    def step(self, data):
        # Iterate all modules
        for module in self.modules:
            # Only present the requested data to this module
            stripped_data = self._strip_down_input_signal(data, module.inputSignals)

            # Run a single step of the module
            results = module.step(stripped_data)

            # If we received a tuple, unpack it first. Otherwise we have just received results (for convenience)
            if type(results) is tuple:
                results, mode = results
            else:
                mode = EngineMode.RUN

            # Validate module output with module output schema (only if we are supposed to run)
            if mode == EngineMode.RUN:
                module.outputValidator.validate(remove_galy_streams(results))

            # Verify its result
            # TODO: Use JSON Schema validation here
            assert type(results) is dict, (
                "Module " + module.name + " must return a dictionary!"
            )

            # Update the dictionary
            data.update(results)

            # If the module requests termination, stop immediately
            if mode == EngineMode.TERMINATE:
                return data, EngineMode.TERMINATE

        return data, EngineMode.RUN
