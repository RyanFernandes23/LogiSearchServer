from utils.utility import scrape_website, search_text
from webscraper import extract_text
from typing import List, Tuple, Optional
import os
import logging
from langchain.text_splitter import RecursiveCharacterTextSplitter
from chromadb import PersistentClient
from chromadb.utils import embedding_functions
from chromadb.api.types import Documents, Embeddings
from langchain.schema import Document
from langchain.prompts import ChatPromptTemplate
import uuid
import shutil
from datetime import datetime, timedelta
import time
from os import path, chmod, unlink, stat

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 200
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def save_scraped_text(search_results: List[str]) -> List[Tuple[str, str]]:
    """Process search results into (content, source) tuples"""
    documents = []
    for link in search_results:
        try:
            soup = scrape_website(link)
            text = extract_text(soup, class_name=None)

            if text:
                content = ' '.join(text) if isinstance(text, list) else text
                documents.append((content, link))

        except Exception as e:
            logger.warning(f"Failed to scrape {link}: {str(e)}")

    return documents

def grab_links(query: str) -> List[str]:
    """Retrieve search result URLs for a query"""
    results = search_text(query)
    return [result['href'] for result in results if 'href' in result]

def chunk_text(
    documents: List[Tuple[str, str]],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP
) -> List[Document]:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    return [
        Document(
            page_content=chunk,
            metadata={"source": source}
        )
        for content, source in documents
        for chunk in text_splitter.split_text(content)
    ]

# def create_vector_db(
#     documents: List[Document],
#     collection_name: str,
#     embedding_model: str = EMBEDDING_MODEL
# ) -> Optional[PersistentClient]:
#     """Create and return Chroma DB instance with session directory"""
#     try:
#         collection_path = f".chroma/{collection_name}"
#         chroma_client = PersistentClient(path=collection_path)
#         embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=embedding_model)
#         collection = chroma_client.create_collection(name=collection_name, embedding_function=embedding_func)

#         for idx, doc in enumerate(documents):
#             doc_id = str(uuid.uuid4())  # Generate unique ID
#             collection.add(
#                 ids=[doc_id],
#                 documents=[doc.page_content],
#                 metadatas=[doc.metadata]
#             )

#         logger.info(f"Created vector DB collection: {collection_name}")
#         return collection

#     except Exception as e:
#         logger.error(f"Failed to create vector DB: {str(e)}")
#         return None

def create_prompt(query: str, results: Documents) -> str:
    PROMPT_TEMPLATE = """You are a helpful assistant that can answer questions about the context provided.
    Question: {query}
    Context: {context}
    Don't say like \"Here is the summary\" or similar phrases. you can break down the answer into multiple points.
    tell as much detailed as possible, if the context is not related to the question or empty, say " i am not sure about that"
    and continue with your right answer.
    important: write in markdown format always(use # for headings, * for bold, _ for italics, and ** for bold italics)"""

    context_text = "\n\n---\n\n".join(results)
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    return prompt_template.format(query=query, context=context_text)



