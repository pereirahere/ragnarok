# loaders/loader_factory.py

from typing import Union
from langchain_text_splitters import Language
from langchain_community.document_loaders import DirectoryLoader, UnstructuredFileLoader
from langchain_core.document_loaders.base import BaseLoader
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers import LanguageParser

class LoaderFactory:
    """A factory for creating and providing specific document loaders."""

    def __init__(self, repo_path: str):
        """Initializes the factory with the base path for the repository."""
        if not repo_path:
            raise ValueError("A repository path must be provided.")
        self.repo_path = repo_path

    def get_loader(self, loader_type: Union[Language, str]) -> BaseLoader:
        """Returns a configured loader based on the specified type."""
        
        # Mapping for language-specific code parsers
        lang_map = {
            Language.JAVA: "java",
            Language.PYTHON: "py",
            Language.JS: "js",
        }

        if isinstance(loader_type, Language) and loader_type in lang_map:
            extension = lang_map[loader_type]
            return GenericLoader.from_filesystem(
                path=self.repo_path,
                glob=f"**/*.{extension}",
                suffixes=[f".{extension}"],
                parser=LanguageParser(language=loader_type, parser_threshold=10)
            )
        
        elif loader_type == "general_unstructured":
            # General-purpose loader for other common document types
            return DirectoryLoader(
                path=self.repo_path,
                glob="**/*[.pdf|.docx|.md|.txt|.xml|.json]",
                loader_cls=UnstructuredFileLoader,
                recursive=True,
                show_progress=True,
                use_multithreading=True,
                silent_errors=True
            )
        
        raise ValueError(f"Unsupported or unknown loader type: {loader_type}")