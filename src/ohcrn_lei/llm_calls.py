from openai import OpenAI
import json

def call_gpt_api(system_msg:str, query:str, model_used:str)->dict:
    client = OpenAI()

    chat_completion = client.chat.completions.create(
        model=model_used,
        response_format={"type":"json_object"},
        messages=[
            {"role":"system", "content":system_msg},
            {"role": "user", "content": query}
        ]
    )

    response_json = json.loads(chat_completion.choices[0].message.content)

    return response_json

