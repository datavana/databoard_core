#%%
# Example: Import data into qdrant vector database.
#
# You need to have a running Qdrant server on host '127.0.0.1'.
#
# See https://python-client.qdrant.tech/


#%% Import packages

import pandas as pd
from databoard_core.clients import QdrantClient

db = QdrantClient('localhost')

#%% Load text


# Load markdown files from "data/articles" into a DataFrame
# TODO: Provide sample data in the repository
df = db.loadTextFolder("data/articles/")

#%% Sample

df = df.sample(n=10)

#%% Calculate embeddings

# TODO: why does the call fail, but doing it line by line works?
#tokens = db.tokenizeAndEmbedText(df)

list_tokens = df['text'].apply(db.embedToken)
tokens = pd.concat([pd.DataFrame(df_token) for df_token in list_tokens], keys=df['document'])
tokens = tokens.reset_index(level=1, drop=True)
tokens = tokens.reset_index()


#%% Create a qdrant collections

db.createCollection("example-token", len(tokens['embedding'][0]))

#%% Fill the qdrant instance

db.fillCollection("example-token", tokens)

#%% Search the database

db.searchVector( "gloriose", "example-token", 5)
