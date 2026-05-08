import ollama
from lib.data_loader import Data
from discord import Interaction


class Chatbot:
    def __init__(self, datapath, model, basemodel, max_history=-1):
        self.model = model
        self.basemodel = basemodel
        self.max_history = max_history
        self.data = Data(datapath)

    def _history_slide(self, chat_data: dict):
        if self.max_history < 0:
            return
        while len(chat_data) > self.max_history:
            chat_data.pop(0)

    def save_history(self):
        self.data.save()

    def exist(self):
        models = ollama.list()['models']

        for model in models:
            if model.model == self.model + ":latest":
                return True
        return False

    def create(self, instruction):
        ollama.create(
            model=self.model,
            from_=self.basemodel,
            system=instruction,
        )

    def chat(self, content: str, reply_limit: int, role: int, interaction: Interaction):
        chat_data = self.data.get_data(interaction)
        chat_data.append({
            'role': role,
            'content': content
        })
        self._history_slide(chat_data)

        return ollama.chat(
            model=self.model,
            messages=chat_data,
            options={
                "num_predict": int(reply_limit / 4),
                "temperature": 1.3,
            },
            stream=True,
        )

    def add_bot_response(self, content, interaction: Interaction):
        chat_data = self.data.get_data(interaction)
        chat_data.append({
            "role": "assistant",
            "content": content
        })
        self._history_slide(chat_data)

    def clear_history(self, interaction: Interaction):
        chat_data = self.data.get_data(interaction)
        chat_data.clear()

    def get_info(self):
        info = ollama.show(self.model)
        ret = {
            "name": self.model,
            "modified_at": str(info.modified_at),
        }
        return ret | vars(info.details)
