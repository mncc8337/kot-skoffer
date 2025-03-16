import lib.data_loader as data_loader


class TODOList(data_loader.Data):
    todo_list: list

    def __init__(self, *args):
        super().__init__(*args)
        if "todos" not in self.data.keys():
            self.data["todos"] = []
        self.todo_list = self.data["todos"]

    def add(self, content):
        self.todo_list.append({
            "content": content,
            "checked": False,
            "remind": -1,
        })

    def remove(self, id):
        self.todo_list.pop(id)

    def toggle(self, id):
        self.todo_list[id]["checked"] = not self.todo_list[id]["checked"]

    def text(self):
        content = "```\n"
        for i in range(len(self.todo_list)):
            item = self.todo_list[i]
            box = "☐"
            if item["checked"]:
                box = "☑"
            content += f"{i}. " + box + " " + item["content"] + "\n"
        content += "\n```"
        return content
