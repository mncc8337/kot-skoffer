from discord import Interaction
import random

import lib.data_loader as data_loader


class LuckyWheel(data_loader.Data):
    def __init__(self, *args):
        super().__init__(*args)

    async def spin(self, interaction: Interaction):
        server_data = self.get_data_per_server(
            interaction.guild_id,
            {"user": {}, "item": {}},
        )
        if len(server_data["item"].keys()) < 2:
            await interaction.response.send_message("not enough item to spin")
            return

        item = random.choice(list(server_data["item"].keys()))

        if str(interaction.user.id) in server_data["user"].keys():
            server_data["user"][str(interaction.user.id)]["point"] += server_data["item"][item]
        else:
            server_data["user"][str(interaction.user.id)] = {
                "name": interaction.user.name,
                "point": server_data["item"][item],
            }

        await interaction.response.send_message(f"{interaction.user.mention} got {item}, value {server_data["item"][item]} points")

    def add(self, key: str, val: int, server_id):
        server_data = self.get_data_per_server(
            server_id,
            {"user": {}, "item": {}},
        )
        server_data["item"][key] = val

    def remove(self, key: str, server_id):
        server_data = self.get_data_per_server(
            server_id,
            {"user": {}, "item": {}},
        )
        server_data["item"].pop(key)

    async def list(self, interaction: Interaction):
        server_data = self.get_data_per_server(
            interaction.guild_id,
            {"user": {}, "item": {}},
        )
        msg = ""

        for item in server_data["item"].keys():
            msg += f"{item}: {server_data["item"][item]}\n"

        if msg != "":
            await interaction.response.send_message(msg)
        else:
            await interaction.response.send_message("no item")

    async def user(self, interaction: Interaction):
        server_data = self.get_data_per_server(
            interaction.guild_id,
            {"user": {}, "item": {}},
        )
        l = []
        for user in server_data["user"].keys():
            l.append((
                server_data["user"][user]["point"],
                server_data["user"][user]["name"]
            ))
        l.sort()

        msg = ""

        for pair in l:
            msg += f"{pair[1]}: {pair[0]}\n"

        if msg != "":
            await interaction.response.send_message(msg)
        else:
            await interaction.response.send_message("no user")
