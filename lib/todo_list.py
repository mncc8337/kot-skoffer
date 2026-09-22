import lib.data_loader as data_loader
from discord import Interaction


class TODOList(data_loader.Data):
    def __init__(self, *args):
        super().__init__(*args)

    def valid_item(self, item_id: int, interaction: Interaction):
        data, _, _ = self.get_data(interaction)
        return item_id < len(data["items"])

    def add(self, content: str, interaction: Interaction):
        doc, target_id, target_type = self.get_data(interaction, {"items": []})

        doc["items"].append(
            {
                "content": content,
                "checked": False,
                "remind": -1,
            }
        )

        self.save_data(doc, target_id, target_type)

    def remove(self, item_id: int, interaction: Interaction):
        doc, target_id, target_type = self.get_data(interaction, {"items": []})

        if item_id < len(doc["items"]):
            doc["items"].pop(item_id)
            self.save_data(doc, target_id, target_type)

        if item_id < len(doc["items"]):
            doc["items"].pop(item_id)
            self.save_data(doc, target_id, target_type)

    def toggle(self, item_id: int, interaction: Interaction):
        doc, target_id, target_type = self.get_data(interaction, {"items": []})

        if item_id < len(doc["items"]):
            doc["items"][item_id]["checked"] = not doc["items"][item_id]["checked"]
            self.save_data(doc, target_id, target_type)

    def text(self, interaction: Interaction):
        doc, _, _ = self.get_data(interaction, {"items": []})
        items = doc["items"]

        if len(items) == 0:
            return "nothing to show"

        content = "```\n"
        for i, item in enumerate(items):
            box = "☑" if item["checked"] else "☐"
            content += f"{i}. {box} {item['content']}\n"
        content += "```"

        return content
