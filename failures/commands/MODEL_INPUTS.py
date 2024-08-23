import os

# TODO: Put all commands' model parameters here. Name them: MODEL_PARAMETERS_'COMMAND_NAME'
OPENAI_THEMES_INPUTS = {"model": "gpt-3.5-turbo", "temperature": 0, "api_key": os.getenv('OPENAI_API_KEY')}