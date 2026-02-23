from model.llm_wrapper import say
import importlib
import json
import sys
import os

class Assistant:
    def __init__(self, name="Siri"):
        self.name = name
        self.memory = []
        self.shapes = read_skills("shape")
        self.instructions = read_skills("instruction")

    def router(self, text):
        raw = self.parse_intent(text)
        print("RAW:", raw)

        try:
            intent = json.loads(raw)
        except Exception as e:
            return f"Router output is not valid JSON: {raw!r} ({e})"

        tool = intent.get("type")
        args = intent.get("args", {})
        tool = "" if tool is None else str(tool).strip().lower()

        if tool in ("", "none", "null"):
            return say(text, env="local", type="chat")

        try:
            module = importlib.import_module(f"skills.{tool}")
            return module.main(args=args, text=text)
        except ModuleNotFoundError:
            return f"Skill not found: {tool}"
    
    def parse_intent(self, text):
        return say(text, env="local", type="router", 
                   shapes=self.shapes, 
                   instructions=self.instructions)
    
def read_skills(x):
    shape = ""
    instruction = ""
    for file in os.listdir("skills"):
        if file.endswith(".py") and file != "__init__.py":
            skill = file[:-3]
            module = importlib.import_module(f"skills.{skill}")
            if hasattr(module, "shape"):
                shape += f"- {{\"type\":{str(module.shape())}}}\n"
            if hasattr(module, "instruction"):
                instruction += f'- {skill}: {{{str(module.instruction())}}}\n'
    if x == "shape":
        return shape
    if x == "instruction":
        return instruction
    else:
        raise ValueError

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