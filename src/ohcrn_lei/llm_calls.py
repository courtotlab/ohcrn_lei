import json

from openai import OpenAI


def call_gpt_api(
  system_msg: str, query: str, model_used: str, mock: bool = False
) -> dict:
  if mock:
    return {"output": "mock"}

  client = OpenAI()

  chat_completion = client.chat.completions.create(
    model=model_used,
    response_format={"type": "json_object"},
    messages=[
      {"role": "system", "content": system_msg},
      {"role": "user", "content": query},
    ],
  )

  response_json = json.loads(chat_completion.choices[0].message.content)

  return response_json
