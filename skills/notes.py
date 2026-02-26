from pathlib import Path
from model.llm_wrapper import say
import json
import ast

def shape():
    return '"notes","args":{{"action":"add","context":"buy bananas"}'
def instruction():
    return '"action": "add"|"list"|"delete", "context": string (required - return "" if no context specified))'

persistence = Path("skills/notes/notes.json")

def checkPersistence():
    return Path.exists(persistence)

def add(text, context):
    if checkPersistence():
        data = json.loads(persistence.read_text())
    else:
        data = {"next_id":0, "notes": []}

    prompt = f"""
    A program detected the user is trying to add a note.
    The program extracted this note context:
    ----
    {context}
    ----
    From the user's message:
    ----
    {text}
    ----
    Please analyze the user's request above and create a note based on his needs.
    Rules:
    - If the user's input is direct as if talking to a machine output the note without editing it.
    - If the user's input is more flexible as if talking to a human or assistant, 
    rephrase the note in a way that makes it easy to understand, and shorter if able to summarize without
    losing important context.
    - Output only the final note text, nothing else. No explanation, no punctuation besides what is necessary.
    
    Output:
    """
    
    newNote = say(prompt, env="groq", type="chat")
    data["notes"].append({
        "id": data["next_id"],
        "note": newNote
    })
    data["next_id"] += 1
    persistence.parent.mkdir(parents=True, exist_ok=True)
    persistence.write_text(json.dumps(data, indent=2))
    return f'Added to your notes: "{newNote}"'

def inv(text, context):
    if checkPersistence():
        data = json.loads(persistence.read_text())
    else:
        return "You don't have any notes."
    
    notes = data["notes"]
    notelist = ""
    for i in range(len(notes)):
            notelist += f"[{notes[i]["id"]}]: {notes[i]["note"]}\n"
    print(notelist)
    print(context)
    prompt = f"""
    A program detected the user is trying to browse his notes.
    The program extracted this note context:
    ----
    {context}
    ----
    From the user's message:
    ----
    {text}
    ----
    His notes:
    [ID]: <note>
    {notelist}
    ----

    Please analyze the user's request above and find a note that matches the best based on his needs.
    Rules:
    - If the user's input is direct as if talking to a machine output the note without editing it.
    - If the user's input is more flexible as if talking to a human or assistant, 
    rephrase the note in a way that makes it easy to understand, and shorter if able to summarize without
    losing important context.
    
    Output:
    """
    return say(prompt, env="groq", type="chat")

def delete(text, context):
    if checkPersistence():
        data = json.loads(persistence.read_text())
    else:
        return "You don't have any notes."
    
    notes = data["notes"]
    notelist = ""
    for i in range(len(notes)):
            notelist += f"[{notes[i]["id"]}]: {notes[i]["note"]}\n"
    print(notelist)  
    prompt1 = f"""
    Analyze the user's request and find all notes they want to delete from the list below.

    User request:
    --
    {text}
    --
    Notes:
    --
    {notelist}
    --
    Output rules:
    - Output a valid Python list of strings
    - Each string must be a complete note exactly as it appears in the list
    - Example output: ["buy oranges", "drink water"]
    - If no matches found, output: []
    - Output nothing else, no explanation, no extra text

    Output:
    """

    try:
        delete = ast.literal_eval(say(prompt1, env="groq", type="chat").strip())
        print(delete)
        prompt2 = f"""
    You are confirming a delete action with the user.

    Notes to be deleted:
    ---
    {delete}
    ---

    Output rules:
    - Write a single confirmation question
    - Always mention the number of notes being deleted
    - If there is 1 note, also mention its name
    - If there are multiple notes, give the count and a brief theme/summary of what they're about
    - Never list all notes individually
    - Never say just "these notes" without context
    - Output only the question, nothing else

    Examples:
    1 note: "Are you sure you want to delete 'buy bananas'?"
    3 notes: "Are you sure you want to delete these 3 notes about daily tasks?"

    Output:
        """
        llm = say(prompt2, env="groq", type="chat")
        answer = input(f"{llm}\n>")
        prompt2 = f"""
        Check this user's input and determine that it is either affirming or denying something, then return either yes or no.
        Input: {answer}
        --
        Rules:
        - First analyze the input, determine it is either agreeing or disagreeing.
        - Output must be strictly either yes or no.
        - No capitalizing letters, no extra words, no ponctuation.
        - strictly either "yes" or "no", if in doubt, return no.
        - if the user's input is messy and you don't wanna risk, just default to no
        """
        answer2 = say(prompt2, env="local", type="chat")
        print(answer2)
        if answer2 == "yes" or answer2 == "no":
            if answer2 == "yes":
                newNotes = []
                for item in data["notes"]:
                    if item["note"] not in delete:
                        newNotes.append(item)
                data["notes"] = newNotes
                data["next_id"] = len(data["notes"]) + 1
                for i, item in enumerate(data["notes"]):
                    item["id"] = i + 1
                persistence.parent.mkdir(parents=True, exist_ok=True)
                persistence.write_text(json.dumps(data, indent=2))
                return "Deleted."
            if answer2 == "no":
                return "Okay, cancelled."
        else:
            return "What? I don't understand so I cancelled."
    except Exception as e:
        return "I failed", e
    

def routeNotes(text, action, context):
    match action:
        case "add":
            return add(text, context)
        case "list":
            return inv(text, context)
        case "delete":
            return delete(text, context)


def main(text, args):
    print(args)
    if not isinstance(args, dict) or args == "":
        return "I didn't understand your request."
    try:
        action = args["action"]
        if "context" in args:
            context = args["context"]    
        else:
            context = ""

        return routeNotes(text, action, context)
    except Exception as e:
        return ("Something isn't quite right with your request", e)

if __name__ == "__main__":
    main()