"""Fetch a pinned release archive and validate its allowlisted files before extraction."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import tarfile
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''): h.update(block)
    return h.hexdigest()

def install(archive, manifest):
    if archive.stat().st_size != manifest['archive_bytes'] or digest(archive) != manifest['archive_sha256']:
        raise ValueError('Archive length or SHA-256 mismatch')
    expected = {x['path']:x for x in manifest['files']}
    if len(expected) != len(manifest['files']): raise ValueError('Duplicate manifest paths')
    with tarfile.open(archive, 'r:gz') as tar:
        members = tar.getmembers()
        if len(members)!=len(expected) or {x.name for x in members}!=set(expected):
            raise ValueError('Unexpected archive file set')
        for member in members:
            name = PurePosixPath(member.name)
            target = ROOT/member.name
            if not member.isfile() or name.is_absolute() or '..' in name.parts or str(name)!=member.name:
                raise ValueError('Unsafe archive member')
            if ROOT not in target.resolve().parents or target.is_symlink():
                raise ValueError('Unsafe extraction destination')
            item = expected[member.name]
            if member.size!=item['bytes']: raise ValueError('Member length mismatch')
            data = tar.extractfile(member).read()
            if hashlib.sha256(data).hexdigest()!=item['sha256']: raise ValueError('Member SHA-256 mismatch')
            if target.exists() and (not target.is_file() or digest(target)!=item['sha256']):
                raise ValueError('Refuse overwrite of changed local artifact: '+member.name)
        # All checks completed before writing. Do not follow tar links or use extractall.
        for member in members:
            target = ROOT/member.name
            if target.exists(): continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as f: f.write(tar.extractfile(member).read())
    return len(members)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, help='Use an existing local archive; no network')
    args=parser.parse_args(); manifest=json.loads((ROOT/'ARTIFACTS.json').read_text())
    if args.archive:
        count=install(args.archive.resolve(),manifest)
    else:
        if not manifest['url'].startswith('https://github.com/ickma2311/transcript-command-diagnostics/releases/download/'):
            raise ValueError('Unexpected release destination')
        with tempfile.TemporaryDirectory(prefix='transcript-command-download-') as tmp:
            archive=Path(tmp)/manifest['archive_name']
            request=urllib.request.Request(manifest['url'],headers={'User-Agent':'transcript-command-diagnostics/0.1.0'})
            with urllib.request.urlopen(request,timeout=60) as response, archive.open('wb') as out:
                size=0
                while block:=response.read(1024*1024):
                    size+=len(block)
                    if size>manifest['archive_bytes']: raise ValueError('Download exceeds declared length')
                    out.write(block)
            count=install(archive,manifest)
    print(json.dumps({'verified_files':count,'archive_sha256':manifest['archive_sha256'],'model_inference':False}))

if __name__=='__main__': main()
