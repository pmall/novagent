import os
from agent import Novagent
from models import LiteLLMModel
from outputs import CliOutput

API_KEY = os.getenv("LITELLM_API_KEY")
MODEL_ID = os.getenv("LITELLM_MODEL_ID")

EXTRA_INSTRUCTIONS = """
### Guidelines for Data Analysis

- **No Internet Access:**  
  Do **not** attempt to download or fetch external resources. You must work **only** with the provided local files.

- **Inspect the Data First:**  
  Before starting any analysis, preview a few rows to understand the structure and contents.

- **Excel Files – Multiple Sheets:**  
  Always check for multiple sheets in Excel files. Never assume the structure is based on the first sheet alone.

- **Missing or Inadequate Data:**  
  If no suitable data is found for the task, clearly state the issue and stop the analysis.
""".strip()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("task", type=str, help="The task to solve using the code agent")
    args = parser.parse_args()

    model = LiteLLMModel(api_key=API_KEY, model_id=MODEL_ID)

    agent = Novagent(model, output=CliOutput(), extra_instructions=EXTRA_INSTRUCTIONS)

    agent.run(args.task)

    while True:
        more = input("Is this ok? (q to quit)\n> ")

        if more.lower() == "q":
            break

        agent.run(more)
