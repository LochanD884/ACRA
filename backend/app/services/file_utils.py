from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pathspec

BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg", ".pdf",
    ".zip", ".tar", ".gz", ".7z", ".rar", ".exe", ".dll", ".so",
    ".dylib", ".bin", ".class", ".jar", ".wasm",
}

LOCK_FILES = {
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "poetry.lock",
    "Pipfile.lock",
    "uv.lock",
    "Cargo.lock",
    "composer.lock",
    "go.sum",
    "Gemfile.lock",
}

TEXT_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs", ".cpp", ".c", ".h",
    ".cs", ".rb", ".php", ".swift", ".kt", ".scala", ".sql", ".html", ".css",
    ".md", ".yaml", ".yml", ".toml", ".json", ".sh", ".ps1",
}


@dataclass
class FileItem:
    path: str
    content: str


def load_gitignore_patterns(lines: Iterable[str]) -> pathspec.PathSpec:
    return pathspec.PathSpec.from_lines("gitwildmatch", lines)


def is_relevant_file(path: str) -> bool:
    p = Path(path)
    if p.name in LOCK_FILES:
        return False
    if p.suffix.lower() in BINARY_EXTENSIONS:
        return False
    if p.suffix.lower() in TEXT_EXTENSIONS:
        return True
    return False


def chunk_text(text: str, limit: int) -> list[str]:
    if len(text) <= limit:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + limit, len(text))
        chunks.append(text[start:end])
        start = end
    return chunks
