import os
import faiss
from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from transformers import pipeline
from google import genai

# ---------- Configuration ----------
FLAN_MODEL = os.getenv("FLAN_MODEL", "google/flan-t5-small")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# ---------- Models & Clients ----------
embedder = SentenceTransformer("all-MiniLM-L6-v2")
gen_local = pipeline("text2text-generation", model=FLAN_MODEL)
qa_model = pipeline("question-answering", model="deepset/roberta-base-squad2", framework="pt")
client = genai.Client(api_key="AIzaSyA-VlPUk31E5w-u6VAQ3k3uEL4EeoYy8Jo") 

app = FastAPI()


# ---------- FAQ Loader ----------
def load_faq_txt(path="project_knowledge.txt"):
    faq_dict = {}
    with open(path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    current_q = None
    for line in lines:
        if line.lower().startswith("q:"):
            current_q = line[2:].strip()
        elif line.lower().startswith("a:") and current_q:
            faq_dict[current_q] = line[2:].strip()
            current_q = None
    return faq_dict


FAQ = load_faq_txt("project_knowledge.txt")
FAQ_QS = list(FAQ.keys())
FAQ_AS = list(FAQ.values())
FAQ_Q_EMB = embedder.encode(FAQ_QS) if FAQ_QS else []
print(f"Loaded {len(FAQ_QS)} FAQ entries from TXT")


# ---------- Request Model ----------
class ChatRequest(BaseModel):
    message: str


# ---------- Helpers ----------
def ensure_full_answer(answer: str, query: str, context: str = None) -> str:
    """Guarantee answer is 2 to 3 sentences using local generator if too short."""
    if not answer or len(answer.split()) < 10:
        prompt = (
            f"Context:\n{context}\n\n" if context else ""
        ) + f"Question: {query}\n\nAnswer in 2-3 complete sentences."
        gen = gen_local(prompt, max_length=250, do_sample=True, temperature=0.4, top_p=0.9)
        return gen[0]["generated_text"].strip()
    return answer


def match_faq(query: str, threshold: float = 0.65):
    if not FAQ_QS:
        return None, None

    query_emb = embedder.encode([query])
    index = faiss.IndexFlatL2(FAQ_Q_EMB.shape[1])
    index.add(FAQ_Q_EMB)
    distances, indices = index.search(query_emb, 1)

    best_idx = indices[0][0]
    best_dist = distances[0][0]

    # Normalize distance → similarity
    similarity = 1 / (1 + best_dist)
    if similarity >= threshold:
        return FAQ_QS[best_idx], FAQ_AS[best_idx]
    return None, None


def answer_with_gemini(query: str):
    instruction = (
        "You are a helpful assistant for HireAI Pro. "
        "Answer the following question in 2–3 full sentences.\n\n"
        f"Question: {query}"
    )
    try:
        resp = client.models.generate_content(model=GEMINI_MODEL, contents=instruction)
        raw_answer = getattr(resp, "text", "").strip()
    except Exception as e:
        raw_answer = f"Error fetching from Gemini: {e}"
    final_answer = ensure_full_answer(raw_answer, query)
    return final_answer, "gemini"
