"""OHCRN-LEI - LLM-based Extraction of Information
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


def call_gpt_api(
  system_msg: str, query: str, model_used="gpt-4o", mock: bool = False
) -> dict:
  """Calls the GPT4o API with a given system message and query string.

  Args:
    system_msg: The system-message part of the LLM prompt
    query: The query part of the LLM prompt.
    model_used: The LLM model to use
    mock: Whether to skip this query and produce a mock output instead. (for debugging / unit tests)

  Returns:
    A dictionary representation of the JSON output produced by the LLM

  """
  if mock:
    return {"output": "mock"}

  # lazy import to speed-up app load time
  from openai import OpenAI

  client = OpenAI()

  chat_completion = client.chat.completions.create(
    model=model_used,
    response_format={"type": "json_object"},
    messages=[
      {"role": "system", "content": system_msg},
      {"role": "user", "content": query},
    ],
  )

  response_json = json.loads(str(chat_completion.choices[0].message.content))

  return response_json
