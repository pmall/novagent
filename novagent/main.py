import os
from novagent.agent import Novagent
from novagent.models import LiteLLMModel
from novagent.loggers import LogLevel

API_KEY = os.getenv("LITELLM_API_KEY")
MODEL_ID = os.getenv("LITELLM_MODEL_ID")

AUTHORIZED_IMPORTS = [
    "os",
    "sys",
    "math",
    "re",
    "json",
    "csv",
    "datetime",
    "numpy",
    "pandas",
    "matplotlib",
    "openpyxl",
]

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("task", type=str, help="The task to solve using the code agent")
    args = parser.parse_args()

    model = LiteLLMModel(api_key=API_KEY, model_id=MODEL_ID)

    agent = Novagent(
        model, log_level=LogLevel.VERBOSE, authorized_imports=AUTHORIZED_IMPORTS
    )

    agent.run(args.task)

    while True:
        more = input("Is this ok? (q to quit)\n> ")

        if more.lower() == "q":
            break

        agent.run(more)
