# Ragnarok - Local RAG Chat Application
This project provides a local question-answering system using a RAG (Retrieval-Augmented Generation) pipeline. It leverages local LLMs via Ollama and a Chainlit UI to allow users to query multiple code repositories.

### Features
- Local First: All components (LLM, embeddings, vector store) run locally, ensuring data privacy.
- Multi-Repo Support: Query across several codebases simultaneously using a single interface.
- Configurable: Easily configure repositories and models via a config.yml file.
- Interactive UI: A user-friendly chat interface powered by Chainlit.
- Language-Aware: Uses tree-sitter for intelligent, language-specific chunking of source code files, including Java, Python and JavaScript. 
  - If you want support a specific language not here represented, it's fairly straight-forward to edit the script - [check this!](extend_lang_support.md)

### Prerequisites
Before you begin, ensure you have the following installed:

- Python 3.11:  Consider using `pyenv` to manage Python versions.  [🌍](https://github.com/pyenv/pyenv)
- Ollama: Make sure the Ollama service is running. The application will attempt to pull the required models, but you can also pull them manually beforehand (e.g., ollama pull gemma3:12b). [🌍](https://ollama.com/download)

## Setup and Installation
### Clone the Repository

```
git clone <your-repo-url>
cd <your-repo-name>
````
___

### Set Local Python Version and Virtual Environment

Make sure you have a version of 3.11 installed via pyenv (e.g., 3.11.12)

`pyenv local 3.11.12`

Create and Activate Virtual Environment

```
python -m venv ragnarok_venv
source ragnarok_venv/bin/activate
(On Windows, use venv\Scripts\activate)
````

### Install Dependencies

Install all required packages from the requirements.txt file.

`pip install -r requirements.txt`

## Configuration

Edit config.yml: This file is the single source of configuration for your repositories and models.

Add Your Repositories: Update the repositories list with the name (used for the index folder) and path for each repository you want to query.

Choose Your Models: Set the LLM and embedding models you wish to use from [Ollama](https://ollama.com/).

Example config.yml:
```
models:
  llm: gemma3:12b
  embedding: mxbai-embed-large

# List of repositories to index
repositories:
  - name: project-aperture-science
    path: /path/to/your/first/repo/
  - name: project-1-ring-2-rule
    path: /path/to/your/second/repo/
```

## Usage
This application uses a two-step process: first, you build the indexes for your repositories, and second, you run the chat application.

### Step 1: Build the Indexes

Run the indexer script. This will read your config.yml, process the files in each repository, and create a local FAISS index for each one inside the faiss_indexes/ directory.

`python build_indexes.py`

_You only need to re-run this step when your source code changes or when you update the repository list in config.yml._

### Step 2: Run the Chat Application

Once the indexes are built, start the Chainlit UI.

`chainlit run app_ui.py -w`

_The -w flag will automatically reload the app if you make changes to app_ui.py._

Open the URL provided in your terminal (usually http://localhost:8000) to start asking questions.

## Troubleshooting

### TypeError or ImportError related to tree-sitter

If you encounter errors related to tree-sitter or tree-sitter-languages during installation or when running build_indexes.py, it is likely due to a Python version incompatibility. This project is confirmed to work with Python 3.11. Please ensure you are using a Python 3.11.x environment managed by pyenv.

If the problem persists, try a clean re-installation of the packages:

```
pip uninstall tree-sitter tree-sitter-languages -y
pip install --no-cache-dir "tree-sitter>=0.20.4,<0.22.0" tree-sitter-languages
```