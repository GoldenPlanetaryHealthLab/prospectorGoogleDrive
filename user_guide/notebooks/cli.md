# Defining the Google Drive Rclone Prospector


This package is a simple wrapper around the `rclone` command line tool
to help sync the Golden Lab Google Drive to FASRC. It simply calls
`rclone` under the hood, while managing configuration and logs.

The original script that ran the sync was written in bash, but I thought
it would be wise to create a Python wrapper that may or may not be
extensible in the future.

This is a pretty straightforward function, so the Python wrapper will be
pretty simple as well. The main goal is to run this script periodically
using a `scrontab` job, and keep logs of the sync process.

This package uses notebook-driven-development to create modules from a
notebook (this notebook, to be specific). The code is written in Quarto
notebook cells, and then extracted into a Python module using the Quarto
extensions `sorting-hat` and `ripper`. In this way, we can keep the code
and documentation together in a single notebook, while still producing a
clean Python module for use in our projects. This affords us the
flexibility to easily update the code and documentation in one place,
and then extract it into a module for use in our projects. Documentation
is built with `great-docs`, which allows us to extract documentation
from docstrings in the code.

## Imports and Libraries

The functionality is pretty straightforward, using `argparse` for
command line argument parsing, `subprocess` for running the `rclone`
commands, and `shutil` to check for the presence of `rclone`. We also
use `re` for regular expression matching to find the dataset
directories.

``` python
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
```

## Hydra Config

We do want to ensure that this module is modular, so we have put our
hard coded variables in a `config.yaml` that we read in with Hydra.

To read in the config, we will use Hydra’s `@hydra.main` decorator on
our main function, which will allow us to access the configuration as a
`DictConfig` object. This will make it easy to access our configuration
variables throughout the code.

Looks good to me. We’ll also be using Hydra logging behind the scenes.
Now we can move to the functionality of the module.

``` python
log = logging.getLogger(__name__)
```

## RClone Functionality

We’ll add a quick checker to make sure `rclone` is available:

Awesome!

``` python
def ensure_rclone() -> None:
    if shutil.which("rclone") is None:
        log.error("Error: rclone not found in PATH.")
        raise SystemExit(2)
    else:
        log.info("rclone is available.")
```

Now the basic functionality of `rclone` is implemented as a subcommand.
We can see it in action running the `lsf` command:

``` python
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
```

Lastly, we set up the sync function:

``` python
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
```

That looks great to me. Finally, we’ll put in a main function for the
CLI:

``` python
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
```

After running Quarto render, the module should now be exported to
`src/google_drive_prospector/cli.py` and can be run from the command
line after we install it with `uv`:

# Script file

The code for this document can be found here:

- [../src/google_drive_prospector/cli.py](../src/google_drive_prospector/cli.py)
