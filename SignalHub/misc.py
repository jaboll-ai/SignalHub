def get_nested_key(key, data, default=None):
    keys = key.split(".")  # Split the key by dot to handle nested keys
    current_data = data

    # Traverse the nested keys
    for sub_key in keys:
        if sub_key in current_data:
            current_data = current_data[sub_key]
        else:
            # If a nested key does not exist, return None or handle error
            current_data = default
            break

    return current_data


def check_is_signal_is_exclusive(signal, schema):
    if not isinstance(schema, dict):
        return True

    if schema.get("type") != "object":
        return True

    properties = schema.get("properties")
    if properties is None:
        return True

    if not isinstance(properties, dict):
        return True

    signalSchema = properties.get(signal)
    if signalSchema is None:
        return True

    if not isinstance(signalSchema, dict):
        return True

    return signalSchema.get("exclusive", True)
