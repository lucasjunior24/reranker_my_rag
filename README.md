# reranker_my_rag

Embeddings amazônicos + agente RAG. Veja [todo.md](todo.md) e o plano do projeto.

## Setup

```bash
uv sync            # ou: pip install -e .
cp .env.example .env   # preencha GEMINI_API_KEY
```

Windows: instale Tesseract (com o idioma `por`) e Ghostscript e coloque no PATH (necessário só para OCR).

## Etapa 1: pipeline de dados

1. Preencha `data/sources.csv` (colunas: doc_id, titulo, fonte, url, licenca, formato, escaneado, idioma).
2. Rode em ordem:

```bash
python -m src.ingest.download            # 1.2  data/raw + sha256
python -m src.ingest.extract             # 1.3  data/interim (OCR se preciso)
python -m src.ingest.clean               # 1.4  data/processed/clean
python -m src.ingest.split               # 1.6  data/splits.json (por documento)
python -m src.chunking.chunk --size 512 --overlap 64   # 1.5  data/processed/chunks.jsonl
python -m src.eval.generate_questions    # 1.7  data/eval/candidates.jsonl (precisa de splits e chunks)
# revisar candidates.jsonl (aprovada: true/false) e escrever data/eval/manual.jsonl
python -m src.eval.build_qrels           # 1.7  data/eval/qrels.jsonl
```

`data/eval/manual.jsonl`, uma pergunta por linha:

```json
{"question": "...", "answer": "...", "relevant_chunks": ["madeira_001_p12_c3"]}
```

Observação: se mudar o chunking depois de criar as perguntas, os `chunk_id` mudam e o `qrels` precisa ser refeito. Defina o chunking antes de gerar as perguntas.

## Versionamento (1.8)

```bash
git init
dvc init
dvc add data/raw data/processed
dvc remote add -d storage gdrive://<id-da-pasta>
git add data/*.dvc .gitignore .dvc/config data/sources.csv data/splits.json data/eval/qrels.jsonl
git commit -m "Corpus inicial e conjunto de avaliação"
dvc push
```
