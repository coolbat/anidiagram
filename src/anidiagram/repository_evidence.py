"""Resolve authored source references against immutable Git blobs, without network access."""

from copy import deepcopy
import hashlib
from pathlib import Path
import re
import subprocess
from urllib.parse import quote


class EvidenceError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def _require(condition, code, message):
    if not condition:
        raise EvidenceError(code, message)


def github_repository(value):
    match = re.fullmatch(r"(?:https://github\.com/|git@github\.com:|ssh://git@github\.com/)([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?", str(value))
    _require(match is not None, "repository_url", "repository must identify a GitHub owner/repository without credentials or query parameters")
    return "https://github.com/" + match[1].lower() + "/" + match[2].lower()


def validate_repository(value):
    _require(isinstance(value, dict), "repository_shape", "source.repository must be an object")
    _require(not set(value) - {"url", "revision", "path", "line", "end_line"}, "repository_shape", "unsupported source.repository field")
    github_repository(value.get("url"))
    _require(str(value.get("url", "")).startswith("https://github.com/"), "repository_url", "source.repository.url must use HTTPS")
    _require(isinstance(value.get("revision"), str) and re.fullmatch(r"[a-fA-F0-9]{40}", value["revision"]), "revision", "repository.revision must be a full 40-character commit SHA")
    path = value.get("path")
    _require(isinstance(path, str) and path and "\\" not in path and not any(ord(c) < 32 or ord(c) == 127 for c in path), "source_path", "repository.path must be a relative POSIX path")
    _require(all(part not in {"", ".", ".."} and part.lower() != ".git" for part in path.split("/")), "source_path", "repository.path cannot escape the repository or address .git")
    for field in ("line", "end_line"):
        if field in value:
            _require(type(value[field]) is int and value[field] > 0, "source_lines", f"repository.{field} must be a positive integer")
    _require("end_line" not in value or ("line" in value and value["end_line"] >= value["line"]), "source_lines", "end_line requires line and cannot precede it")


def compile_evidence(semantic):
    sources = [deepcopy(s) for s in semantic.get("sources", []) if "repository" in s]
    if not sources:
        return None
    source_ids = {s["id"] for s in sources}
    subjects = {}
    for collection in ("entities", "relations", "groups"):
        for item in semantic.get(collection, []):
            refs = sorted(source_ids.intersection(item.get("source_refs", [])))
            if refs:
                subjects[item["id"]] = refs
    for flow in semantic.get("flows", []):
        refs = source_ids.intersection(flow.get("source_refs", []))
        for relation_id in flow["relation_ids"]:
            if refs:
                subjects[relation_id] = sorted(set(subjects.get(relation_id, [])) | refs)
    return {"sources": sources, "subjects": subjects}


def _git(root, *args):
    try:
        result = subprocess.run(["git", "-c", "core.fsmonitor=false", "-C", str(root), *args],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise EvidenceError("git_unavailable", "Git could not inspect the evidence repository") from error
    _require(result.returncode == 0, "git_reference", "Git could not resolve the requested repository, revision, or blob")
    return result.stdout


def verify_evidence(value, repo_root, subject_ids):
    _require(isinstance(value, dict) and set(value) == {"sources", "subjects"}, "evidence_shape", "evidence requires only sources and subjects; verified status cannot be supplied by input")
    sources, subjects = value["sources"], value["subjects"]
    _require(isinstance(sources, list) and bool(sources) and isinstance(subjects, dict), "evidence_shape", "evidence sources must be non-empty and subjects must be an object")
    source_ids = set()
    for source in sources:
        _require(isinstance(source, dict) and isinstance(source.get("id"), str), "evidence_shape", "each evidence source requires an id")
        _require(source["id"] not in source_ids and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]*", source["id"]), "evidence_shape", "evidence source ids must be unique semantic ids")
        _require(not set(source) - {"id", "type", "title", "uri", "note", "repository"}, "evidence_shape", "unsupported evidence source field")
        _require(isinstance(source.get("type"), str) and re.fullmatch(r"[a-z][a-z0-9-]*", source["type"]), "evidence_shape", "evidence sources require a semantic type")
        for field in ("title", "uri", "note"):
            _require(field not in source or isinstance(source[field], str), "evidence_shape", "evidence source copy must be text")
        validate_repository(source.get("repository"))
        source_ids.add(source["id"])
    for subject, refs in subjects.items():
        _require(subject in subject_ids, "evidence_subject", "evidence references a missing scene subject")
        _require(isinstance(refs, list) and all(isinstance(ref, str) and ref in source_ids for ref in refs), "evidence_subject", "evidence subject references a missing source")
        _require(len(refs) == len(set(refs)), "evidence_subject", "source references must be unique")
    _require(repo_root is not None, "repository_required", "repository-backed evidence requires --repo-root (or compile_scene(..., repo_root=...))")
    root = Path(repo_root).resolve()
    _require(Path(_git(root, "rev-parse", "--show-toplevel").decode().strip()).resolve() == root, "repository_root", "repo-root must be the Git top-level directory")
    origin = github_repository(_git(root, "remote", "get-url", "origin").decode().strip())
    verified = []
    for source in sources:
        ref = source["repository"]
        url, revision, path = github_repository(ref["url"]), ref["revision"].lower(), ref["path"]
        _require(url == origin, "repository_mismatch", "source repository does not match the local origin")
        _git(root, "cat-file", "-e", revision + "^{commit}")
        tree = _git(root, "ls-tree", "-z", revision, "--", path).split(b"\0")
        entries = [item.split(b"\t", 1) for item in tree if item]
        entry = next((info for info, name in entries if name.decode("utf-8") == path), b"")
        _require(entry.startswith((b"100644 blob ", b"100755 blob ")), "source_file", "source must be a regular file at the pinned commit (not a symlink, directory, or submodule)")
        blob = entry.split()[-1].decode()
        size = int(_git(root, "cat-file", "-s", blob))
        _require(size <= 8 * 1024 * 1024, "source_size", "source blob exceeds the 8 MiB evidence limit")
        content = _git(root, "cat-file", "blob", blob)
        if "line" in ref:
            _require(b"\0" not in content, "source_lines", "line evidence requires a text file")
            _require(ref.get("end_line", ref["line"]) <= len(content.splitlines()), "source_lines", "source line range exceeds the pinned file")
        href = url + "/blob/" + revision + "/" + quote(path, safe="/")
        if "line" in ref:
            href += f"#L{ref['line']}"
            if ref.get("end_line", ref["line"]) != ref["line"]:
                href += f"-L{ref['end_line']}"
        verified.append({"id": source["id"], "title": str(source.get("title") or path),
                         "repository": {**ref, "url": url, "revision": revision}, "href": href,
                         "blob": blob, "sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content)})
    return {"schema": {"name": "AniDiagramEvidence", "version": "0.1"},
            "status": "references-verified", "sources": sorted(verified, key=lambda s: s["id"]),
            "subjects": deepcopy(subjects)}
