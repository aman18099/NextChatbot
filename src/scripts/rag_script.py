import os
import logging
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from src.scripts.supabase_logger import SupabaseLogger
from src.scripts.supabase_config import verify_jwt_token
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

# Initialize FastAPI
app = FastAPI()

# Load environment variables
load_dotenv()
BOOK_PDF1 = os.getenv("BOOK_PATH1")
BOOK_PDF2 = os.getenv("BOOK_PATH2")

# Configure logging
logger = logging.getLogger("pipeline_logger")
logger.setLevel(logging.INFO)
logger.addHandler(SupabaseLogger())
logger.addHandler(logging.StreamHandler())

# CORS settings (adjust as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic model for request body
class AskRequest(BaseModel):
    question: str
    user_id: str

@app.post("/api/ask")
async def ask_endpoint(req: AskRequest, request: Request):
    """FastAPI endpoint to handle RAG queries."""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        logger.error("Authorization header missing", extra={"user_id": req.user_id})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing"
        )

    try:
        # Extract and verify JWT token
        token = auth_header.split(" ")[1]
        payload = verify_jwt_token(token)
        logger.info(f"Token verified for user: {payload.get('sub')}", extra={"user_id": req.user_id})

        # Process RAG pipeline
        pdf_dir = "downloaded_pdfs"
        os.makedirs(pdf_dir, exist_ok=True)
        pdf_urls = [BOOK_PDF1, BOOK_PDF2]
        file_id = generate_common_file_id(pdf_urls)
        logger.info(f"Generated file_id: {file_id}", extra={"user_id": req.user_id})

        if not is_file_already_embedded(file_id, req.user_id):
            logger.info("Processing PDF...", extra={"user_id": req.user_id})
            local_pdf_paths = download_pdfs(pdf_urls, pdf_dir, req.user_id)
            if not local_pdf_paths:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to download PDF"
                )
            all_text = extract_texts_parallel(local_pdf_paths, req.user_id)
            chunks = chunk_text(all_text, req.user_id)
            embeddings = embed_chunks(chunks, req.user_id)
            if not embeddings:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to generate embeddings"
                )
            store_embeddings(chunks, embeddings, file_id, req.user_id)

        top_chunks = get_relevant_chunks(req.question, file_id, req.user_id)
        answer = ask_llm(top_chunks, req.question, req.user_id)
        store_query_and_answer(file_id, req.question, answer, req.user_id)
        return {"output": answer}

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error: {str(e)}", extra={"user_id": req.user_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Health check endpoint
@app.get("/")
def health_check():
    return {"status": "RAG API is running"}

if __name__ == "__main__":
    app.run()