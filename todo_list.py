class TODOList:
    todo_list = []

    def add(self, content):
        self.todo_list.append({
            "content": content,
            "checked": False
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
