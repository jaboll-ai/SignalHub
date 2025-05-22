def get_nested_key(key, data):
    keys = key.split(".")  # Split the key by dot to handle nested keys
    current_data = data

    # Traverse the nested keys
    for sub_key in keys:
        if sub_key in current_data:
            current_data = current_data[sub_key]
        else:
            # If a nested key does not exist, return None or handle error
            current_data = None
            break

    return current_data
