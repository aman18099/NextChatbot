import requests
import logging
import os
from multiprocessing import Pool, cpu_count
from io import StringIO
from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams
import re
from langchain.text_splitter import RecursiveCharacterTextSplitter
import openai
import tiktoken
from dotenv import load_dotenv
from src.scripts.supabase_config import create_supabase_client

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ---------- Load ENV ----------
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")
MAX_TOKENS = os.getenv("MAX_TOKENS", 300000)
supabase = create_supabase_client()
# -----------------------------

import hashlib

def generate_common_file_id(pdf_urls):
    # Sort URLs to ensure consistent ID regardless of order
    combined_string = ''.join(sorted(pdf_urls))
    return hashlib.sha256(combined_string.encode()).hexdigest()[:16]

def download_pdfs(pdf_urls, output_dir="downloaded_pdfs", user_id=None):
    os.makedirs(output_dir, exist_ok=True)
    downloaded_paths = []
    for idx, pdf_url in enumerate(pdf_urls):
        try:
            filename = f"book{idx+1}.pdf"
            output_path = os.path.join(output_dir, filename)
            
            logger.info(f"Downloading PDF from: {pdf_url}", extra={"user_id": user_id})
            logger.info(f"Saving PDF to: {output_path}", extra={"user_id": user_id})

            response = requests.get(pdf_url, stream=True)
            response.raise_for_status()

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            downloaded_paths.append(output_path)
            logger.info(f"PDF downloaded successfully to: {output_path}", extra={"user_id": user_id})

        except Exception as e:
            logger.error(f"Failed to download PDF from {pdf_url}: {e}", extra={"user_id": user_id})
    return downloaded_paths




def extract_text_from_pdf(pdf_path,user_id, encoding='utf-8'):
    try:
        laparams = LAParams(
            line_margin=0.5,
            word_margin=0.1,
            char_margin=2.0,
            boxes_flow=0.5,
            detect_vertical=True,
            all_texts=True
        )
        output = StringIO()
        with open(pdf_path, 'rb') as pdf_file:
            extract_text_to_fp(
                pdf_file,
                output,
                laparams=laparams,
                output_type='text',
                codec=encoding
            )
        text = output.getvalue()
        output.close()

        cleaned_text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
        # logger.info(f"Text extracted from: {pdf_path}", extra={"user_id": user_id})
        return cleaned_text

    except Exception as e:
        # logger.error(f"Error processing {pdf_path}: {e}", extra={"user_id": user_id})
        return ""


from multiprocessing import Pool, cpu_count
def extract_texts_parallel(pdf_paths,user_id=None, num_workers=None):
    # print(pdf_paths)
    if num_workers is None:
        num_workers = max(1, cpu_count() - 1)
    args = [(pdf_path, user_id) for pdf_path in pdf_paths]
    with Pool(processes=num_workers) as pool:
        all_texts = pool.starmap(extract_text_from_pdf, args)
    # print(f"Extracted texts from {len(all_texts)} PDFs")
    return "\n".join(all_texts)


def chunk_text(text: str, user_id,
               chunk_size: int = 1000,
               overlap: int = 200,
               min_chunk_size: int = 100) -> list[dict]:
    """
    Chunk text into semantically meaningful segments with metadata.
    
    Args:
        text (str): Input text to chunk
        chunk_size (int): Maximum size of each chunk
        overlap (int): Number of characters to overlap between chunks
        min_chunk_size (int): Minimum size for any chunk
        
    Returns:
        list[dict]: List of chunks with metadata
    """
    separators = ["\n\n", "\n", ".", "!", "?", ";", ":", " "]
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        length_function=len,
        separators=separators,
        is_separator_regex=False
    )
    
    raw_chunks = splitter.split_text(text)
    
    processed_chunks = []
    for i, chunk in enumerate(raw_chunks):
        chunk = chunk.strip()
        
        if len(chunk) < min_chunk_size:
            continue
            
        # Create chunk with metadata
        chunk_dict = {
            'content': chunk,
            'metadata': {
                'chunk_id': i,
                'char_length': len(chunk),
                'start_char': text.find(chunk),
                'end_char': text.find(chunk) + len(chunk),
                # Detect if chunk contains special sections
                'contains_table': bool(re.search(r'table|figure|fig\.', chunk.lower())),
                'contains_list': bool(re.search(r'^\s*[-•*]\s|^\s*\d+\.\s', chunk, re.MULTILINE)),
                'is_header': bool(re.search(r'^[A-Z\s]{5,}$', chunk, re.MULTILINE))
            }
        }
        
        processed_chunks.append(chunk_dict)
    logger.info(f"Total Chunks Created: {len(processed_chunks)}", extra={"user_id": user_id})
    logger.info(f"Sample Chunk: {processed_chunks[:1]}", extra={"user_id": user_id})
    return processed_chunks

