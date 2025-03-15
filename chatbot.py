import ollama


class Chatbot:
    model: str = None
    basemodel: str = None

    def __init__(self, model, basemodel):
        self.model = model
        self.basemodel = basemodel

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
            system=instruction
        )

    def chat(self, content: str):
        return ollama.chat(
            model=self.model,
            messages=[{
                'role': 'user',
                'content': content
            }],
            stream=True,
        )
