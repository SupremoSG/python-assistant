from model.llm_wrapper import say
import json

def instruction():
    return '"duration": number, "unit": "seconds"|"minutes"'
def shape():
    return '"timer","args":{"duration": number, "unit":"seconds"|"minutes"}'

def setTimer():
    ...

def main(args):
    if not isinstance(args, dict) or args == "":
        print(type(args))
        return "I didn't understand your request."

    try:
        loader = json.loads(args)
        duration = loader.get("duration")
        unit = loader.get("unit")
        return setTimer(duration, unit)
    except Exception as e:
        print("I had an error while loading the timer")


if __name__ == "__main__":
    main()