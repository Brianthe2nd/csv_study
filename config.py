import json
import os

CONFIG_PATH = "config.json"

def get_config(key=None, default=None):
    """
    Reads config.json and returns the full dict or a specific key's value.
    If the file doesn't exist it creates it.
    If the key is missing, returns default.
    """

    # Ensure the file exists
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump({}, f)

    # Try to read the file
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {}
            with open(CONFIG_PATH, "w", encoding="utf-8") as fw:
                json.dump(data, fw)

    if key is None:
        return data
    else:
        return data.get(key, default)



def update_config(key, value=None ,default=None):
    """
    Updates config.json.
    - If data_or_key is a dict, merges it into the config.
    - If data_or_key is a key (str) and value is provided, updates that key.
    """
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                return default if key else {}

    data[key] = value

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


if __name__ == "__main__":
    update_config({"mode": "test", "retry_count": 3})
    update_config("last_value", 42)
    print(get_config())
    print(get_config("last_value"))
