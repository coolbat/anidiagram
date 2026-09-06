"""Commit a small set of sidecars using the delivery module's rollback machinery."""

from pathlib import Path
import shutil
import tempfile

from .delivery import DeliveryError, _commit_replacements


def commit_bundle(files, *, inputs=()):
    targets = [Path(path).absolute() for path in files]
    if not targets or len(set(targets)) != len(targets):
        raise ValueError("artifact bundle requires distinct output files")
    directory = targets[0].parent
    if any(target.parent != directory for target in targets):
        raise ValueError("artifact sidecars must share the output directory")

    def check_targets():
        for target in targets:
            if target.is_symlink() or (target.exists() and not target.is_file()):
                raise ValueError("artifact targets must be regular files, not symlinks or directories")
            for source in inputs:
                source = Path(source)
                if target.resolve() == source.resolve() or (target.exists() and source.exists() and target.samefile(source)):
                    raise ValueError("artifact output cannot replace an input file")

    check_targets()
    directory.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".anidiagram-bundle-", dir=directory))
    preserve = False
    try:
        replacements = []
        for target, data in zip(targets, files.values()):
            if not isinstance(data, bytes) or not data:
                raise ValueError("artifact bundle requires non-empty bytes")
            candidate = stage / target.name
            candidate.write_bytes(data)
            replacements.append((candidate, target))
        check_targets()
        _commit_replacements(replacements, stage / ".backup", {})
    except DeliveryError as error:
        preserve = error.recovery_path is not None
        raise
    finally:
        if not preserve:
            shutil.rmtree(stage)
