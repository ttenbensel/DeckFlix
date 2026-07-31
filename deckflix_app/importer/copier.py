import shutil
from pathlib import Path

from .models import ImportJob


def copy_job(job: ImportJob, temp_dir: Path) -> Path:
    temp_dir.mkdir(parents=True, exist_ok=True)

    temp_file = temp_dir / job.destination.name

    shutil.copy2(job.source, temp_file)

    job.copied = True

    return temp_file
