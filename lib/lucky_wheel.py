from discord import Interaction
import random

import lib.data_loader as data_loader


class LuckyWheel(data_loader.Data):
    def __init__(self, *args):
        super().__init__(*args)

        if "user" not in self.data.keys():
            self.data["user"] = {}
            self.data["item"] = {}

    async def spin(self, interaction: Interaction):
        if len(self.data["item"].keys()) < 2:
            await interaction.response.send_message("not enough item to spin")
            return

        item = random.choice(list(self.data["item"].keys()))

        if str(interaction.user.id) in self.data["user"].keys():
            self.data["user"][str(interaction.user.id)]["point"] += self.data["item"][item]
        else:
            self.data["user"][str(interaction.user.id)] = {
                "name": interaction.user.name,
                "point": self.data["item"][item],
            }

        await interaction.response.send_message(f"{interaction.user.mention} got {item}, valued {self.data["item"][item]} points")

    def add(self, key: str, val: int):
        self.data["item"][key] = val

    def remove(self, key: str):
        self.data["item"].pop(key)

    async def list(self, interaction: Interaction):
        msg = ""

        for item in self.data["item"].keys():
            msg += f"{item}: {self.data["item"][item]}\n"

        if msg != "":
            await interaction.response.send_message(msg)
        else:
            await interaction.response.send_message("no item")

    async def user(self, interaction: Interaction):
        l = []
        for user in self.data["user"].keys():
            l.append((self.data["user"][user]["point"], self.data["user"][user]["name"]))
        l.sort()

        msg = ""

        for pair in l:
            msg += f"{pair[1]}: {pair[0]}\n"

        if msg != "":
            await interaction.response.send_message(msg)
        else:
            await interaction.response.send_message("no user")
