#
# Experimental class to use the qdrant vector database for storing and searching text embeddings.
#

import os
import pandas as pd

import torch
from transformers import AutoTokenizer, AutoModel

from qdrant_client import QdrantClient as RawQdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchText
from qdrant_client import models

from qdrant_client.models import VectorParams, Distance
from qdrant_client.models import PointStruct

class QdrantClient:
    def __init__(self, qdrant_host='localhost'):
        """
        Manages text loading, embedding, search

        @param qdrant_host The qdrant host
        """

        self.settings = {
            'qdrant_host': qdrant_host
        }

        self.qdrantClient = None
        self.tokenizerModel = None
        self.nlpModel = None

    def loadModels(self):
        model_name = "deepset/gbert-large"

        if self.tokenizerModel is None:
            self.tokenizerModel = AutoTokenizer.from_pretrained(model_name)

        if self.nlpModel is None:
            self.nlpModel = AutoModel.from_pretrained(model_name)

        return self.nlpModel

    def loadQdrant(self):
        if self.qdrantClient is None:
            self.qdrantClient = RawQdrantClient(host=self.settings['qdrant_host'], port=6333)

        return self.qdrantClient

    def createCollection(self, name, vectorLength):
        """
        Create a qdrant collection
        See https://python-client.qdrant.tech/

        :param name:
        :param vectorLength:
        :return:
        """
        self.loadQdrant()

        collection_name = name
        if not self.qdrantClient.collection_exists(collection_name):
            self.qdrantClient.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=vectorLength, distance=Distance.COSINE),
            )

    def fillCollection(self, collection_name, df):
        """ Push embeddings to a qdrant instance

        Parameters:
        collection_name (string): name of the collection
        df (Dataframe) Data source with the columns document, token, and embedding
        """

        self.loadQdrant()

        batch_size = 1000

        # Iterate through the DataFrame in batches
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i + batch_size]

            collection_points = [
                PointStruct(
                    id=(i * batch_size) + idx,
                    vector=row.embedding,
                    payload={
                        'document': row.document,
                        'text': row.token
                    }
                )
                for idx, row in batch.iterrows()
            ]

            self.qdrantClient.upsert(collection_name=collection_name, points=collection_points)

    def search(self, query, corpus):
        status = ''
        text = []
        try:
            text = self.searchVector(query, corpus, 10)
        except Exception as e:
            status = str(e)

        return {'text' : text, 'status' : status}

    def searchVector(self, term, collection, nn=1):
        self.loadQdrant()

        # search_embed = self.embedToken(term)
        # search_embed = search_embed['embedding'][0]

        # hits = self.qdrantClient.search(
        #    collection_name=collection,
        #    query_vector=search_embed,
        #    limit=nn  # Return 5 closest points
        # )

        search_embed = self.embedToken(term)
        search_embed = search_embed.embedding.to_list()

        hits = self.qdrantClient.query_points(
            collection_name=collection,
            query=models.RecommendQuery(
                recommend=models.RecommendInput(
                    positive=search_embed,
                    strategy=models.RecommendStrategy.AVERAGE_VECTOR
                )
            ),
            limit=nn
        )

        results = []
        for hit in hits.points:
            result = hit.payload
            result['score'] = hit.score
            results.append(result)

        return results

    def searchTerm(self, term, collection, field = "text", nn=1):
        self.loadQdrant()

        hits = self.qdrantClient.scroll(
            collection_name=collection,
            limit=nn,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key=field,
                        match=MatchText(text=term)
                    )
                ]
            ),
            with_payload=True
        )
        return hits


    def loadText(self, filename, path="data/articles/", rm_breaks=True, show=True):
        """
        Load a text file and remove all line breaks

        :param filename: The text file name
        :param path: The path
        :param rm_breaks Whether to replace line breaks by space.
        :param show: Whether to print the loaded text
        :return: The loaded text
        """
        with (open(path + filename, "r", encoding="utf-8") as f):
            content = f.read()
            if rm_breaks:
                content = content.replace('\r', '').replace('\n', ' ')

        if show:
            print("Text :\n" +content)

        return(content)

    def loadTextFolder(self, path="data/articles/", extension=".md"):
        """
        Load all text files in a folder

        :param path: Folder with text files
        :param extension All files matching the extension (e.g. ".md" or ".txt") will be loaded
        :return: A data frame with the columns filename and text
        """

        rows = []
        for filename in os.listdir(path):
            if filename.endswith(extension):  # Only process .md files

                content = self.loadText(filename, path, show=False)

                row = {
                    'document': filename,
                    'text': content
                }
                rows.append(row)

        df = pd.DataFrame(rows)
        return df

    def tokenizeAndEmbedText(self, df):
        """
        Tokenize text and calculate embeddings for each token

        :param df:
        :return:
        """
        list_tokens = df['text'].apply(self.embedToken)
        tokens = pd.concat([pd.DataFrame(df_token) for df_token in list_tokens], keys=df['document'])
        tokens = tokens.reset_index(level=1, drop=True)
        tokens = tokens.reset_index()

        return tokens

    def embedToken(self, text):
        """
        Get tokens and their embeddings

        @param text A character value
        @return Returns a pandas DataFrame with one row
                and the columns token and embeddings.
                The columns contain lists with one value for each token.
        """

        self.loadModels()

        # Tokenize the text
        inputs = self.tokenizerModel(text, return_tensors="pt", truncation=True, padding=True, is_split_into_words=False)
        tokens = self.tokenizerModel.convert_ids_to_tokens(inputs['input_ids'].squeeze().tolist())

        # Get the embeddings from the model
        # (last hidden states)
        with torch.no_grad():
            outputs = self.nlpModel(**inputs)
        embeddings = outputs.last_hidden_state.squeeze(0)

        # Calculate the mean embedding across all tokens (to represent the whole document)
        #embeddings = embeddings.mean(dim=0).tolist()

        # Create a DataFrame for tokens and embeddings
        tokens_df = pd.DataFrame({
            'token': tokens,
            'embedding': embeddings.tolist()
        })

        return tokens_df
