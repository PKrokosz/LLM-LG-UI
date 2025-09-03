from contextlib import contextmanager
from pathlib import Path
import json, time, uuid, hashlib

LOG_ROOT = Path("user_logs/traces")
LOG_ROOT.mkdir(parents=True, exist_ok=True)

def _now():
    t = time.time()
    return t, time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(t))

def new_run_id():
    return time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]

def emit(run_id: str, stage: str, **fields):
    t, iso = _now()
    rec = {"run_id": run_id, "stage": stage, "ts": t, "ts_iso": iso, **fields}
    p = LOG_ROOT / f"{run_id}.jsonl"
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

def save_artifact(run_id: str, name: str, content):
    adir = LOG_ROOT / run_id / "artifacts"
    adir.mkdir(parents=True, exist_ok=True)
    out = adir / name
    mode = "wb" if isinstance(content, (bytes, bytearray)) else "w"
    with out.open(mode, encoding=None if "b" in mode else "utf-8") as f:
        f.write(content)
    return str(out)

def prompt_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]

@contextmanager
def trace_run(meta: dict):
    rid = new_run_id()
    emit(rid, "trace.start", meta=meta)
    t0 = time.time()
    try:
        yield rid
        emit(rid, "trace.end", total_ms=int((time.time()-t0)*1000), ok=True)
    except Exception as e:
        emit(rid, "trace.error", error=str(e))
        emit(rid, "trace.end", total_ms=int((time.time()-t0)*1000), ok=False)
        raise
