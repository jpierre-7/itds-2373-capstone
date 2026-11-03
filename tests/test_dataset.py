import os

from capstone.dataset import needs_rebuild


def write(path, mtime):
    path.write_text("x")
    os.utime(path, (mtime, mtime))
    return path


def test_needs_rebuild_when_missing_or_older_than_the_code(tmp_path):
    clean = write(tmp_path / "clean.py", mtime=100)
    features = write(tmp_path / "features.py", mtime=200)
    output = tmp_path / "anime.parquet"

    assert needs_rebuild(output, [clean, features])  # never built

    write(output, mtime=150)
    assert needs_rebuild(output, [clean, features])  # features.py changed after the build

    write(output, mtime=300)
    assert not needs_rebuild(output, [clean, features])  # built from the current code
