"""Keep legacy location bindings stable across Btrfs device renumbering.

The auxiliary metadata never rewrites saved consent or historical records. A
first observation retains today's device number; it cannot recover an already
stale legacy hash. Other filesystems keep the existing fail-closed behavior.
"""
import hashlib
import os
import socket
import re
import sys


def stored_device(value):
    if value.isdecimal():
        return int(value)
    if re.fullmatch(r"changed:[0-9a-f]{64}", value):
        return value
    raise ValueError("Saved location identity is invalid; inspect the library before reconnecting.")


def btrfs_id(fd, info):
    if sys.platform != 'linux':
        return None
    device = f'{os.major(info.st_dev)}:{os.minor(info.st_dev)}'
    with open('/proc/self/mountinfo', encoding='utf-8') as stream:
        data = stream.read(2 * 1024 * 1024 + 1)
    if len(data) > 2 * 1024 * 1024:
        raise ValueError('Mount information exceeds the identity inspection limit.')
    if not any(line.split()[2] == device and line.split(' - ', 1)[1].split()[0] == 'btrfs'
               for line in data.splitlines() if ' - ' in line):
        return None
    fsid = os.fstatvfs(fd).f_fsid
    if not fsid:
        raise ValueError('Btrfs filesystem identity is unavailable; retry when the mount is ready.')
    return fsid


def device_identity(store, path, info, fd, *, remember=False):
    fsid = btrfs_id(fd, info)
    if fsid is None:
        return info.st_dev
    # Include host, path, filesystem/subvolume identity and inode. A copied or
    # moved library/source must not inherit consent just because a path matches.
    prefix = 'location_device_v1:' + hashlib.sha256(
        f'{socket.gethostname()}\0{path}'.encode()).hexdigest() + ':'
    key = prefix + hashlib.sha256(f'{fsid}\0{info.st_ino}'.encode()).hexdigest()
    with store.connection() as conn:
        row = conn.execute('SELECT value FROM metadata WHERE key=?', (key,)).fetchone()
        if row is not None:
            return stored_device(row[0])
        if remember:
            conn.execute('BEGIN IMMEDIATE')
        previous = conn.execute('SELECT 1 FROM metadata WHERE key LIKE ? LIMIT 1', (prefix + '%',)).fetchone()
        # A new filesystem at the same path must differ even if the kernel reuses
        # both the old device number and inode. No saved consent is rewritten.
        device = 'changed:' + key.rsplit(':', 1)[1] if previous else info.st_dev
        if not remember:
            return device
        conn.execute('INSERT OR IGNORE INTO metadata VALUES (?,?)', (key, str(device)))
        value = conn.execute('SELECT value FROM metadata WHERE key=?', (key,)).fetchone()[0]
    return stored_device(value)


def remember_location(store, path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        device_identity(store, path, os.fstat(fd), fd, remember=True)
    finally:
        os.close(fd)
