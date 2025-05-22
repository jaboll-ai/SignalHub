from enum import Enum

class EngineMode(Enum):
    RUN = 1,
    TERMINATE = 2

class Engine:
    def __init__(self, modules, signals):
        self.modules = modules
        self.signals = signals

        pass

    def run(self, data):
        # Init all module
        for module in self.modules:
            module.start(data)

        # Run till termination
        while True:
            data, mode = self.step(data)

            if mode == EngineMode.TERMINATE:
                break

        # Shutdown all module
        for module in self.modules:
            module.stop(data)

        return data
    
    def _strip_down_input_signal(self, data, inputSignals):
        stripped_data = {}

        if not inputSignals:
            return
        
        for key in inputSignals:
            keys = key.split('.')  # Split the key by dot to handle nested keys
            current_data = data

            # Traverse the nested keys
            for sub_key in keys:
                if sub_key in current_data:
                    current_data = current_data[sub_key]
                else:
                    # If a nested key does not exist, return None or handle error
                    current_data = None
                    break
            
            stripped_data[key] = current_data

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
            if mode ==  EngineMode.RUN:
              module.outputValidator.validate(results)

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
