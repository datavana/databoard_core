#
# Download the models before starting the app
#
# You need to have a running Qdrant server on host 'qdrant'.
# On the terminal: python src/embeddings/install.py
#

# Load our database class
from databoard_core.clients import QdrantClient

if __name__ == "__main__":
    #args = sys.argv
    # args[0] = current file
    # args[1] = function name
    # args[2:] = function args : (*unpacked)
    # globals()[args[1]](*args[2:])

    db = QdrantClient('qdrant')
    db.loadModels()

