"""Transactional artifact delivery with deterministic SHA-256 receipts."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple


DELIVERY_RECEIPT_VERSION = "0.1"


class DeliveryError(RuntimeError):
    """A delivery failure that is safe to expose as a structured CLI result."""

    def __init__(
        self,
        stage: str,
        message: str,
        *,
        validation: Optional[Dict[str, Any]] = None,
        diagnostics: Optional[Dict[str, Any]] = None,
        recovery_path: Optional[Path] = None,
    ) -> None:
        super().__init__(message)
        self.stage = stage
        self.message = message
        self.validation = validation
        self.diagnostics = diagnostics
        self.recovery_path = recovery_path

    def to_result(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "ok": False,
            "error": {
                "code": "delivery_failed",
                "stage": self.stage,
                "message": self.message,
            },
            "delivery": {"status": "failed", "stage": self.stage},
        }
        if self.validation is not None:
            result["validation"] = self.validation
        if self.diagnostics is not None:
            result["diagnostics"] = self.diagnostics
        if self.recovery_path is not None:
            result["delivery"]["recovery_path"] = str(self.recovery_path)
        return result


def canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    """Serialize resolved input deterministically for receipt identity."""

    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def digest_bytes(data: bytes) -> Dict[str, Any]:
    return {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def source_record(kind: str, data: bytes, path: Optional[Path] = None) -> Dict[str, Any]:
    record = {"kind": kind, **digest_bytes(data)}
    if path is not None:
        record["path"] = str(path.resolve())
    return record


def deliver_artifacts(
    *,
    outdir: Path,
    basename: str,
    formats: Sequence[str],
    extensions: Mapping[str, str],
    source: Dict[str, Any],
    specification: Mapping[str, Any],
    style: Mapping[str, Any],
    render_options: Mapping[str, Any],
    quality: Mapping[str, Any],
    render: Callable[[Path], Dict[str, Dict[str, Any]]],
    receipt_path: Optional[Path] = None,
    additional_artifacts: Optional[Mapping[str, Tuple[Path, bytes]]] = None,
    evidence: Optional[Mapping[str, Any]] = None,
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any]]:
    """Render and commit all requested artifacts as one best-effort transaction.

    Every target is left untouched until quality and staged-artifact validation
    pass. Existing targets are backed up in the same directory and restored if
    any replacement fails.
    """

    validation = _validation_record(quality)
    if int(quality.get("summary", {}).get("errors", 0)) > 0:
        raise DeliveryError(
            "quality",
            "quality validation reported blocking errors; last-good artifacts were preserved",
            validation=validation,
            diagnostics=dict(quality),
        )
    if not basename or Path(basename).name != basename or basename in {".", ".."}:
        raise DeliveryError("input", "--basename must be a filename without directory components")

    outdir = outdir.resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    receipt_path = (receipt_path or (outdir / f"{basename}.delivery.json")).resolve()
    if receipt_path.parent != outdir:
        raise DeliveryError("input", "delivery receipt must be in the same directory as delivered artifacts")

    target_paths = {format_name: outdir / f"{basename}{extensions[format_name]}" for format_name in formats}
    if receipt_path in target_paths.values():
        raise DeliveryError("input", "delivery receipt path collides with a requested artifact")

    supplemental = _resolve_additional_artifacts(
        outdir,
        additional_artifacts or {},
        reserved_paths=[*target_paths.values(), receipt_path],
    )

    stage_dir = Path(tempfile.mkdtemp(prefix=f".{basename}.deliver-", dir=outdir))
    cleanup_stage = True
    try:
        try:
            staged_outputs = render(stage_dir)
        except DeliveryError:
            raise
        except Exception as exc:
            raise DeliveryError(
                "render",
                f"artifact rendering failed: {exc}",
                validation=validation,
            ) from exc

        outputs, artifact_receipt = _validate_staged_outputs(
            formats=formats,
            stage_dir=stage_dir,
            target_paths=target_paths,
            extensions=extensions,
            basename=basename,
            outputs=staged_outputs,
            validation=validation,
        )
        supplemental_receipt: Dict[str, Dict[str, Any]] = {}
        for artifact_name, (target_path, data) in supplemental.items():
            staged_path = stage_dir / target_path.name
            staged_path.write_bytes(data)
            digest = _digest_path(staged_path)
            supplemental_receipt[artifact_name] = {
                "format": "json",
                "path": str(target_path),
                **digest,
            }
        artifact_receipt.update(supplemental_receipt)
        receipt = {
            "schema": {"name": "AniDiagramDeliveryReceipt", "version": DELIVERY_RECEIPT_VERSION},
            "status": "committed",
            "input": {
                "source": dict(source),
                "specification": {
                    "schema": "DiagramScript",
                    "version": specification.get("version"),
                    **digest_bytes(canonical_json_bytes(specification)),
                },
                "style": {
                    "name": style.get("name"),
                    **digest_bytes(canonical_json_bytes(style)),
                },
            },
            "request": {
                "basename": basename,
                "formats": list(formats),
                "render_options": dict(render_options),
            },
            "validation": validation,
            "artifacts": artifact_receipt,
        }
        staged_receipt = stage_dir / receipt_path.name
        if evidence:
            receipt["evidence"] = dict(evidence)
        staged_receipt.write_bytes(
            (json.dumps(receipt, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        )
        replacements = [
            (stage_dir / f"{basename}{extensions[format_name]}", target_paths[format_name])
            for format_name in formats
        ]
        replacements.extend(
            (stage_dir / target_path.name, target_path)
            for target_path, _data in supplemental.values()
        )
        replacements.append((staged_receipt, receipt_path))
        _commit_replacements(replacements, stage_dir / ".backup", validation)

        receipt_digest = _digest_path(receipt_path)
        delivery = {
            "status": "committed",
            "transaction": "same-directory-replace-with-rollback",
            "receipt": {
                "path": str(receipt_path),
                **receipt_digest,
            },
        }
        if supplemental_receipt:
            delivery["supplemental_artifacts"] = supplemental_receipt
        return outputs, delivery
    except DeliveryError as exc:
        if exc.recovery_path is not None:
            cleanup_stage = False
        raise
    finally:
        if cleanup_stage:
            shutil.rmtree(stage_dir, ignore_errors=True)


def _validation_record(quality: Mapping[str, Any]) -> Dict[str, Any]:
    summary = quality.get("summary", {})
    return {
        "quality": {
            "ok": bool(quality.get("ok", False)),
            "score": int(quality.get("score", 0)),
            "errors": int(summary.get("errors", 0)),
            "warnings": int(summary.get("warnings", 0)),
            "issues": int(summary.get("issues", 0)),
            "advisories": len(quality.get("advisories", [])),
        }
    }


def _resolve_additional_artifacts(
    outdir: Path,
    artifacts: Mapping[str, Tuple[Path, bytes]],
    *,
    reserved_paths: Sequence[Path],
) -> Dict[str, Tuple[Path, bytes]]:
    resolved: Dict[str, Tuple[Path, bytes]] = {}
    occupied = {path.resolve() for path in reserved_paths}
    for artifact_name, (target, data) in artifacts.items():
        target = target.resolve()
        if target.parent != outdir:
            raise DeliveryError(
                "input",
                f"additional artifact '{artifact_name}' must be in the delivery output directory",
            )
        if target in occupied:
            raise DeliveryError(
                "input",
                f"additional artifact '{artifact_name}' collides with another delivery target",
            )
        occupied.add(target)
        resolved[artifact_name] = (target, data)
    return resolved


def _validate_staged_outputs(
    *,
    formats: Sequence[str],
    stage_dir: Path,
    target_paths: Mapping[str, Path],
    extensions: Mapping[str, str],
    basename: str,
    outputs: Mapping[str, Dict[str, Any]],
    validation: Dict[str, Any],
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    final_outputs: Dict[str, Dict[str, Any]] = {}
    artifact_receipt: Dict[str, Dict[str, Any]] = {}
    for format_name in formats:
        result = outputs.get(format_name)
        if result is None:
            raise DeliveryError(
                "render",
                f"exporter returned no result for requested format '{format_name}'",
                validation=validation,
            )
        if result.get("status") != "written":
            reason = result.get("reason", f"status was {result.get('status', 'missing')}")
            raise DeliveryError(
                "render",
                f"exporter did not write requested format '{format_name}': {reason}",
                validation=validation,
            )
        staged_path = stage_dir / f"{basename}{extensions[format_name]}"
        if not staged_path.is_file():
            raise DeliveryError(
                "render",
                f"exporter reported success but staged artifact is missing for '{format_name}'",
                validation=validation,
            )
        digest = _digest_path(staged_path)
        if digest["bytes"] == 0:
            raise DeliveryError(
                "render",
                f"exporter produced an empty staged artifact for '{format_name}'",
                validation=validation,
            )
        target_path = target_paths[format_name]
        final_result = dict(result)
        final_result.update({"path": str(target_path), **digest})
        final_outputs[format_name] = final_result
        artifact_receipt[format_name] = {
            "format": format_name,
            "path": str(target_path),
            **digest,
        }
    return final_outputs, artifact_receipt


def _digest_path(path: Path) -> Dict[str, Any]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
    return {"sha256": digest.hexdigest(), "bytes": size}


def _commit_replacements(
    replacements: Sequence[Tuple[Path, Path]],
    backup_dir: Path,
    validation: Dict[str, Any],
) -> None:
    backup_dir.mkdir()
    backups: List[Tuple[Path, Path]] = []
    committed: List[Path] = []
    try:
        for index, (_staged, target) in enumerate(replacements):
            if target.exists():
                backup = backup_dir / f"{index:03d}-{target.name}"
                os.replace(target, backup)
                backups.append((target, backup))
        for staged, target in replacements:
            os.replace(staged, target)
            committed.append(target)
    except Exception as exc:
        rollback_errors: List[str] = []
        for target in reversed(committed):
            try:
                if target.exists():
                    target.unlink()
            except Exception as rollback_exc:
                rollback_errors.append(f"remove {target.name}: {rollback_exc}")
        for target, backup in backups:
            try:
                if target.exists():
                    target.unlink()
                if backup.exists():
                    os.replace(backup, target)
            except Exception as rollback_exc:
                rollback_errors.append(f"restore {target.name}: {rollback_exc}")
        message = f"atomic replacement failed and transaction was rolled back: {exc}"
        if rollback_errors:
            message += "; rollback errors: " + "; ".join(rollback_errors)
        raise DeliveryError(
            "commit",
            message,
            validation=validation,
            recovery_path=backup_dir.parent if rollback_errors else None,
        ) from exc
