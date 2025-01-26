import json
import os
from typing import Dict

class Data:
    filepath: str = ""
    data: Dict = {}

    def __init__(self, path):
        self.filepath = path
        if not os.path.exists(path):
            with open(path, "w") as f:
                f.write("{}")

        self.load()

    def save(self):
        with open(self.filepath, "w") as f:
            f.write(json.dumps(self.data, indent=4))

    def load(self):
        with open(self.filepath, "r") as f:
            self.data = json.load(f)
