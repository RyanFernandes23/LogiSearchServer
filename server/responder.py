import os
import logging
from typing import Optional
from groq import Groq
from chunking_db import (
    grab_links, save_scraped_text, chunk_text,
    create_prompt
)
from dotenv import load_dotenv
import uuid
from chromadb import PersistentClient, Settings
from chromadb.utils import embedding_functions


load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
GROQ_MODEL = "llama3-70b-8192"
TEMPERATURE = 0.7
MAX_TOKENS = 1000
SIMILARITY_SEARCH_K = 3
MAX_DOCUMENTS = 70

collection_path = ".chroma/my_collection"
chroma_client = PersistentClient(path=collection_path,settings=Settings(allow_reset=True))
embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
# collection = chroma_client.create_collection(name="my_collection", embedding_function=embedding_func)


def get_response(query: str) -> Optional[str]:
    """Generate response using RAG pipeline with proper resource cleanup"""
    session_id = str(uuid.uuid4())[:8]
    collection_name = f"session_{session_id}"

    try:
        # Retrieve and process links
        logger.info("Fetching relevant links...")
        # flush_chroma_directory()
        links = grab_links(query)
        if not links:
            logger.warning("No links found for the query.")
            return "No relevant information found."

        # Scrape and chunk documents
        logger.info("Scraping and processing documents...")
        scraped_docs = save_scraped_text(links)
        documents = chunk_text(scraped_docs)
        logger.info(f"Created {len(documents)} document chunks.")

        if len(documents) > MAX_DOCUMENTS:
            logger.warning(f"Limiting documents to {MAX_DOCUMENTS}")
            documents = documents[:MAX_DOCUMENTS]

        # Create vector DB
        
        logger.info("Creating vector database...")
        collection = chroma_client.get_or_create_collection(name="my_collection", embedding_function=embedding_func)

        for idx, doc in enumerate(documents):
            doc_id = str(uuid.uuid4())  # Generate unique ID
            collection.add(
                ids=[doc_id],
                documents=[doc.page_content],
                metadatas=[doc.metadata]
            )

        logger.info(f"Created vector DB collection: {collection_name}")
        if not collection:
            return "Failed to initialize knowledge base."

        # Similarity search
        logger.info(f"Running similarity search: {query}")
        results = collection.query(query_texts=[query], n_results=SIMILARITY_SEARCH_K)
        logger.info(f"Found {len(results['documents'][0])} relevant results.")

        # Generate prompt
        logger.info("Creating prompt...")
        prompt = create_prompt(query, results['documents'][0])
        logger.debug(f"Prompt content: {prompt[:200]}...")

        # Get Groq response
        logger.info("Calling Groq API...")
        client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS
        )

        return response.choices[0].message.content

    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        return "Unable to generate response due to an internal error."

    finally:
        # Cleanup vector DB collection
        logger.info("Cleaning up vector database...")
        
        try:
            chroma_client.reset()
            logger.info("Database reset successfully")
        except Exception as e:
            logger.error(f"Error resetting database: {e}")
        
        # delete_collections(collection_name)

if __name__ == "__main__":
    try:
        query = "Where can we find snake plants?"
        response = get_response(query)
        print("\nResponse:", response)
    except Exception as e:
        logger.error(f"Execution failed: {e}")