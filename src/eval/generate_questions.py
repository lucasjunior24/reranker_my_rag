"""1.7 Gera perguntas candidatas (sintéticas) a partir de chunks dos splits val e test.

Saída: data/eval/candidates.jsonl -> revisar à mão (campo "aprovada": true/false)
e depois rodar `python -m src.eval.build_qrels`.
"""
import json
import random
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from tqdm import tqdm

from src.ingest.split import doc_to_split

load_dotenv()

PROMPT = """Você é um pesquisador da Amazônia. Leia o trecho abaixo e escreva UMA pergunta
que um pesquisador faria e que o trecho responde. Não copie frases do trecho; use
outras palavras. A pergunta deve fazer sentido sozinha, sem mencionar "o trecho".
Responda apenas com JSON: {{"question": "...", "answer": "..."}}

Trecho:
{chunk}"""


def load_chunks(path: str = "data/processed/chunks.jsonl") -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f]


def generate(n: int = 300, seed: int = 42, min_chars: int = 300,
             out: str = "data/eval/candidates.jsonl") -> None:
    client = genai.Client()  # lê GEMINI_API_KEY do ambiente
    split_of = doc_to_split()
    pool = [c for c in load_chunks()
            if split_of.get(c["doc_id"]) in ("val", "test") and len(c["text"]) >= min_chars]
    random.Random(seed).shuffle(pool)

    Path(out).parent.mkdir(parents=True, exist_ok=True)
    done = sum(1 for _ in open(out, encoding="utf-8")) if Path(out).exists() else 0
    with open(out, "a", encoding="utf-8") as f:
        for c in tqdm(pool[done:n]):  # retoma de onde parou
            try:
                resp = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=PROMPT.format(chunk=c["text"]),
                    config={"response_mime_type": "application/json"},
                )
                qa = json.loads(resp.text)
            except Exception as e:
                print(f"[ERRO] {c['chunk_id']}: {e}")
                continue
            rec = {
                "question": qa["question"],
                "answer": qa["answer"],
                "relevant_chunks": [c["chunk_id"]],
                "origin": "sintetica",
                "split": split_of[c["doc_id"]],
                "aprovada": None,  # preencher na revisão manual
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()


if __name__ == "__main__":
    generate()
