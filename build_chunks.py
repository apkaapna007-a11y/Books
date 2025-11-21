import csv, json, os, glob, re, datetime
from pathlib import Path

SRC_DIR = "/project/workspace"
OUT_PATH = "/project/workspace/chunks.csv"
CHUNK_TOKENS = 1200
OVERLAP_TOKENS = 200

files = sorted(glob.glob(os.path.join(SRC_DIR, "*.txt")))

def filename_to_title(path: str):
    base = Path(path).stem
    s = base.replace("&", " and ")
    s = s.replace("_", " ")
    s = re.sub(r"[-]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s.title()

def topic_from_title(title: str):
    parts = title.split()
    return " ".join(parts[:3]) if len(parts) > 3 else title

def chunk_by_tokens(text: str, size: int, overlap: int):
    words = re.findall(r"\S+", text)
    n = len(words)
    chunks = []
    if n == 0:
        return chunks
    start = 0
    idx = 1
    while start < n:
        end = min(n, start + size)
        chunk_words = words[start:end]
        chunk_text = " ".join(chunk_words).strip()
        chunks.append((idx, chunk_text))
        if end >= n:
            break
        start = end - overlap
        if start < 0:
            start = 0
        idx += 1
    return chunks

rows = []
for fp in files:
    try:
        with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read().strip()
    except Exception:
        content = ''
    title = filename_to_title(fp)
    topic = topic_from_title(title)
    subtopic = ''
    index_path = ''
    chunks = chunk_by_tokens(content, CHUNK_TOKENS, OVERLAP_TOKENS)
    if not chunks:
        # create an empty row placeholder
        chunks = [(1, '')]
    for idx, chunk_text in chunks:
        summary_src = chunk_text[:400]
        summary = re.sub(r"\s+", " ", summary_src).strip()
        meta = {
            "source_file": os.path.basename(fp),
            "imported_at": datetime.datetime.utcnow().isoformat() + 'Z',
            "bytes": os.path.getsize(fp) if os.path.exists(fp) else None,
            "generator": "capy-chunks-v1",
            "chunk_size_tokens": CHUNK_TOKENS,
            "overlap_tokens": OVERLAP_TOKENS
        }
        rows.append({
            "meta": json.dumps(meta, ensure_ascii=False),
            "index_path": index_path,
            "title": title,
            "topic": topic,
            "subtopic": subtopic,
            "content": chunk_text,
            "summary": summary,
            "chunk_no": idx,
        })

fieldnames = ["meta","index_path","title","topic","subtopic","content","summary","chunk_no"]
with open(OUT_PATH, 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
    w.writeheader()
    for r in rows:
        w.writerow(r)

print(f"Wrote {len(rows)} chunk rows to {OUT_PATH}")
