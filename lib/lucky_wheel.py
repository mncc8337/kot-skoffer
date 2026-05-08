from discord import Interaction
import random

import lib.data_loader as data_loader


class LuckyWheel(data_loader.Data):
    def __init__(self, *args):
        super().__init__(*args)

    async def spin(self, interaction: Interaction):
        local_data = self.get_data(interaction)
        if len(local_data["item"].keys()) < 2:
            await interaction.response.send_message("not enough item to spin")
            return

        item = random.choice(list(local_data["item"].keys()))

        usr_id_str = str(interaction.user.id)

        if str(interaction.user.id) in local_data["user"].keys():
            local_data["user"][usr_id_str]["point"] += local_data["item"][item]
        else:
            local_data["user"][usr_id_str] = {
                "name": interaction.user.name,
                "point": local_data["item"][item],
            }

        await interaction.response.send_message(f"{interaction.user.mention} got {item}, value {local_data["item"][item]} points")

    def add(self, key: str, val: int, interaction: Interaction):
        local_data = self.get_data(interaction)
        local_data["item"][key] = val

    def remove(self, key: str, interaction: Interaction):
        local_data = self.get_data(interaction)
        local_data["item"].pop(key)

    async def list(self, interaction: Interaction):
        local_data = self.get_data(interaction)
        msg = ""

        for item in local_data["item"].keys():
            msg += f"{item}: {local_data["item"][item]}\n"

        if msg != "":
            await interaction.response.send_message(msg)
        else:
            await interaction.response.send_message("no item")

    async def user(self, interaction: Interaction):
        local_data = self.get_data(interaction)
        items = []
        for user in local_data["user"].keys():
            items.append((
                local_data["user"][user]["point"],
                local_data["user"][user]["name"]
            ))
        items.sort()

        msg = ""

        for pair in items:
            msg += f"{pair[1]}: {pair[0]}\n"

        if msg != "":
            await interaction.response.send_message(msg)
        else:
            await interaction.response.send_message("no user")