def count_tokens(text: str, model: str = EMBED_MODEL) -> int:
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

def embed_chunks(chunks: list[dict], user_id) -> list[list[float]]:
    logger.info("Embedding chunks...", extra={"user_id": user_id})
    try:
        all_embeddings = []
        batch = []
        token_count = 0

        for i, chunk in enumerate(chunks):
            text = chunk["content"]
            logger.info(f"Chunk {i+1}/{len(chunks)} preview: {text[:100]}", extra={"user_id": user_id})
            tokens = count_tokens(text)

            if token_count + tokens > MAX_TOKENS:
                response = openai.Embedding.create(
                    model=EMBED_MODEL,
                    input=[c["content"] for c in batch]
                )
                all_embeddings.extend([item["embedding"] for item in response["data"]])
                batch = [chunk]
                token_count = tokens
            else:
                batch.append(chunk)
                token_count += tokens

        if batch:
            response = openai.Embedding.create(
                model=EMBED_MODEL,
                input=[c["content"] for c in batch]
            )
            all_embeddings.extend([item["embedding"] for item in response["data"]])

        return all_embeddings

    except Exception as e:
        logger.error(f"Error creating embeddings: {e}", extra={"user_id": user_id})
        return None

def store_embeddings(chunks, embeddings, file_id, user_id):
    for chunk, embedding in zip(chunks, embeddings):
        supabase.table("pdf_chunks").insert({
            "file_id": file_id,
            "content": chunk["content"],
            "embedding": embedding,
            "metadata": {"chunk_index": chunk.get("chunk_index", 0)},
            "user_id" : user_id
        }).execute()
    logger.info("Stored embeddings to Supabase.", extra={"user_id": user_id})
    

def is_file_already_embedded(file_id, user_id):
    result = supabase.table("pdf_chunks").select("id").eq("file_id", file_id).limit(1).execute()
    exists = len(result.data) > 0
    logger.info(f"File already embedded: {exists}", extra={"user_id": user_id})
    return len(result.data) > 0


def get_relevant_chunks(user_query, file_id,user_id, top_k=5):
    query_embedding = openai.Embedding.create(
        model="text-embedding-3-small",
        input=user_query
    )["data"][0]["embedding"]

    result = supabase.rpc("match_pdf_chunks", {
        "query_embedding": query_embedding,
        "match_count": top_k,
        "file_id": file_id
    }).execute()

    logger.info(f"Relevant chunks fetched: {len(result.data) if result and result.data else 0}", extra={"user_id": user_id})

    return result.data


def ask_llm(context_chunks: list[dict], question: str, user_id) -> str:
    texts = [chunk['content'] for chunk in context_chunks]
    context = "\n\n".join(texts)
    prompt = (
        # "You are a helpful assistant. "
        # "Use ONLY the context below to answer, and format in Markdown with bullet points if helpful. please use '\n' if you are trying to break the line.\n\n"
        # f"---\n{context}\n---\n"
        # f"**Q:** {question}\n**A:**"
            "You are a helpful assistant. "
    "Use ONLY the context below to answer the question. "
    "Format the response in Markdown, using bullet points if helpful. "
    "Use '\\n' explicitly for line breaks.\n\n"
    "---\n"
    f"{context}\n"
    "---\n\n"
    f"**Q:** {question}\n"
    "**A:**"
    )
    try: 
        resp = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error during LLM query: {e}", extra={"user_id": user_id})
        return "An error occurred while generating the response."



def store_query_and_answer(file_id: str, question: str, answer: str, user_id):
    try: 
        data = {
            "file_id": file_id,
            "question": question,
            "answer": answer,
            "user_id" : user_id
        }
        response = supabase.table("queries").insert(data).execute()
        logger.info("Stored user query and answer.", extra={"user_id": user_id})
        return response
    except Exception as e:
        logger.error(f"Error storing query and answer: {e}", extra={"user_id": user_id})
        return None