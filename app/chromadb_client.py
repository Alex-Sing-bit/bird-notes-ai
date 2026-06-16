import chromadb
import pandas as pd
from chromadb.utils import embedding_functions
from semchunk import semchunk
from transformers import AutoTokenizer

import config

_chroma_client = None
_birds_collection = None


def get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=config.CHROMA_DB_PATH)
    return _chroma_client


def get_birds_collection():
    global _birds_collection

    if _birds_collection is not None:
        return _birds_collection

    client = get_chroma_client()

    existing_collections = [c.name for c in client.list_collections()]

    if config.CHROMA_COLLECTION_NAME in existing_collections:
        _birds_collection = client.get_collection(
            name=config.CHROMA_COLLECTION_NAME
        )
    else:
        _birds_collection = _create_collection(client)

    return _birds_collection

def _create_collection(chroma_client):
    tokenizer = AutoTokenizer.from_pretrained(config.EMBEDDING_MODEL_NAME)

    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=config.EMBEDDING_MODEL_NAME
    )

    collection = chroma_client.create_collection(
        name=config.CHROMA_COLLECTION_NAME,
        embedding_function=ef
    )

    _fill_collection(collection, tokenizer)

    return collection

def _fill_collection(filled_collection, tokenizer):
    chunker = semchunk.chunkerify(
        tokenizer_or_token_counter=tokenizer,
        chunk_size=config.CHUNK_SIZE,
        memoize=True
    )

    path_csv = config.BIRDS_DATA_PATH
    try:
        df = pd.read_csv(path_csv)
        df["full_text"] = df["full_text"].fillna('')

        ids = []
        metadatas = []
        documents = []

        for index, row in df.iterrows():
            text = " ".join(row['full_text'].split())
            if not text:
                continue

            chunks = chunker(text)

            for i, chunk in enumerate(chunks):
                metadata = {
                    "bird_name": row["name"],
                    "source": "wikipedia_birds",
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "original_row_id": index,
                    "bird_name_lower": row["name"].lower()
                }

                chunk_id = f"{row["name"]}_{index}_{i}"

                documents.append(f"{config.PASSAGE_PREFIX}{chunk}")
                metadatas.append(metadata)
                ids.append(chunk_id)

        filled_collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

    except FileNotFoundError as e:
        print(f"Ошибка чтения файла {config.BIRDS_DATA_PATH}: {e}")
        raise
    except Exception as e:
        print(f"Ошибка при загрузке данных: {e}")
        raise