import csv, json, os, glob, datetime, re
from pathlib import Path

SRC_DIR = "/project/workspace"
OUT_PATH = "/project/workspace/dataset.csv"

files = sorted(glob.glob(os.path.join(SRC_DIR, "*.txt")))

# Normalize filename to a readable title
def filename_to_title(name: str):
    base = Path(name).stem
    # replace separators
    s = base.replace("&", " and ")
    s = s.replace("_", " ")
    s = re.sub(r"[-]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    # Fix common truncation typos lightly (optional)
    s = s.title()
    return s

# Simple topic derivation: use first token(s) until first dash in original filename

def topic_from_title(title: str):
    # take first 2 words as topic heuristic
    parts = title.split()
    if len(parts) <= 2:
        return title
    return " ".join(parts[:3])

rows = []
for fp in files:
    try:
        with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read().strip()
    except Exception as e:
        content = ''
    title = filename_to_title(fp)
    topic = topic_from_title(title)
    subtopic = ''
    index_path = ''
    # summary: first 500 chars from content (single-line)
    summary_src = (content or '')[:500]
    summary = re.sub(r"\s+", " ", summary_src).strip()
    meta = {
        "source_file": os.path.basename(fp),
        "imported_at": datetime.datetime.utcnow().isoformat() + 'Z',
        "bytes": os.path.getsize(fp) if os.path.exists(fp) else None,
        "generator": "capy-dataset-v1"
    }
    row = {
        "meta": json.dumps(meta, ensure_ascii=False),
        "index_path": index_path,
        "title": title,
        "topic": topic,
        "subtopic": subtopic,
        "content": content,
        "summary": summary,
        "chunk_no": 1,
    }
    rows.append(row)

# Write CSV (omit id/embedding/timestamps so DB defaults apply)
fieldnames = ["meta","index_path","title","topic","subtopic","content","summary","chunk_no"]
with open(OUT_PATH, 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
    w.writeheader()
    for r in rows:
        w.writerow(r)

print(f"Wrote {len(rows)} rows to {OUT_PATH}")
