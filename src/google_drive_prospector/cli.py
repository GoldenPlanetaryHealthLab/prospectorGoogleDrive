#' ---
#' title: Defining the Google Drive Rclone Prospector
#' ---
#' 

from pathlib import Path
from omegaconf import DictConfig, OmegaConf

import hydra
import time
import logging
import argparse
import re
import shutil
import subprocess
import sys


log = logging.getLogger(__name__)


def ensure_rclone() -> None:
    if shutil.which("rclone") is None:
        log.error("Error: rclone not found in PATH.")
        raise SystemExit(2)
    else:
        log.info("rclone is available.")


def list_dataset_dirs(remote: str, dataset_pattern: re.Pattern) -> list[str]:
    result = subprocess.run(
        ["rclone", "lsf", "-R", remote, "--dirs-only"],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        raise SystemExit(result.returncode)

    return [
        line.rstrip("/")
        for line in result.stdout.splitlines()
        if dataset_pattern.search(line)
    ]


def sync(
    remote: str,
    destination: str,
    dataset_pattern: re.Pattern[str],
    dry_run: bool = False,
    ) -> int:
    """
    Sync dataset directories from a remote location to a local destination.

    Parameters
    ----------
    remote : str
        The remote location to sync from (e.g., "csph-googledrive:2. Projects").
    destination : str
        The local destination to sync to (e.g., "/n/holylabs/LABS/cgolden_lab/Lab/data_freeze/golden_googledrive_rclone").
    dataset_pattern : re.Pattern
        A regular expression pattern to match dataset directories (e.g., r"/[0-9]+\\. Datasets/$").
    dry_run : bool, optional
        If True, perform a dry run without making any changes (default is False).
    Returns
    -------
    int
        Returns 0 if the sync was successful, or 1 if there were any failures.
    """
    log.info("Starting sync: %s -> %s", remote, destination)
    start_time = time.time()

    ensure_rclone()
    dataset_dirs = list_dataset_dirs(remote, dataset_pattern)
    
    if not dataset_dirs:
        log.warning("No dataset directories found.")
        return 0

    failures = 0

    for dataset_path in dataset_dirs:
        dest_path = Path(destination) / dataset_path
        cmd = [
            "rclone",
            "copy",
            f"{remote}/{dataset_path}",
            str(dest_path),
            "--create-empty-src-dirs",
            "--progress",
        ]

        if dry_run:
            cmd.append("--dry-run")

        log.info("Copying: %s/%s -> %s", remote, dataset_path, dest_path)

        result = subprocess.run(cmd, check=False)

        if result.returncode != 0:
            failures += 1
            log.error("Failed: %s", dataset_path)

    elapsed = time.time() - start_time

    log.info("Sync complete in %.2f seconds", elapsed)

    return 1 if failures else 0


@hydra.main(version_base=None, config_path="conf", config_name="config")
def main(cfg: DictConfig) -> int:
    
    dataset_pattern = re.compile(cfg.dataset_pattern)
    if cfg.run == "sync":
        return sync(
            remote=cfg.remote,
            destination=cfg.destination,
            dataset_pattern=dataset_pattern,
            dry_run=cfg.dry_run,
        )
    raise ValueError(f"Unknown action: {cfg.run}")

if __name__ == "__main__":
    sys.exit(main())
