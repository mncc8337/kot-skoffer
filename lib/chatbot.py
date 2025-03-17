import ollama
from lib.data_loader import Data


class Chatbot:
    model: str = None
    basemodel: str = None
    chat_history: list = []
    max_history: int = -1
    data: Data

    def __init__(self, datapath, model, basemodel, max_history=-1):
        self.model = model
        self.basemodel = basemodel
        self.max_history = max_history
        self.data = Data(datapath)
        if "chat_history" not in self.data.data.keys():
            self.data.data["chat_history"] = []
        self.chat_history = self.data.data["chat_history"]

    def _history_slide(self):
        if self.max_history < 0:
            return
        while len(self.chat_history) > self.max_history:
            self.chat_history.pop(0)

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

    def chat(self, content: str, reply_limit: int, role: int):
        self.chat_history.append({
            'role': role,
            'content': content
        })
        self._history_slide()

        return ollama.chat(
            model=self.model,
            messages=self.chat_history,
            options={
                "num_predict": int(reply_limit / 4),
                "temperature": 1.3,
            },
            stream=True,
        )

    def add_bot_response(self, content):
        self.chat_history.append({"role": "assistant", "content": content})
        self._history_slide()

    def clear_history(self):
        self.chat_history.clear()

    def get_info(self):
        info = ollama.show(self.model)
        ret = {
            "name": self.model,
            "modified_at": str(info.modified_at),
        }
        return ret | vars(info.details)
