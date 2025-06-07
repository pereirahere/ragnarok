# build_indexes.py

import pathlib
import yaml
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
from langchain_ollama.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from loaders.loader_factory import LoaderFactory

# --- Configuration ---
FAISS_ROOT_DIR = pathlib.Path("faiss_indexes")
CONFIG_PATH = "config.yml"

def build_index_for_repo(repo_name: str, repo_path: str, embedding_model: str):
    """Builds and saves a FAISS index for a single repository using the loader factory."""
    
    index_dir = FAISS_ROOT_DIR / repo_name
    print(f"\n--- Building index for repository: '{repo_name}' ---")

    # 1. Instantiate the factory and define desired loaders
    loader_factory = LoaderFactory(repo_path)
    desired_loader_types = [
        Language.JAVA,
        Language.PYTHON,
        Language.JS,
        "general_unstructured"
    ]
    
    # 2. Load all documents by iterating through the desired loaders
    all_docs = []
    print("Loading documents...")
    for loader_type in desired_loader_types:
        try:
            loader = loader_factory.get_loader(loader_type)
            all_docs.extend(loader.load())
        except Exception as e:
            print(f"  - Warning: Could not use loader for type '{loader_type}'. Error: {e}")

    if not all_docs:
        print(f"WARNING: No documents were loaded for '{repo_name}'. Skipping.")
        return
        
    print(f"Loaded a total of {len(all_docs)} documents.")

    # 3. Define splitters and split documents
    splitters = {
        Language.JAVA: RecursiveCharacterTextSplitter.from_language(language=Language.JAVA, chunk_size=1000, chunk_overlap=200),
        Language.PYTHON: RecursiveCharacterTextSplitter.from_language(language=Language.PYTHON, chunk_size=1000, chunk_overlap=200),
        Language.JS: RecursiveCharacterTextSplitter.from_language(language=Language.JS, chunk_size=1000, chunk_overlap=200),
        "general": RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    }

    final_chunks = []
    for doc in all_docs:
        doc_language = doc.metadata.get("language")
        splitter = splitters.get(doc_language, splitters["general"])
        final_chunks.extend(splitter.split_documents([doc]))
        
    if not final_chunks:
        print(f"WARNING: No chunks were created for '{repo_name}'. Skipping index creation.")
        return
    print(f"Created {len(final_chunks)} total chunks.")

    # 4. Create embeddings and save FAISS Index
    print(f"Creating embeddings with '{embedding_model}' and building FAISS index...")
    emb = OllamaEmbeddings(model=embedding_model)
    db = FAISS.from_documents(final_chunks, emb)
    db.save_local(index_dir)
    print(f"Index for '{repo_name}' built and saved successfully.")


if __name__ == "__main__":
    FAISS_ROOT_DIR.mkdir(exist_ok=True)

    with open(CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)

    model_config = config.get("models", {})
    embedding_model_name = model_config.get("embedding")
    
    if not embedding_model_name:
        raise ValueError("Embedding model name not found in config.yml under models:embedding")

    for repo in config.get("repositories", []):
        repo_name = repo.get("name")
        repo_path = repo.get("path")
        if repo_name and repo_path:
            build_index_for_repo(repo_name, repo_path, embedding_model_name)
        else:
            print(f"WARNING: Skipping invalid repository entry in config.yml: {repo}")
    
    print("\n--- All indexes built. ---")