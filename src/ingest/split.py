"""1.6 Divide os documentos (não os chunks) em treino/val/teste: 70/15/15."""
import json
from pathlib import Path

from sklearn.model_selection import train_test_split


def make_splits(
    doc_ids: list[str],
    seed: int = 42,
    out: str = "data/splits.json",
    stratify: list[str] | None = None,
) -> dict:
    """`stratify`: tema de cada doc (mesma ordem de doc_ids), opcional."""
    train, rest, _, rest_strat = train_test_split(
        doc_ids, stratify or [0] * len(doc_ids), test_size=0.30, random_state=seed,
        stratify=stratify,
    )
    val, test = train_test_split(
        rest, test_size=0.50, random_state=seed,
        stratify=rest_strat if stratify else None,
    )
    splits = {"train": sorted(train), "val": sorted(val), "test": sorted(test)}
    Path(out).write_text(json.dumps(splits, indent=2), encoding="utf-8")
    return splits


def doc_to_split(splits_path: str = "data/splits.json") -> dict[str, str]:
    splits = json.loads(Path(splits_path).read_text(encoding="utf-8"))
    return {d: s for s, docs in splits.items() for d in docs}


if __name__ == "__main__":
    ids = sorted(p.stem for p in Path("data/processed/clean").glob("*.json"))
    s = make_splits(ids)
    print({k: len(v) for k, v in s.items()})
