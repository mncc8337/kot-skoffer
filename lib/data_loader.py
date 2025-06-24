import json
import os


class Data:
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

    def get_data_per_server(self, server_id, default={}):
        if not self.data.get(str(server_id)):
            self.data[str(server_id)] = default
        return self.data[str(server_id)]
