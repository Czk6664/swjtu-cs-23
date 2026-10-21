import hashlib, json
from pathlib import Path

base = Path(__file__).resolve().parent
manifest = json.loads((base / "manifest.json").read_text(encoding="utf-8"))
target = base.parent / manifest["filename"]
digest = hashlib.sha256()
size = 0
with target.open("xb") as output:
    for name in manifest["parts"]:
        with (base / name).open("rb") as source:
            while block := source.read(1024 * 1024):
                output.write(block)
                digest.update(block)
                size += len(block)
if size != manifest["size"] or digest.hexdigest() != manifest["sha256"]:
    raise RuntimeError("Reconstruction checksum mismatch")
print(target)
