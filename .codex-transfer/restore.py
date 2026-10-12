"""Restore only the exact tested files, then remove the temporary transport."""
import hashlib
import io
import json
import shutil
import tarfile
from pathlib import Path

root = Path.cwd().resolve()
transport = root / '.codex-transfer'
manifest = json.loads((transport / 'manifest.json').read_text())
assert manifest['version'] == 1
payload = b''.join((root / path).read_bytes() for path in manifest['chunks'])
assert hashlib.sha256(payload).hexdigest() == manifest['bundleSha256'], 'Bundle checksum mismatch'
expected = {file['path']: file for file in manifest['files']}
with tarfile.open(fileobj=io.BytesIO(payload), mode='r:xz') as archive:
    members = archive.getmembers()
    assert len(members) == len(expected) and {member.name for member in members} == set(expected)
    for member in members:
        path = Path(member.name)
        assert member.isfile() and not path.is_absolute() and '..' not in path.parts and '.git' not in path.parts
        target = (root / path).resolve()
        assert target.is_relative_to(root)
        raw = archive.extractfile(member).read()
        file = expected[member.name]
        assert len(raw) == file['rawLength'], member.name
        blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        assert blob == file['sha'], member.name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
tree = manifest['tree']
shutil.rmtree(transport)
(root / '.github/workflows/restore-tested-files.yml').unlink()
print('Restored all verified files. Expected Git tree:', tree)
