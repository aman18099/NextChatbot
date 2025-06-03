import sys
import os
import logging
from src.scripts.supabase_logger import SupabaseLogger
from dotenv import load_dotenv
from src.scripts.rag_utils import (
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
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

app = FastAPI()

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AskRequest(BaseModel):
    question: str
    user_id: str

security = HTTPBearer()
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"])
        user_id = payload["sub"]  # 'sub' is the user id in Supabase JWT
        return user_id
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

@app.get("/")
def root():
    return {"message": "RAG backend is running!"}

@app.post("/api/ask")
async def ask_endpoint(req: AskRequest, user_id=Depends(get_current_user)):
    user_query = req.question
    pdf_dir = "downloaded_pdfs"
    os.makedirs(pdf_dir, exist_ok=True)
    pdf_urls = [BOOK_PDF1, BOOK_PDF2]
    file_id = generate_common_file_id(pdf_urls)
    logger.info(f"Generated file_id: {file_id}", extra={"user_id": user_id})
    try:
        if not is_file_already_embedded(file_id, user_id):
            logger.info("Embeddings not found. Processing PDF...", extra={"user_id": user_id})
            local_pdf_paths = download_pdfs(pdf_urls, pdf_dir, user_id)
            logger.info(f"PDF downloaded to: {local_pdf_paths}", extra={"user_id": user_id})
            if not local_pdf_paths:
                logger.error("Failed to download PDF", extra={"user_id": user_id})
                return JSONResponse(status_code=500, content={"error": "Failed to download PDF"})
            all_text = extract_texts_parallel(local_pdf_paths, user_id)
            logger.info(f"Extracted text: {all_text}")
            logger.info("Text extracted from PDF", extra={"user_id": user_id})
            chunks = chunk_text(all_text, user_id)
            logger.info("Text chunked into smaller pieces", extra={"user_id": user_id})
            embeddings = embed_chunks(chunks, user_id)
            logger.info("Embeddings generated for text chunks", extra={"user_id": user_id})
            if embeddings is None:
                logger.error("Failed to generate embeddings.", extra={"user_id": user_id})
                return JSONResponse(status_code=500, content={"error": "Failed to generate embeddings"})
            store_embeddings(chunks, embeddings, file_id, user_id)
            logger.info("Stored embeddings and chunks in Supabase", extra={"user_id": user_id})
        else:
            logger.info("Embeddings already present for this file. Skipping processing.", extra={"user_id": user_id})
        top_chunks = get_relevant_chunks(user_query, file_id, user_id)
        logger.info(f"Retrieved {len(top_chunks)} relevant chunks for the query", extra={"user_id": user_id})
        answer = ask_llm(top_chunks, user_query, user_id)
        logger.info(f"LLM answered the question based on context {answer}", extra={"user_id": user_id})
        store_query_and_answer(file_id, user_query, answer, user_id)
        logger.info("Stored query and answer in Supabase", extra={"user_id": user_id})
        return {"output": answer}
    except Exception as e:
        logger.error(f"Error in /api/ask: {e}", extra={"user_id": user_id})
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    app.run()

