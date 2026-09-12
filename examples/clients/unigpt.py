#%%
#
# Example for using UniGPT
#
import json

# Provide the access token and server URL
# in the environment variables:
# - Create .env file with the access token and URL,
#   see .env.default for a blueprint
# - Install python-dotenv:
#   pip install python-dotenv

import dotenv
dotenv.load_dotenv("databoard_core/.env")

from databoard_core.clients import llm_unigpt as llm

#%% Use our client classes

client = llm.UniGptClient()
client.settings['gpt_temperature'] = 0.0
client.settings['rawAnswer'] = False
answer = client.answer("Why is the sky blue?", "Short answer in six words please")
print(answer)


#%% Iterate over available models and output raw answers

client = llm.UniGptClient()
models = client.models()

#%%
answers = {}

for model in models:
    print(model)

    client.settings['gpt_modelname'] = model
    client.settings['rawAnswer'] = True
    answers[model] = client.answer("Why is the sky blue?", "Short answer in six words please")

    print(answers[model]['text'])

#%% Print as table
import json

print(f"{'Model':<30} {'Error':<10} {'Message'}")
for model, data in answers.items():

    try:
        message = json.loads(data["text"])["choices"][0]["message"]["content"]
    except Exception as e:
        message = ""

    error = data["status"] is not None

    print(f"{model:<30} {error:<10} {message[:50]}")

#%% Use a specific LLM server such as Blabador

# To use another LLM server, you can pass the server URL and access token directly when creating the client instance.
# For example, if you are affiliated with a German research institution, you can obtain API access to
# Blabador, a service operated by the Jülich research center, following the instructions in the documentation:
# https://sdlaml.pages.jsc.fz-juelich.de/ai/guides/blablador_api_access/

client = llm.UniGptClient(
    "https://api.blablador.fz-juelich.de/v1/",
    "YOURACCESSTOKEN"
)

# You need to provide a valid model name provided by the server
# To see the available models, print them
models = client.models()
print(models)

# Then set one of the candidates
client.settings['gpt_modelname'] = 'alias-apertus'

#%% Now you can use the server

client.settings['rawAnswer'] = True
answer = client.answer("Why is the sky blue?", "Short answer in six words please")
print(answer)
