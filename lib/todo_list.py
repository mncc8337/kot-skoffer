import lib.data_loader as data_loader
from discord import Interaction


class TODOList(data_loader.Data):
    todo_list: list

    def __init__(self, *args):
        super().__init__(*args)

    def valid_item(self, id, interaction: Interaction):
        local_data = self.get_data(interaction, [])
        return id < len(local_data)

    def add(self, content, interaction: Interaction):
        local_data = self.get_data(interaction, [])
        local_data.append({
            "content": content,
            "checked": False,
            "remind": -1,
        })

    def remove(self, id, interaction: Interaction):
        local_data = self.get_data(interaction, [])
        local_data.pop(id)

    def toggle(self, id, interaction: Interaction):
        local_data = self.get_data(interaction, [])
        local_data[id]["checked"] = not local_data[id]["checked"]

    def text(self, interaction: Interaction):
        local_data = self.get_data(interaction, [])
        content = "```\n"
        if len(local_data) == 0:
            content = "nothing to show"
        else:
            for i in range(len(local_data)):
                item = local_data[i]
                box = "☐"
                if item["checked"]:
                    box = "☑"
                content += f"{i}. " + box + " " + item["content"] + "\n"
            content += "\n```"
        return content
