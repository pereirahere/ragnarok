# Extending Language Support

The application is designed to be extensible. You can add support for any new programming language that is supported by LangChain's `LanguageParser` by modifying two files.

Here is how to add support for a new language, using **C# (`.cs`)** as an example.

### Step 1: Check for Language Support

First, ensure that `langchain_text_splitters.Language` has an enum for your desired language (e.g., `Language.CSHARP`). You can check the LangChain documentation or source code for a complete list of supported languages.

### Step 2: Update the Loader Factory

Open `loaders/loader_factory.py`. You only need to add one line to the `lang_map` dictionary within the `get_loader` method.

Python

```
# In loaders/loader_factory.py

# ... inside the get_loader method
        lang_map = {
            Language.JAVA: "java",
            Language.PYTHON: "py",
            Language.JS: "js",
            Language.SH: "sh",
            Language.CSHARP: "cs", # <-- ADD THIS LINE
        }
# ...

```

### Step 3: Update the Indexer Script

Open `build_indexes.py`. You need to make two small additions to the `build_index_for_repo` function.

**A. Add the new language to the `desired_loader_types` list:**

Python

```
# In build_indexes.py, inside build_index_for_repo()

    desired_loader_types = [
        Language.JAVA,
        Language.PYTHON,
        Language.JS,
        Language.SH,
        Language.CSHARP, # <-- ADD THIS LINE
        "general_unstructured"
    ]

```

**B. Add a corresponding splitter to the `splitters` dictionary:**

Python

```
# In build_indexes.py, inside build_index_for_repo()

    splitters = {
        Language.JAVA: RecursiveCharacterTextSplitter.from_language(...),
        Language.PYTHON: RecursiveCharacterTextSplitter.from_language(...),
        Language.JS: RecursiveCharacterTextSplitter.from_language(...),
        Language.SH: RecursiveCharacterTextSplitter.from_language(...),
        # ADD THIS LINE
        Language.CSHARP: RecursiveCharacterTextSplitter.from_language(language=Language.CSHARP, chunk_size=1000, chunk_overlap=200),
        "general": RecursiveCharacterTextSplitter(...)
    }

```

#### Step 4: Re-run the Indexer

That's it. Now, simply run the indexer again. It will automatically find, parse, and index the new file types you've configured.

Bash

```
python build_indexes.py
```