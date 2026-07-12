import os
os.environ.setdefault("HF_HOME", "./rerankers")

from sentence_transformers import CrossEncoder

MODEL_NAME = "BAAI/bge-reranker-base"

def download():
    print(f"Downloading {MODEL_NAME} ...")
    model = CrossEncoder(MODEL_NAME, max_length=512)
    print("Done.")
    return model

if __name__ == "__main__":
    download()