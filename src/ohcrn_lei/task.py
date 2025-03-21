
import os
import sys

from ohcrn_lei import llm_calls


class Task:

  def __init__(self, prompt:str):
    self.prompt=prompt
    self.plutings = None


  def set_plugins(self, plugins:dict):
    self.plugins = plugins


  # print string representation
  def __str__(self):
    return "PROMPT:\n"+ self.prompt + "\nPLUGINS:\n"+ str(self.plugins)


  def run(self, inputfile:str, chunk_size=2) -> dict:

    try:
      with open(inputfile, 'r', encoding='utf-8') as instream:
        text = instream.read()
    except Exception as e:
      print(f"ERROR: Unable to read file {inputfile}: {e}")
      sys.exit(os.EX_IOERR)

    #simulate multiple pages for plain text input
    all_text = [text]

    i=0
    full_llm_results = {}

    while i <= len(all_text)-(chunk_size-1):

        print("Sending request for pages",i,"to",i+chunk_size-1)
        merge = " ".join(all_text[i:i+chunk_size])

        #Prepare query
        query_msg = "Use the given format to extract information from the following input: "+merge
        #Call the API to get JSON (dict) with the requested fields in the prompt
        llm_results = llm_calls.call_gpt_api(self.prompt, query_msg, "gpt-4o")
        #Add to llm dict
        full_llm_results["Pages "+str(i+1)+"-"+str(i+chunk_size)] = llm_results

        i+=chunk_size

    return full_llm_results