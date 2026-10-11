#!/usr/bin/env python3
"""Extract / rebuild HD2 lua-resource patch archives (9ba626afa44a3aa3.patch_0).

Layout (mirrors Bingus Shared Loader / translations.py make_archive):
  header  '<III20sQQ24s'  magic 0xF0000011, version, count, ..., total, ...
  types   '<IIQIIII'      (..., type_id, count, ..., 16, 16)
  entries '<7Q6I' x count (name_hash, type, offset, 0,0,0,0, size, 0,0,16,16, index)
  body    resources, 16-byte aligned; each = <II (len(source), 2) + source bytes

Commands:
  info    <patch>                 list entries
  extract <patch> <outdir>        dump entries: <hash>.<type>.bin (lua shown as .lua)
  build   <patch> <outdir> <out>  reassemble from an extract dir, lua entries replaced
                                  by edited <hash>.lua files; verifies round-trip
  verify  <patch> <outdir>        rebuild from untouched extract and compare bytes
"""
import struct
import sys
from pathlib import Path

MAGIC = 0xF0000011
LUA_TYPE = 0xA14E8DFA2CD117E2
HEADER = '<III20sQQ24s'
TYPES = '<IIQIIII'
ENTRY = '<7Q6I'


def read_archive(data):
    magic, version, count = struct.unpack_from(HEADER, data, 0)[:3]
    if magic != MAGIC:
        raise SystemExit(f'not a patch archive: magic {magic:#x}')
    types = struct.unpack_from(TYPES, data, 72)
    type_id = types[2]
    entries = []
    for i in range(count):
        fields = struct.unpack_from(ENTRY, data, 104 + 80 * i)
        name, etype, offset = fields[0], fields[1], fields[2]
        size = fields[7]
        payload = data[offset:offset + size]
        entries.append({'name': name, 'type': etype, 'offset': offset,
                        'size': size, 'fields': fields, 'payload': payload})
    return {'version': version, 'count': count, 'type_id': type_id,
            'types': types, 'total': struct.unpack_from(HEADER, data, 0)[4],
            'entries': entries}


def lua_source(payload):
    if len(payload) < 8:
        raise SystemExit('lua resource too short')
    length, kind = struct.unpack_from('<II', payload, 0)
    return payload[8:8 + length], kind


def wrap_lua(source, kind=2):
    return struct.pack('<II', len(source), kind) + source


def align16(n):
    return (n + 15) & ~15


def make_archive(entries):
    """entries: list of dicts {name, type, fields, payload} in original order."""
    count = len(entries)
    offset = align16(104 + 80 * count)
    entry_bytes = bytearray()
    body = bytearray(offset)
    for index, entry in enumerate(entries):
        payload = entry['payload']
        entry_fields = (entry['name'], entry['type'], offset) + entry['fields'][3:7] \
            + (len(payload),) + entry['fields'][8:]
        entry_bytes += struct.pack(ENTRY, *entry_fields)
        body += payload
        if index != count - 1:                       # pad between, not after the last
            body += b'\0' * (-len(body) % 16)
        offset = len(body)
    first = entries[0]['fields']
    header = struct.pack(HEADER, MAGIC, 1, count, b'', offset, 0, b'')
    types = struct.pack(TYPES, 0, 0, first[1], count, 0, 16, 16)
    body[:104 + len(entry_bytes)] = header + types + bytes(entry_bytes)
    return bytes(body)


def load_dir(extract, entries):
    out = []
    for entry in entries:
        stem = f"{entry['name']:016X}.{entry['type']:016X}"
        lua = Path(extract) / f'{stem}.lua'
        raw = Path(extract) / f'{stem}.bin'
        if lua.exists():
            source = lua.read_bytes()
            _, kind = lua_source(entry['payload'])
            out.append({'name': entry['name'], 'type': entry['type'],
                        'fields': entry['fields'], 'payload': wrap_lua(source, kind)})
        elif raw.exists():
            out.append({'name': entry['name'], 'type': entry['type'],
                        'fields': entry['fields'], 'payload': raw.read_bytes()})
        else:
            out.append({'name': entry['name'], 'type': entry['type'],
                        'fields': entry['fields'], 'payload': entry['payload']})
    return out


def main(argv):
    command = argv[1]
    patch = Path(argv[2])
    data = patch.read_bytes()
    archive = read_archive(data)
    if command == 'info':
        print(f'{patch}: {archive["count"]} entries, type {archive["type_id"]:#x}, '
              f'total {archive["total"]}, file {len(data)}')
        for entry in archive['entries']:
            kind = ''
            if entry['type'] == LUA_TYPE:
                source, lua_kind = lua_source(entry['payload'])
                head = source[:60].decode('utf-8', 'replace').replace('\n', ' | ')
                kind = f'lua{lua_kind} {len(source)}B  {head}'
            print(f"  {entry['name']:016X} type={entry['type']:#018x} size={entry['size']:7d}  {kind}")
        return 0
    extract = Path(argv[3])
    if command == 'extract':
        extract.mkdir(parents=True, exist_ok=True)
        for entry in archive['entries']:
            stem = f"{entry['name']:016X}.{entry['type']:016X}"
            if entry['type'] == LUA_TYPE:
                source, _ = lua_source(entry['payload'])
                (extract / f'{stem}.lua').write_bytes(source)
            else:
                (extract / f'{stem}.bin').write_bytes(entry['payload'])
        print(f'extracted {archive["count"]} entries -> {extract}')
        return 0
    if command in ('build', 'verify'):
        rebuilt = make_archive(load_dir(extract, archive['entries']))
        if command == 'verify':
            if rebuilt == data:
                print(f'round-trip OK: {patch} ({len(data)} bytes)')
                return 0
            differ = next((i for i, (a, b) in enumerate(zip(rebuilt, data)) if a != b), min(len(rebuilt), len(data)))
            print(f'round-trip MISMATCH at byte {differ}: rebuilt {len(rebuilt)} vs {len(data)}')
            return 1
        out = Path(argv[4])
        out.write_bytes(rebuilt)
        print(f'built {out} ({len(rebuilt)} bytes, {archive["count"]} entries)')
        return 0
    raise SystemExit(__doc__)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
