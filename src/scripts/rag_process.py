import sys
import os
import sys
import logging
from src.scripts.supabase_logger import SupabaseLogger
from dotenv import load_dotenv
from rag_utils import (
    generate_common_file_id,
    download_pdfs,
    extract_texts_parallel,
    chunk_text,
    embed_chunks,
    store_embeddings,
    is_file_already_embedded,
    get_relevant_chunks,
    ask_llm,
    store_query_and_answer
)

load_dotenv()
BOOK_PDF1 = os.getenv("BOOK_PATH1")
BOOK_PDF2 = os.getenv("BOOK_PATH2")

# Setup logger
logger = logging.getLogger("pipeline_logger")
logger.setLevel(logging.INFO)

# Supabase log handler
logger.addHandler(SupabaseLogger())
console_handler = logging.StreamHandler()
logger.addHandler(console_handler)

user_query = sys.argv[1]
user_id = sys.argv[2]
# user_id = "e77725df-6465-43a0-96f0-b25ca514aa9b"
# user_query = "What are the best places to visit in Meghalaya during a 7-day scooty trip?"

# user_id="2345678"

def main():
    pdf_url = "https://mxkorpfjfdawaficaigo.supabase.co/storage/v1/object/sign/pdfs/Meghalaya_7_Day_Scooty_Trip_Itinerary_With_Images.pdf?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6InN0b3JhZ2UtdXJsLXNpZ25pbmcta2V5XzFhZmNhYTRlLWNjNWQtNGU5MC1iNWM0LTk1YjNhNzY1MDc1ZCJ9.eyJ1cmwiOiJwZGZzL01lZ2hhbGF5YV83X0RheV9TY29vdHlfVHJpcF9JdGluZXJhcnlfV2l0aF9JbWFnZXMucGRmIiwiaWF0IjoxNzQ4NzU2NTQxLCJleHAiOjE3NTEzNDg1NDF9.2Uumc24Qaxmnj06SOToVunB0L6Cckxsya8bOGMvstGs"
    pdf_dir = "downloaded_pdfs"
    os.makedirs(pdf_dir, exist_ok=True)
    pdf_urls = [BOOK_PDF1, BOOK_PDF2] 
    # Use PDF filename as a unique file_id for Supabase storage references
    file_id = generate_common_file_id(pdf_urls)
    logger.info(f"Generated file_id: {file_id}", extra={"user_id": user_id})
    # Check if file's embeddings already stored in Supabase
    if not is_file_already_embedded(file_id, user_id):
        logger.info("Embeddings not found. Processing PDF...", extra={"user_id": user_id})
        local_pdf_paths = download_pdfs(pdf_urls, pdf_dir,user_id)
        logger.info(f"PDF downloaded to: {local_pdf_paths}", extra={"user_id": user_id})
        if not local_pdf_paths:
            logger.error("Failed to download PDF", extra={"user_id": user_id})
            return

        logger.info(f"PDF saved at: {local_pdf_paths}", extra={"user_id": user_id})

        all_text = extract_texts_parallel(local_pdf_paths,user_id)
        logger.info(f"Extracted text: {all_text}")
        # return
        logger.info("Text extracted from PDF", extra={"user_id": user_id})

        chunks = chunk_text(all_text,user_id)
        logger.info("Text chunked into smaller pieces", extra={"user_id": user_id})

        embeddings = embed_chunks(chunks,user_id)  # Pass only the text content for embedding
        logger.info("Embeddings generated for text chunks", extra={"user_id": user_id})
        print(f"embedding {embeddings}")
        if embeddings is None:
            logger.error("Failed to generate embeddings.", extra={"user_id": user_id})  
        else:
            logger.info(f"Generated {len(embeddings)} embeddings", extra={"user_id": user_id})

        store_embeddings(chunks, embeddings, file_id,user_id)
        logger.info("Stored embeddings and chunks in Supabase", extra={"user_id": user_id})
    else:
        logger.info("Embeddings already present for this file. Skipping processing.", extra={"user_id": user_id})   


    top_chunks = get_relevant_chunks(user_query, file_id,user_id)
    logger.info(f"Retrieved {len(top_chunks)} relevant chunks for the query", extra={"user_id": user_id})

    answer = ask_llm(top_chunks, user_query,user_id)
    print(answer)
    logger.info(f"LLM answered the question based on context {answer}", extra={"user_id": user_id})

    store_query_and_answer(file_id, user_query, answer, user_id)
    logger.info("Stored query and answer in Supabase", extra={"user_id": user_id})

if __name__ == "__main__":
    main()

