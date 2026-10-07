#!/usr/bin/env python3
"""Inventory generated outputs; move an exact reviewed manifest to Trash reversibly."""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTECTED = {'release-evidence', 'accuracy-study'}

def candidates(root: Path, older_than_days: int) -> list[Path]:
    cutoff = time.time() - max(0, older_than_days) * 86400
    return sorted(p for p in root.iterdir() if p.name not in PROTECTED and not p.is_symlink() and p.stat().st_mtime < cutoff)

def fingerprint(path: Path) -> dict:
    """Hash relative names and bytes; never traverse symlinks."""
    digest = hashlib.sha256(); size = 0; count = 0
    for item in [path] + (sorted(path.rglob('*')) if path.is_dir() else []):
        if item.is_symlink():
            raise ValueError(f'symlink is not a cleanup candidate: {item}')
        name = '.' if item == path else str(item.relative_to(path))
        digest.update(('D:' if item.is_dir() else 'F:').encode() + name.encode() + b'\0')
        if item.is_file():
            data = item.read_bytes(); size += len(data); count += 1; digest.update(hashlib.sha256(data).digest())
    return {'sha256': digest.hexdigest(), 'bytes': size, 'files': count}

def exact_path(root: Path, name: str) -> Path:
    rel = Path(name)
    if rel.is_absolute() or len(rel.parts) != 1 or rel.name in PROTECTED or rel.name in {'.','..'}:
        raise ValueError(f'only unprotected top-level output names are allowed: {name}')
    path = root / rel
    if path.is_symlink() or not path.exists(): raise ValueError(f'missing or symlink path: {path}')
    return path

def manifest(root: Path, names: list[str]) -> dict:
    if len(names) != len(set(names)): raise ValueError('duplicate cleanup candidates')
    entries = [{'name': name, **fingerprint(exact_path(root, name))} for name in names]
    return {'version': 'output-cleanup-v1', 'root': str(root), 'entries': entries, 'bytes': sum(e['bytes'] for e in entries)}

def apply_manifest(root: Path, data: dict, trash: Path) -> dict:
    if data.get('version') != 'output-cleanup-v1' or data.get('root') != str(root): raise ValueError('manifest root/version mismatch')
    names = [entry['name'] for entry in data['entries']]
    # Validate the entire selection before moving the first file.
    current = manifest(root, names)
    if current != data: raise ValueError('cleanup candidates changed; generate and review a fresh manifest')
    if trash.exists(): raise ValueError('refusing to overwrite an existing Trash destination')
    trash.mkdir(parents=True)
    receipt = {'version': 'output-cleanup-receipt-v1', 'manifest': data, 'moves': []}
    try:
        for name in names:
            original = root / name; target = trash / name
            shutil.move(str(original), str(target)); receipt['moves'].append({'from': str(original), 'to': str(target)})
    except Exception:
        for move in reversed(receipt['moves']): shutil.move(move['to'], move['from'])
        raise
    (trash/'restore-manifest.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n')
    return receipt

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT/'outputs')
    parser.add_argument('--older-than-days', type=int, default=14)
    parser.add_argument('--select', nargs='+', help='Exact top-level names for a reviewable manifest.')
    parser.add_argument('--manifest', type=Path, help='Previously reviewed manifest; required with --apply.')
    parser.add_argument('--write-manifest', type=Path)
    parser.add_argument('--apply', action='store_true', help='Move reviewed unchanged paths to system Trash; never permanently delete.')
    args = parser.parse_args(); root = args.root.resolve()
    if root != (ROOT/'outputs').resolve(): parser.error('refusing non-canonical output root')
    try:
        if args.apply:
            if not args.manifest or args.select: parser.error('--apply requires --manifest and forbids --select')
            data = json.loads(args.manifest.read_text())
            result = apply_manifest(root, data, Path.home()/'.Trash'/f'anidiagram-{time.time_ns()}')
        elif args.select:
            result = manifest(root, args.select)
        else:
            result = {'mode': 'inventory-only', 'root': str(root), 'protected': sorted(PROTECTED), 'paths': [str(p) for p in candidates(root,args.older_than_days)], 'note': 'Age alone is not authorization. Select exact paths and review the resulting manifest.'}
        if args.write_manifest: args.write_manifest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except (ValueError, KeyError, OSError) as exc: parser.error(str(exc))

if __name__ == '__main__': main()
