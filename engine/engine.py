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


class DataBuffer:
    def __init__(self):
        self.buffer = []
        self.index = 0
        self.max_size = 600

    def set_max_size(self, sz):
        self.max_size = sz

    def add_and_move_to_end(self, data):
        if len(self.buffer) >= self.max_size:
            self.buffer.pop(0)

        self.buffer.append(data)
        self.index = len(self.buffer) - 1
        


    def is_at_end(self):
        if len(self.buffer) == 0:
            return True
        
        return self.index == len(self.buffer) - 1

    def step_forward(self):
        if self.index < len(self.buffer) - 1:
            self.index += 1

        return self.buffer[self.index]

    def step_backward(self):
        if self.index > 0:
            self.index -= 1

        return self.buffer[self.index]

    def len(self):
        return len(self.buffer)

class Engine:
    def __init__(self, modules, signals):
        self.modules = modules
        self.signals = signals

        self.buffer = DataBuffer()

    def get_buffer_status_text(self):
        return f"Scan {self.buffer.index + 1} / {self.buffer.len()}"

    def step_backward(self):
        data = self.buffer.step_backward()
        process_galy(data)

    def step_forward(self):
        # If the buffer is at the end, we have to actually step through the modules
        if self.buffer.is_at_end():
            data, mode = self.step(self.data)
            self.buffer.add_and_move_to_end(data)

            if mode == EngineMode.TERMINATE:
                qt_quit()
        else:
            data = self.buffer.step_forward()

        self.data = process_galy(data)

    def run(self, data):
        # Init all module
        for module in self.modules:
            if not module.check_initialized():
                logging.critical(f"Module {module.name} did not call super constructor")
                exit()

        # Start all modules
        self.data, _ = self.step(data, True)
        historyBufferSize = get_nested_key("config.engine.history", self.data) or 600
        self.buffer.set_max_size(historyBufferSize)

        # Pass execution to QT
        run_qt_eventloop(self, data["config"])

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

    def step(self, data, start=False):
        # Iterate all modules
        for module in self.modules:
            # Only present the requested data to this module
            stripped_data = self._strip_down_input_signal(data, module.inputSignals)

            # Run a single step of the module
            if start:
                results = module.start(stripped_data)
            else:
                results = module.step(stripped_data)

            # If we received a tuple, unpack it first. Otherwise we have just received results (for convenience)
            if type(results) is tuple:
                results, mode = results
            else:
                mode = EngineMode.RUN

            # Verify its result
            # TODO: Use JSON Schema validation here
            assert type(results) is dict, (
                "Module " + module.name + " must return a dictionary!"
            )

            # Validate module output with module output schema (only if we are supposed to run)
            if mode == EngineMode.RUN:
                module.outputValidator.validate(remove_galy_streams(results))

            # Update the dictionary
            data.update(results)

            # If the module requests termination, stop immediately
            if mode == EngineMode.TERMINATE:
                return data, EngineMode.TERMINATE

        return data, EngineMode.RUN
