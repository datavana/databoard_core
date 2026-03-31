#%%
#
# Example: Query a qdrant server
#
# You need to have a running Qdrant server on host 'localhost'.
#

from databoard_core.clients import QdrantClient

db = QdrantClient('localhost')
query = "Blüte"
answer = db.search(query, "example-token")
print(answer)