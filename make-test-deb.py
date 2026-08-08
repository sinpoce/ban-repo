#!/usr/bin/env python3
"""Create a harmless .deb used only to test this repository."""

from __future__ import annotations

import gzip
import io
import tarfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "debs" / "ban-repo-test_1.0.0_all.deb"


def tar_gz(files: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode="wb", mtime=0) as gz:
        with tarfile.open(fileobj=gz, mode="w") as archive:
            for name, content in files.items():
                info = tarfile.TarInfo(name)
                info.size = len(content)
                info.mode = 0o644
                info.uid = 0
                info.gid = 0
                info.uname = "root"
                info.gname = "root"
                info.mtime = 0
                archive.addfile(info, io.BytesIO(content))
    return buffer.getvalue()


def ar_header(name: str, size: int) -> bytes:
    return (
        name.ljust(16)
        + "0".ljust(12)
        + "0".ljust(6)
        + "0".ljust(6)
        + "100644".rjust(8)
        + str(size).rjust(10)
        + "`\n"
    ).encode("ascii")


def ar_member(name: str, data: bytes) -> bytes:
    padding = b"\n" if len(data) % 2 else b""
    return ar_header(name, len(data)) + data + padding


def main() -> None:
    control = (
        "Package: ban-repo-test\n"
        "Name: Ban Repo Test\n"
        "Version: 1.0.0\n"
        "Architecture: all\n"
        "Section: utils\n"
        "Priority: optional\n"
        "Maintainer: Ban <ban@example.invalid>\n"
        "Description: Harmless test package for Ban Personal Repo\n"
        " This package only installs a text file for testing repository installation.\n"
    ).encode("utf-8")
    marker = (
        "Ban Personal Repo test package\n"
        "安装成功后可以在 /usr/share/ban-repo-test/README.txt 找到此文件。\n"
    ).encode("utf-8")
    control_tar = tar_gz({"./control": control})
    data_tar = tar_gz({"./usr/share/ban-repo-test/README.txt": marker})
    deb = (
        b"!<arch>\n"
        + ar_member("debian-binary", b"2.0\n")
        + ar_member("control.tar.gz", control_tar)
        + ar_member("data.tar.gz", data_tar)
    )
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_bytes(deb)
    print(f"已生成测试包：{OUTPUT}")


if __name__ == "__main__":
    main()
