import lib.data_loader as data_loader


class TODOList(data_loader.Data):
    todo_list: list

    def __init__(self, *args):
        super().__init__(*args)

    def valid_item(self, id, server_id):
        server_data = self.get_data_per_server(server_id, [])
        return id < len(server_data)

    def add(self, content, server_id):
        server_data = self.get_data_per_server(server_id, [])
        server_data.append({
            "content": content,
            "checked": False,
            "remind": -1,
        })

    def remove(self, id, server_id):
        server_data = self.get_data_per_server(server_id, [])
        server_data.pop(id)

    def toggle(self, id, server_id):
        server_data = self.get_data_per_server(server_id, [])
        server_data[id]["checked"] = not server_data[id]["checked"]

    def text(self, server_id):
        server_data = self.get_data_per_server(server_id, [])
        content = "```\n"
        if len(server_data) == 0:
            content = "nothing to show"
        else:
            for i in range(len(server_data)):
                item = server_data[i]
                box = "☐"
                if item["checked"]:
                    box = "☑"
                content += f"{i}. " + box + " " + item["content"] + "\n"
            content += "\n```"
        return content
