"""Generate only the locally reviewed outputs on this exact feature branch."""
import importlib.util, json, os, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CFG={"branch":"fix/eau-male-citrate-threshold-20261017","base":"a853851ef6afdc34861dde63daf422eb2e1a86f8","tree":"b15779a63da7f19b116d0054a60000a2c50277e5","workflow":".github/workflows/check.yml","repository":"Residency-Game-DE"}
def git(*args):
    return subprocess.run(['git',*args],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()
assert os.environ.get('GITHUB_REF')=='refs/heads/'+CFG['branch']
assert git('branch','--show-current')==CFG['branch']
start=git('rev-parse','HEAD')
git('merge-base','--is-ancestor',CFG['base'],'HEAD')
original=subprocess.run(['git','show',CFG['base']+':'+CFG['workflow']],cwd=ROOT,capture_output=True,check=True).stdout
(ROOT/CFG['workflow']).write_bytes(original)
Path(__file__).unlink()
sys.path.insert(0,str(ROOT))
import hashlib
spec=importlib.util.spec_from_file_location('reviewed_manage',ROOT/'scripts/manage.py')
manage=importlib.util.module_from_spec(spec);spec.loader.exec_module(manage)
manage.build(ROOT)
manifest=manage.package(ROOT,ROOT/'dist/night-shift-academy.zip')
(ROOT/'SHA256.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
git('add','--all')
actual=git('write-tree')
assert actual==CFG['tree'],f"Generated tree {actual} differs from reviewed tree {CFG['tree']}"
remote=git('ls-remote','origin','refs/heads/'+CFG['branch']).split()[0]
assert remote==start,'Feature branch moved concurrently; refusing to overwrite it'
git('-c','user.name=github-actions[bot]','-c','user.email=41898282+github-actions[bot]@users.noreply.github.com','commit','-m','Generate outputs identical to the reviewed local tree')
git('push','origin','HEAD:refs/heads/'+CFG['branch'])
print('Verified and published tree '+actual)
