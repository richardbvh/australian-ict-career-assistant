# rag_pipeline.py
from typing import List, Dict
from pathlib import Path
import os, re, yaml
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

# ---- Load config ----
try:
    with open("config.yml","r") as f:
        CFG = yaml.safe_load(f) or {}
except Exception:
    CFG = {}

RAG = CFG.get("rag", {}) or {}
PDF_PATH      = RAG.get("pdf_path", "data/sources/OSCA_27_ICT.pdf")
DB_DIR        = RAG.get("db_dir", "data/vector_db")
COLLECTION    = RAG.get("collection", "osca_ict")
EMB_MODEL     = RAG.get("embedding_model", "all-MiniLM-L6-v2")
USE_PYMUPDF   = bool(RAG.get("use_pymupdf", True))
CHUNK_SIZE    = int(RAG.get("chunk_size", 700) or 0)      # 0 => whole page
CHUNK_OVERLAP = int(RAG.get("chunk_overlap", 120))

def _load_pages_pypdf(pdf_path: str) -> List[Dict]:
    from pypdf import PdfReader
    reader = PdfReader(pdf_path)
    out = []
    for i, p in enumerate(reader.pages, start=1):
        txt = (p.extract_text() or "").strip()
        if txt:
            out.append({"page": i, "text": txt})
    return out

def _load_pages_pymupdf(pdf_path: str) -> List[Dict]:
    try:
        import fitz  # PyMuPDF
    except Exception:
        return _load_pages_pypdf(pdf_path)
    doc = fitz.open(pdf_path)
    out = []
    for i, page in enumerate(doc, start=1):
        raw = page.get_text("text") or ""
        txt = re.sub(r"[ \t]+\n", "\n", raw).strip()
        if txt:
            out.append({"page": i, "text": txt})
    return out

def _chunk_text(text: str, size: int, overlap: int) -> List[str]:
    if size <= 0:
        return [text]
    out, i = [], 0
    step = max(1, size - overlap)
    while i < len(text):
        seg = text[i:i+size].strip()
        if seg:
            out.append(seg)
        i += step
    return out

def _get_client_and_collection(create_if_missing: bool = True):
    Path(DB_DIR).mkdir(parents=True, exist_ok=True)
    emb_fn = SentenceTransformerEmbeddingFunction(model_name=EMB_MODEL)
    client = chromadb.PersistentClient(path=DB_DIR)
    try:
        col = client.get_collection(name=COLLECTION, embedding_function=emb_fn)
    except Exception:
        if not create_if_missing:
            raise
        col = client.create_collection(name=COLLECTION, embedding_function=emb_fn)
    return client, col

def build_index(pdf_path: str = PDF_PATH, force_rebuild: bool = False) -> None:
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found at {pdf_path}")

    client, col = _get_client_and_collection(create_if_missing=True)

    if force_rebuild and col.count() > 0:
        client.delete_collection(COLLECTION)
        _, col = _get_client_and_collection(create_if_missing=True)

    if col.count() > 0 and not force_rebuild:
        print(f"Collection '{COLLECTION}' already has {col.count()} items. Skipping rebuild.")
        return

    pages = _load_pages_pymupdf(pdf_path) if USE_PYMUPDF else _load_pages_pypdf(pdf_path)
    if not pages:
        raise ValueError("No text extracted from the PDF")

    ids, docs, metas = [], [], []
    for p in pages:
        for j, ck in enumerate(_chunk_text(p["text"], CHUNK_SIZE, CHUNK_OVERLAP)):
            ids.append(f"p{p['page']}-c{j}")
            docs.append(ck)
            metas.append({"page": p["page"], "source": os.path.basename(pdf_path)})

    col.add(ids=ids, documents=docs, metadatas=metas)
    print(f"Stored {len(docs)} chunks (from {len(pages)} pages) in '{COLLECTION}' @ {DB_DIR}")

def retrieve(query: str, top_k: int = 4) -> List[Dict]:
    _, col = _get_client_and_collection(create_if_missing=False)
    res = col.query(query_texts=[query], n_results=top_k)
    docs  = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    ids   = res.get("ids", [[]])[0]
    return [{"id": i, "text": d, "meta": m} for i, d, m in zip(ids, docs, metas)]

if __name__ == "__main__":
    import sys
    build_index(PDF_PATH, force_rebuild="--rebuild" in sys.argv)
