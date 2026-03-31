# %% Ollama example

# Make sure to have a ollama docker container running.
# From the databoard_server repository root, run:
# ```
# docker compose up -d
# ```
# For first time usage, pull the llama model:
# ```
# docker exec -it db_ollama ollama pull llama3.2
# ```

from databoard_core.clients import OllamaClient

client = OllamaClient()
answer =client.answer("Why is the sky blue?", "Short answer in six words please")
print(answer)

