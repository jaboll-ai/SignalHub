from re import sub
import jsonschema
import jsonschema.validators


def camelCase(s):
    s = sub(r"(_|-)+", " ", s).title().replace(" ", "")
    return "".join([s[0].lower(), s[1:]])


module_name_counter = {}


def make_unique(name):
    # First, make the name camel case
    name = camelCase(name)

    # Now make it unique by attaching a number
    if name not in module_name_counter.keys():
        module_name_counter[name] = 1
        return name
    else:
        module_name_counter[name] += 1
        return name + f"_{module_name_counter[name]}"


class Module:
    def __init__(self, inputSignals=None, outputSchema=None, name=None):
        self._name = make_unique(name or self.__class__.__name__)

        self._initialized = True

        if outputSchema is None:
            outputSchema = {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            }

        if outputSchema is not None:
            # One special case: If you do not explicitly specify that you allow additional properties, do not allow them (reverse default in JSON schema validators, only on top level)
            if "type" in outputSchema and outputSchema["type"] == "object":
                if not "additionalProperties" in outputSchema:
                    outputSchema["additionalProperties"] = False

            self.outputValidator = jsonschema.validators.Draft202012Validator(
                outputSchema
            )

        self.outputSchema = outputSchema
        self.inputSignals = inputSignals

        pass

    def check_initialized(self):
        if not getattr(self, "_initialized", False):
            return False

        return True

    def start(self, data):
        return { }

    def step(self, data):
        return { }

    def stop(self, data):
        return { }
