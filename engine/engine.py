from enum import Enum
from .galy import process_galy

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

            data = process_galy(data)

        # Shutdown all module
        for module in self.modules:
            module.stop(data)

        return data

    def step(self, data):
        # Iterate all modules
        for module in self.modules:
            # Run a single step of the module
            results = module.step(data)

            # If we received a tuple, unpack it first. OLtherwise we have just received results (for convenience)
            if type(results) is tuple:
                results, mode = results
            else:
                mode = EngineMode.RUN

            # Verify its result
            # TODO: Use JSON Schema validation here
            assert type(results) is dict, (
                "Module " + module.name + " must return a dictionary!"
            )

            # Verify results
            for signal, value in results.items():
                # if signal in self.signals:
                #     verifier = self.signals[signal]
                #     if type(verifier) is type:
                #         if type(results[signal]) is not verifier:
                #             print(
                #                 "Cannot verify result of module",
                #                 module.name,
                #                 "on signal",
                #                 signal,
                #             )
                #             print("Expected type", verifier, "on signal", signal)

                #     try:
                #         verifier(results[signal])
                #     except AssertionError as e:
                #         print(
                #             "Cannot verify result of module",
                #             module.name,
                #             "on signal",
                #             signal,
                #         )
                #         print(e)
                #         exit()

                data[signal] = results[signal]

            # If the module requests termination, stop immediately
            if mode == EngineMode.TERMINATE:
              return data, EngineMode.TERMINATE

        return data, EngineMode.RUN
