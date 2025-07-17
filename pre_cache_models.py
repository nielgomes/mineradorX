# Arquivo: pre_cache_models.py
from langchain_huggingface import HuggingFaceEmbeddings

print("--- Pré-aquecendo o cache do modelo de embeddings ---")
try:
    HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    print("✅ Cache do modelo de embeddings aquecido com sucesso.")
except Exception as e:
    print(f"❌ Erro ao aquecer o cache: {e}")