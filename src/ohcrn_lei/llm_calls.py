"""
OHCRN-LEI - LLM-based Extraction of Information
Copyright (C) 2025 Ontario Institute for Cancer Research

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

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
