#!/usr/bin/env python3
"""Build a small unsigned APT repository for jailbreak package managers."""

from __future__ import annotations

import bz2
import email.utils
import gzip
import hashlib
import json
import lzma
import sys
import tarfile
from collections import OrderedDict
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEBS = ROOT / "debs"
PACKAGES = ROOT / "Packages"
PACKAGES_GZ = ROOT / "Packages.gz"
RELEASE = ROOT / "Release"


def fail(message: str) -> None:
    print(f"错误：{message}", file=sys.stderr)
    raise SystemExit(1)


def read_ar_members(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    if not data.startswith(b"!<arch>\n"):
        fail(f"{path.name} 不是有效的 .deb/ar 文件")

    members: dict[str, bytes] = {}
    offset = 8
    while offset + 60 <= len(data):
        header = data[offset : offset + 60]
        if header[58:60] != b"`\n":
            fail(f"{path.name} 的 ar 头格式无效")
        raw_name = header[0:16].decode("utf-8", "replace").strip()
        try:
            size = int(header[48:58].decode("ascii").strip())
        except ValueError:
            fail(f"{path.name} 的 ar 成员大小无效")
        start = offset + 60
        end = start + size
        if end > len(data):
            fail(f"{path.name} 的 ar 成员超出文件范围")
        name = raw_name.rstrip("/")
        members[name] = data[start:end]
        offset = end + (size % 2)
    return members


def unpack_control(deb_path: Path) -> bytes:
    members = read_ar_members(deb_path)
    control_name = next((name for name in members if name.startswith("control.tar")), None)
    if control_name is None:
        fail(f"{deb_path.name} 内没有 control.tar.*")
    control_data = members[control_name]
    if control_name.endswith(".zst"):
        fail(f"{deb_path.name} 使用 zstd 压缩；请先用 dpkg-deb 解包，或提供 gzip/xz/bz2 版本")

    try:
        with tarfile.open(fileobj=BytesIO(control_data), mode="r:*") as archive:
            member = next((item for item in archive.getmembers() if item.name.lstrip("./") == "control"), None)
            if member is None:
                fail(f"{deb_path.name} 的 control.tar.* 内没有 control 文件")
            extracted = archive.extractfile(member)
            if extracted is None:
                fail(f"无法读取 {deb_path.name} 的 control 文件")
            return extracted.read()
    except tarfile.TarError as exc:
        fail(f"无法解压 {deb_path.name} 的 control.tar.*：{exc}")
    return b""  # unreachable


def parse_control(raw: bytes) -> OrderedDict[str, str]:
    text = raw.decode("utf-8", "replace").replace("\r\n", "\n")
    fields: OrderedDict[str, str] = OrderedDict()
    current: str | None = None
    for line in text.splitlines():
        if not line:
            continue
        if line[0] in " \t" and current is not None:
            fields[current] += "\n" + line
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        current = key.strip()
        fields[current] = value.lstrip()
    return fields


def format_field(key: str, value: str) -> str:
    lines = value.split("\n")
    result = [f"{key}: {lines[0]}"]
    result.extend(line if line.startswith((" ", "\t")) else f" {line}" for line in lines[1:])
    return "\n".join(result)


def digest(path: Path, algorithm: str) -> str:
    hasher = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def write_release(config: dict[str, str]) -> None:
    lines = [
        f"Origin: {config['name']}",
        f"Label: {config['label']}",
        "Suite: stable",
        "Codename: stable",
        f"Date: {email.utils.format_datetime(datetime.now(timezone.utc), usegmt=True)}",
        "Architectures: iphoneos-arm64 iphoneos-arm64e all",
        "Components: main",
        f"Description: {config['description']}",
        "MD5Sum:",
    ]
    for path in (PACKAGES, PACKAGES_GZ):
        lines.append(f" {digest(path, 'md5')} {path.stat().st_size:16d} {path.name}")
    lines.append("SHA256:")
    for path in (PACKAGES, PACKAGES_GZ):
        lines.append(f" {digest(path, 'sha256')} {path.stat().st_size:16d} {path.name}")
    RELEASE.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    config_path = ROOT / "repo.json"
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
        for key in ("name", "label", "description"):
            if not config.get(key):
                fail(f"repo.json 缺少 {key}")
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"读取 repo.json 失败：{exc}")

    DEBS.mkdir(exist_ok=True)
    paragraphs: list[str] = []
    deb_paths = sorted(DEBS.glob("*.deb"), key=lambda item: item.name.lower())
    for deb_path in deb_paths:
        fields = parse_control(unpack_control(deb_path))
        required = ["Package", "Version", "Architecture", "Description"]
        missing = [key for key in required if not fields.get(key)]
        if missing:
            fail(f"{deb_path.name} 缺少字段：{', '.join(missing)}")

        fields["Filename"] = f"debs/{deb_path.name}"
        fields["Size"] = str(deb_path.stat().st_size)
        fields["MD5sum"] = digest(deb_path, "md5")
        fields["SHA256"] = digest(deb_path, "sha256")
        paragraphs.append("\n".join(format_field(key, value) for key, value in fields.items()))

    package_text = "\n\n".join(paragraphs)
    if package_text:
        package_text += "\n"
    PACKAGES.write_text(package_text, encoding="utf-8", newline="\n")
    with gzip.open(PACKAGES_GZ, "wb", compresslevel=9) as stream:
        stream.write(package_text.encode("utf-8"))
    write_release(config)

    print(f"已生成：{len(deb_paths)} 个软件包")
    print(f"索引：{PACKAGES.name}、{PACKAGES_GZ.name}、{RELEASE.name}")


if __name__ == "__main__":
    main()
