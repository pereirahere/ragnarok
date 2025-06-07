import os
import pathlib
import yaml
import chainlit as cl

# Import new components for the direct chat chain
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

# Existing imports
from langchain.retrievers import EnsembleRetriever
from langchain_ollama.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.llms import Ollama
from langchain.chains import RetrievalQA

# --- Configuration ---
FAISS_ROOT_DIR = pathlib.Path("faiss_indexes")
CONFIG_PATH = "config.yml"

# Load model configurations from the YAML file
try:
    with open(CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)
    LLM_MODEL = config.get("models", {}).get("llm")
    EMB_MODEL = config.get("models", {}).get("embedding")
    if not all([LLM_MODEL, EMB_MODEL]):
        raise ValueError("LLM or Embedding model not defined in config.yml")
except (FileNotFoundError, ValueError) as e:
    print(f"Error loading configuration: {e}")
    exit()

@cl.set_chat_profiles
def chat_profile():
    return [
        cl.ChatProfile(
            name="Repo Q&A",
            markdown_description="Chat with your repositories. The model will use your code as context.",
            icon="https://static.thenounproject.com/png/file-icon-7914143-512.png",
        ),
        cl.ChatProfile(
            name="General Chat",
            markdown_description="A general-purpose chat with the model you chose.",
            icon="https://static.thenounproject.com/png/chat-icon-7454161-512.png",
        ),
    ]
def chat_profile(current_user: cl.User):
    # This can be used to further customize based on user, but we'll keep it simple
    return

@cl.on_chat_start
async def on_chat_start():
    """
    This function now creates and stores BOTH chains in the user session.
    """
    # Get the current chat profile to decide what to load
    chat_profile = cl.user_session.get("chat_profile")
    
    # --- Setup for Direct Chat (always available) ---
    llm = Ollama(model=LLM_MODEL)
    prompt = PromptTemplate(
        template="You are a helpful AI assistant. Answer the following question.\nQuestion: {question}\nAnswer:",
        input_variables=["question"]
    )
    chat_chain = LLMChain(llm=llm, prompt=prompt)
    cl.user_session.set("chat_chain", chat_chain)

    # --- Setup for RAG Chat (only if this profile is selected) ---
    if chat_profile == "Repo Q&A":
        await cl.Message(content="Loading repository indexes for **Repo Q&A** mode...").send()
        
        try:
            with open(CONFIG_PATH, "r") as f:
                config = yaml.safe_load(f)
            repo_configs = config.get("repositories", [])
        except FileNotFoundError:
            await cl.Message(content=f"Error: `{CONFIG_PATH}` not found.").send()
            return

        emb = OllamaEmbeddings(model=EMB_MODEL)
        list_of_retrievers = []

        for repo in repo_configs:
            repo_name = repo.get("name")
            index_dir = FAISS_ROOT_DIR / repo_name
            if index_dir.exists():
                db = FAISS.load_local(str(index_dir), emb, allow_dangerous_deserialization=True)
                retriever = db.as_retriever(search_kwargs={'k': 5})
                list_of_retrievers.append(retriever)
            else:
                await cl.Message(content=f"Warning: Index for repo '{repo_name}' not found. Please run `build_indexes.py`.").send()

        if list_of_retrievers:
            ensemble_retriever = EnsembleRetriever(retrievers=list_of_retrievers)
            rag_chain = RetrievalQA.from_chain_type(
                llm=llm, chain_type="stuff", retriever=ensemble_retriever
            )
            cl.user_session.set("rag_chain", rag_chain)
            await cl.Message(content=f"Ready to answer questions about {len(list_of_retrievers)} repositories!").send()
        else:
            await cl.Message(content="No valid repository indexes were loaded.").send()
    else:
        await cl.Message(content="**General Chat** mode activated. I will not use your repositories as context.").send()


@cl.on_message
async def on_message(message: cl.Message):
    """
    This function now checks the chat profile to decide which chain to use.
    """
    chat_profile = cl.user_session.get("chat_profile")
    
    if chat_profile == "Repo Q&A":
        # --- Use the RAG Chain ---
        chain = cl.user_session.get("rag_chain")
        if not chain:
            await cl.Message(content="The RAG system is not configured. Please restart the chat in the 'Repo Q&A' profile.").send()
            return
        
        # Use the standard RAG invocation
        response = await cl.make_async(chain.invoke)({"query": message.content})
        answer = response.get("result")
        source_documents = response.get("source_documents")

        source_elements = []
        if source_documents:
            for i, doc in enumerate(source_documents):
                source_name = f"Source {i+1}: {os.path.basename(doc.metadata.get('source', ''))}"
                source_elements.append(
                    cl.Text(content=doc.page_content, name=source_name, display="inline")
                )
        await cl.Message(content=answer, elements=source_elements).send()

    else: # General Chat mode
        # --- Use the Direct Chat Chain ---
        chain = cl.user_session.get("chat_chain")
        if not chain:
            await cl.Message(content="The chat system is not configured. Please restart the chat.").send()
            return
            
        # Use a simpler invocation
        response = await cl.make_async(chain.invoke)({"question": message.content})
        await cl.Message(content=response.get("text")).send()