import base64,hashlib,io,json,shutil,tarfile
from pathlib import Path
root=Path.cwd().resolve();transport=root/'.codex-transfer';m=json.loads((transport/'checkpoint.json').read_text());assert m['version']==1
raw=base64.b64decode((transport/'source.b64').read_bytes(),validate=True);assert hashlib.sha256(raw).hexdigest()==m['bundleSha256'];expected={f['path']:f for f in m['files']}
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:xz') as tar:
 members=tar.getmembers();assert len(members)==len(expected) and {f.name for f in members}==set(expected)
 for member in members:
  p=Path(member.name);assert member.isfile() and not p.is_absolute() and '..' not in p.parts and '.git' not in p.parts
  target=(root/p).resolve();assert target.is_relative_to(root);x=tar.extractfile(member).read();f=expected[member.name];assert len(x)==f['size'] and hashlib.sha256(x).hexdigest()==f['sha256'];target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(x)
shutil.rmtree(transport);(root/'.github/workflows/restore-tested-files.yml').unlink();print('Restored verified source; target tree',m['tree'])
