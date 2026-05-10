from discord import Interaction, Embed
import random

import lib.data_loader as data_loader


class LuckyWheel(data_loader.Data):
    def __init__(self, *args):
        super().__init__(*args)

    async def spin(self, interaction: Interaction):
        local_data = self.get_data(interaction, {"user": {}, "item": {}})

        items_dict = local_data["item"]
        if len(items_dict.keys()) < 2:
            await interaction.response.send_message("not enough items to spin")
            return

        item_names = list(items_dict.keys())
        weights = [v[1] for v in items_dict.values()]

        item = random.choices(item_names, weights=weights, k=1)[0]

        usr_id_str = str(interaction.user.id)
        value = items_dict[item][0]

        if usr_id_str in local_data["user"]:
            local_data["user"][usr_id_str]["point"] += value
        else:
            local_data["user"][usr_id_str] = {
                "name": interaction.user.name,
                "point": value,
            }

        await interaction.response.send_message(
            f"{interaction.user.mention} got **{item}**, value **{value}** points"
        )

    def add(self, key: str, val: int, weight: int, interaction: Interaction):
        local_data = self.get_data(interaction, {"user": {}, "item": {}})
        local_data["item"][key] = [val, weight]

    def remove(self, key: str, interaction: Interaction):
        local_data = self.get_data(interaction, {"user": {}, "item": {}})
        local_data["item"].pop(key)

    def set_weight(self, key: str, weight: int, interaction: Interaction):
        local_data = self.get_data(interaction, {"user": {}, "item": {}})
        local_data["item"][key][1] = weight

    def set_value(self, key: str, value: int, interaction: Interaction):
        local_data = self.get_data(interaction, {"user": {}, "item": {}})
        local_data["item"][key][0] = value

    async def list(self, interaction: Interaction):
        local_data = self.get_data(interaction, {"user": {}, "item": {}})

        total_weight = 0
        expected_value = 0

        items = []

        for item in local_data["item"].keys():
            item_dat = local_data["item"][item]
            total_weight += item_dat[1]
            expected_value += item_dat[0] * item_dat[1]
            items.append([item_dat[0], item_dat[1], item])
        if len(local_data["item"]) == 0:
            total_weight = 1

        items.sort(key=lambda x: (x[0], x[1]), reverse=True)

        expected_value /= total_weight

        name_field = ""
        value_field = ""
        weight_field = ""

        for item in items:
            name_field += item[2] + '\n'
            value_field += str(item[0]) + '\n'
            weight_field += str(item[1]) + f" ({item[1] * 100 / total_weight:.2f}%)\n"

        embed = Embed(title="Wheel Items", color=0x32a852)
        embed.add_field(name="Item", value=name_field, inline=True)
        embed.add_field(name="Value", value=value_field, inline=True)
        embed.add_field(name="Weight", value=weight_field, inline=True)
        embed.add_field(name="Expected value", value=f"{expected_value:.2f}")

        if name_field == "":
            await interaction.response.send_message("no item")
        else:
            await interaction.response.send_message(embed=embed)

    async def user(self, interaction: Interaction):
        local_data = self.get_data(interaction, {"user": {}, "item": {}})
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
