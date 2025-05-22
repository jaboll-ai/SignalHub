import jsonschema
import jsonschema.validators

class Module:
    def __init__(self, inputSignals = None, outputSchema = None):
        self._initialized = True

        if outputSchema is None:
          outputSchema = {
            "type" : "object",
            "properties": { },
            "additionalProperties": False
          }

        if outputSchema is not None:
          # One special case: If you do not explicitly specify that you allow additional properties, do not allow them (reverse default in JSON schema validators, only on top level)
          if "type" in outputSchema and outputSchema["type"] == "object":
             if not "additionalProperties" in outputSchema:
                outputSchema["additionalProperties"] = False

          self.outputValidator = jsonschema.validators.Draft202012Validator(outputSchema)
        
        self.inputSignals = inputSignals
        
        pass
    
    def check_initialized(self):
      if not getattr(self, '_initialized', False):
        return False
      
      return True

    def start(self, data):
        pass

    def step(self, data):
        pass

    def stop(self, data):
        pass
