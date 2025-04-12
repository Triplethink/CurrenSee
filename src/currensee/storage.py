"""Storage module for the CurrenSee application."""
import json
from pathlib import Path
from typing import Any, Protocol

from currensee.config import get_settings


class StorageWriter(Protocol):
    def write(
        self,
        data: dict[str, Any],
        date_str: str,
        force_overwrite: bool = False,
        dry_run: bool = False,
    ) -> str:
        ...

    def exists(self, date_str: str) -> bool:
        ...

    def get_path(self, date_str: str) -> str:
        ...


class LocalStorageWriter:
    def __init__(self, base_path: str | None = None, stage_dir: str | None = None) -> None:
        settings = get_settings()
        self.base_path = base_path or settings.storage_base_path
        self.stage_dir = stage_dir or settings.stage_dir

    def get_path(self, date_str: str) -> str:
        stage_path = Path(self.stage_dir.lstrip('/'))
        full_path = Path(self.base_path) / stage_path / f'{date_str}.json'
        return str(full_path)

    def exists(self, date_str: str) -> bool:
        path = Path(self.get_path(date_str))
        return path.exists()

    def write(
        self,
        data: dict[str, Any],
        date_str: str,
        force_overwrite: bool = False,
        dry_run: bool = False,
    ) -> str:
        path = self.get_path(date_str)

        if self.exists(date_str) and not force_overwrite:
            raise FileExistsError(f'Data already exists for {date_str} at {path}')

        if not dry_run:
            file_path = Path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)

        return path
