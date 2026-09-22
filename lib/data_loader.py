from tinydb import TinyDB, Query
from discord import Interaction


class Data:
    def __init__(self, path):
        self.db = TinyDB(path, indent=4)

        self.servers = self.db.table("servers")
        self.users = self.db.table("users")
        self.Target = Query()

    def get_data_per_server(self, server_id, default=None):
        if default is None:
            default = {}

        result = self.servers.search(self.Target.id == str(server_id))
        if result:
            return result[0]

        new_data = {"id": str(server_id), **default}
        self.servers.insert(new_data)
        return new_data

    def get_data_per_user(self, user_id, default=None):
        if default is None:
            default = {}

        result = self.users.search(self.Target.id == str(user_id))
        if result:
            return result[0]

        new_data = {"id": str(user_id), **default}
        self.users.insert(new_data)
        return new_data

    def update_server(self, server_id, new_data):
        self.servers.upsert(new_data, self.Target.id == str(server_id))

    def update_user(self, user_id, new_data):
        self.users.upsert(new_data, self.Target.id == str(user_id))

    def get_data(self, interaction: Interaction, default={}):
        if not interaction.guild_id:
            target_id = interaction.user.id
            data = self.get_data_per_user(target_id, default)
            return data, target_id, "user"

        target_id = interaction.guild_id
        data = self.get_data_per_server(target_id, default)
        return data, target_id, "server"

    def save_data(self, data, target_id, target_type):
        if target_type == "server":
            self.update_server(target_id, data)
        else:
            self.update_user(target_id, data)
