from skills import notes, timer, weather
from model.llm_wrapper import say
import json
import sys
import os

class Assistant:
    def __init__(self, name="Siri"):
        self.name = name
        self.memory = []

    def router(self, text):
        skills = ["weather", "notes", "timer"]
        try:
            intent = json.loads(self.parse_intent(text))
            if not isinstance(intent, dict):
                raise ValueError
            if intent.get("type") == "none":
                return say(text, env="local", type="chat")
            else:
                return intent
        except Exception as e:
            sys.exit("Exception while processing request:", e)

        

        

    def parse_intent(self, text):
        return say(text, env="local", type="router")


def main():
    assistant = Assistant()
    while True:
        try:
            user = input(">")
            if user in ["exit", "quit"]:
                sys.exit()
            print(assistant.router(user))
        except (EOFError, KeyboardInterrupt):
            sys.exit()
            
if __name__ == "__main__":
    main()