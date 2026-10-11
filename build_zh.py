#!/usr/bin/env python3
"""Rebuild Armored Overhaul patches with translated lua and pack the zip.

usage: build_zh.py [extract-dir] [output-zip]
Defaults: the 3.3.0 extract dir and the deliverable zip name in the workspace.

Steps:
  1. round-trip: rebuild every original patch from pristine extracted/ sources
     and compare byte-for-byte (proves the layout writer is lossless);
  2. rebuild with translated lua (extracted_zh/); folders without lua are
     copied verbatim; in rebuilt patches every non-lua payload must equal the
     original's;
  3. copy manifest/thumbnail/options previews verbatim and write the zip.
"""
import shutil
import sys
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from patch_tool import LUA_TYPE, read_archive, load_dir, make_archive  # noqa: E402

ROOT = Path(__file__).resolve().parent
SRC = ROOT / 'extracted'
ZH = ROOT / 'extracted_zh'
REBUILT = ROOT / 'rebuilt'
PATCH = '9ba626afa44a3aa3.patch_0'


def rebuild_from(src_dir, original):
    archive = read_archive(original.read_bytes())
    return make_archive(load_dir(src_dir, archive['entries']))


def main(argv):
    mod = Path(argv[1]) if len(argv) > 1 else ROOT.parent / 'Armored-Overhaul-3.3.0-extract'
    out_zip = Path(argv[2]) if len(argv) > 2 else ROOT.parent / 'ArmoredOverhaul-3.3.0-zh-Hans.zip'
    patches = sorted(p for p in mod.rglob(PATCH))
    if not patches:
        print(f'no {PATCH} under {mod}')
        return 1
    if REBUILT.exists():
        shutil.rmtree(REBUILT)
    print(f'{len(patches)} patches in {len({p.parent for p in patches})} folders')

    # 1) lossless round-trip proof on every patch that will be rebuilt
    #    (patches without lua are game-resource archives — copied verbatim)
    for patch in patches:
        rel = patch.parent.name
        if not any((SRC / rel).glob('*.lua')):
            continue
        if rebuild_from(SRC / rel, patch) != patch.read_bytes():
            print(f'round-trip MISMATCH: {rel}')
            return 1
    print('round-trip: all lua patches byte-identical')

    # 2) rebuild; folders without lua keep the original patch
    rebuilt, verbatim = 0, 0
    for patch in patches:
        rel = patch.parent.name
        outdir = REBUILT / rel
        outdir.mkdir(parents=True)
        if not any((SRC / rel).glob('*.lua')):
            shutil.copy2(patch, outdir / PATCH)
            verbatim += 1
            continue
        data = rebuild_from(ZH / rel, patch)
        (outdir / PATCH).write_bytes(data)
        rebuilt += 1
        # non-lua payloads must survive the rebuild untouched
        before, after = read_archive(patch.read_bytes()), read_archive(data)
        if len(before['entries']) != len(after['entries']):
            print(f'entry count changed: {rel}')
            return 1
        for b, a in zip(before['entries'], after['entries']):
            if b['name'] != a['name'] or b['type'] != a['type']:
                print(f'entry identity changed: {rel}')
                return 1
            if b['type'] != LUA_TYPE and b['payload'] != a['payload']:
                print(f'non-lua payload changed: {rel}')
                return 1
    print(f'rebuilt {rebuilt} patches with translated lua, copied {verbatim} verbatim')

    # 3) zip: everything from the original extract, patches from REBUILT
    if out_zip.exists():
        out_zip.unlink()
    with zipfile.ZipFile(out_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(mod.rglob('*')):
            if not path.is_file():
                continue
            rel = path.relative_to(mod)
            source = REBUILT / rel if path.name == PATCH else path
            zf.write(source, str(rel))
    print(f'wrote {out_zip} ({out_zip.stat().st_size:,} bytes)')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
