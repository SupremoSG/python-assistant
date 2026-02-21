from dotenv import load_dotenv
from openai import OpenAI
from llama_cpp import Llama
import os

load_dotenv()
client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)

MODEL_PATH = "model/qwen2.5-1.5b-instruct-q4_k_m.gguf"
llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=1024,
    verbose=False
)

def say(text, env="local", type="router"):
    prompt = f"""
You are a TOOL ROUTER. You do NOT answer the user. You only choose whether to call a tool and extract arguments.

Return VALID JSON only. One JSON object. No markdown. No extra text.

Tools and args:
- timer: {{"duration": number, "unit": "seconds"|"minutes"}}
- notes: {{"action": "add"|"list"|"delete", "content": string (required for add/delete)}}
- weather: {{"location": string}}

Output formats (choose ONE):

If a tool is needed, return ONE of these shapes:

{{"type":"timer","args":{{"duration":5,"unit":"minutes"}}}}
{{"type":"weather","args":{{"location":"current location"}}}}
{{"type":"notes","args":{{"action":"add","content":"buy bananas"}}}}

If no tool is needed, return:

{{"type":"none"}}

Hard routing rules:
- If the user asks about weather, temperature, forecast, rain, snow, wind, outside conditions, or “what’s it like today” -> ALWAYS use tool "weather".
- If the user asks to set/start/cancel a timer, countdown, remind in X time, or mentions a duration like “30 seconds/5 minutes” -> ALWAYS use tool "timer".
- If the user asks to write/save/add a note, list notes, or delete a note -> ALWAYS use tool "notes".

Argument rules:
- Use ONLY the listed keys. Do not invent keys.
- For timer:
  - duration must be a number.
  - unit must be exactly "seconds" or "minutes".
  - If unit missing, assume "minutes".
- For notes:
  - If user says “write/add note” but gives no content, still return notes with action="add" and content="".
  - If user says list notes -> action="list" and omit content.
  - If user says delete note but no content -> action="delete" and content="".
- For weather:
  - If no location is provided, set location="current location".

User input: "{text}"
JSON:
"""

    if env == "local":
        if type == "router":
            output = llm.create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a router."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=40,
                temperature=0.2,
            )
            return output["choices"][0]["message"]["content"].strip()

        elif type == "chat":
            output = llm.create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": text}
                ],
                max_tokens=40,
                temperature=0.2,
            )
            return output["choices"][0]["message"]["content"].strip()

        else:
            raise ValueError("Invalid Type")

    elif env == "groq":
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="openai/gpt-oss-20b"
        )
        return response.choices[0].message.content