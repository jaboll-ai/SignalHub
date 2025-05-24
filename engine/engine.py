from enum import Enum
from .galy import process_galy, remove_galy_streams, make_galy_streams_unique
from .misc import get_nested_key, check_is_signal_is_exclusive
from .galyQT import run_qt_eventloop, qt_quit
from .configparser import ConfigParser  # Replace with the actual module name
from .recorder import Recorder, Replay
from .mode import EngineMode
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
    
    def current(self):
        return self.buffer[self.index]

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
        self.mode = EngineMode.RUN
        self.autoclose = False
        self.exclusiveList = []

    def get_buffer_status_text(self):
        return f"Scan {self.buffer.index + 1} / {self.buffer.len()}"

    def step_backward(self):
        data = self.buffer.step_backward()
        process_galy(data)

    def redraw_galy(self):
        data = self.buffer.current()
        process_galy(data)

    def step_forward(self):
        # If the buffer is at the end, we have to actually step through the modules
        if self.buffer.is_at_end() and self.mode == EngineMode.RUN:
            data, mode = self.step(self.data)
            self.buffer.add_and_move_to_end(data)

            if mode == EngineMode.TERMINATE:
                self.mode = EngineMode.TERMINATE
                if self.autoclose:
                    qt_quit()
        else:
            data = self.buffer.step_forward()

        self.data = process_galy(data)

    def wrap_modules_with_recorder(self, data):
        for module in self.modules:
            if isinstance(module, ConfigParser):
                data = module.start(data)

        mode = get_nested_key("config.mode", data) or None

        if mode == "record":
            record_list = get_nested_key("config.recorder.record", data)
            wrapped_modules = []
            for module in self.modules:
                if module._name in record_list:
                    print(f"Wrapping {module._name} with recorder")
                    wrapped_modules.append(Recorder(module))
                else:
                    wrapped_modules.append(module)

            self.modules = wrapped_modules

        if mode == "replay":
            record_list = get_nested_key("config.recorder.replay", data)
            if record_list is None:
                record_list = get_nested_key("config.recorder.record", data)

            wrapped_modules = []
            for module in self.modules:
                if module._name in record_list:
                    print(f"Wrapping {module._name} with replay")
                    wrapped_modules.append(Replay(module))
                else:
                    wrapped_modules.append(module)

            self.modules = wrapped_modules

    def run(self, data):
        # Wrap modules with recorder or replay modules depending on mode
        self.wrap_modules_with_recorder(data)

        # Init all module
        for module in self.modules:
            if not module.check_initialized():
                logging.critical(
                    f"Module {module._name} did not call super constructor"
                )
                exit()

        # Start all modules
        self.data, _ = self.step(data, True)

        # Extract relevant configuration parameters
        historyBufferSize = get_nested_key("config.engine.history", self.data) or 600
        self.buffer.set_max_size(historyBufferSize)
        self.autoclose = get_nested_key("config.engine.autoclose", self.data) or False

        # Pass execution to QT
        run_qt_eventloop(self, data["config"])

        # Shutdown all module
        print("Shutting down all modules")
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
        # Reset the exclusiv list
        self.exclusiveList = { }

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
                "Module " + module._name + " must return a dictionary!"
            )

            # Validate module output with module output schema (only if we are supposed to run)
            if mode == EngineMode.RUN:
                module.outputValidator.validate(remove_galy_streams(results))

            # Make multiple GALY streams unique names
            results = make_galy_streams_unique(results)    

            # Now make sure we don´t overwrite other signals unless explicitly allowed
            for signal in results.keys():
                if signal in self.exclusiveList.keys():
                    logger.error(
                        f"Module {module._name} must not overwrite exclusive signal {signal} previously written by {self.exclusiveList[signal]}"
                    )
                    exit()
                else:
                    if check_is_signal_is_exclusive(signal, module.outputSchema):
                        self.exclusiveList[signal] = module._name

            # Update the dictionary
            data.update(results)

            # If the module requests termination, stop immediately
            if mode == EngineMode.TERMINATE:
                return data, EngineMode.TERMINATE

        return data, EngineMode.RUN
