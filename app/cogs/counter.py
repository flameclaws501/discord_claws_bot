import json
import os

counter_file = "counter.json"


def get_count(key):
    if not os.path.exists(counter_file):
        return 0
    with open(counter_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get(key, 0)


def update_count(key, value):
    data = {}
    if os.path.exists(counter_file):
        with open(counter_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    data[key] = value
    with open(counter_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
