#!/usr/bin/env python3
"""Verify the translated zip against the original mod zip.

usage: verify_zh.py [original-zip] [translated-zip]

Checks: identical file lists, every menu-bearing lua module translated (no
label/description/title/choices string left without CJK, no untranslated
category name), and prints one rebuilt menu row as a sample.
"""
import re
import sys
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from patch_tool import read_archive, LUA_TYPE, lua_source  # noqa: E402

ORIG = Path(r'E:\HD2 MOSD download\HD2\Armored-Overhaul-3.3.0.zip')
NEW = Path(r'E:\HD2 MOSD download\ArmoredOverhaul-3.3.0-zh-Hans.zip')

CJK = re.compile(r'[\u4e00-\u9fff]')
TEXTS = [(re.compile(r"(label|description|title) = '((?:[^'\\]|\\.)*)'"), 2)]
CHOICES = re.compile(r"choices = \{([^}]*)\}")
QSTR = re.compile(r"'((?:[^'\\]|\\.)*)'")
CATEGORY = "ARMORED OVERHAUL"


def lua_texts(zf, names):
    """Yield (zip name, lua source text) for every lua resource."""
    for name in sorted(names):
        if not name.endswith('.patch_0'):
            continue
        try:
            arch = read_archive(zf.read(name))
        except SystemExit:
            continue
        for entry in arch['entries']:
            if entry['type'] == LUA_TYPE:
                src, _ = lua_source(entry['payload'])
                yield name, src.decode('utf-8')


def main():
    orig = zipfile.ZipFile(Path(sys.argv[1]) if len(sys.argv) > 1 else ORIG)
    new = zipfile.ZipFile(Path(sys.argv[2]) if len(sys.argv) > 2 else NEW)
    onames, nnames = set(orig.namelist()), set(new.namelist())
    print('entries: original %d, new %d, only-orig %s, only-new %s' % (
        len(onames), len(nnames), sorted(onames - nnames)[:5], sorted(nnames - onames)[:5]))

    # expected = menu-bearing modules in the original (they carry spec.mod)
    expected = sum(1 for _, text in lua_texts(orig, onames) if 'spec.mod = ' in text)

    zh, leftover, sample = 0, [], None
    for name, text in lua_texts(new, nnames):
        if 'spec.mod = ' in text and CJK.search(text):
            zh += 1
        for pattern, group in TEXTS:
            for m in pattern.finditer(text):
                s = m.group(group).replace("\\'", "'")
                if not CJK.search(s):
                    leftover.append('%s :: text %r' % (name, s))
        for m in CHOICES.finditer(text):
            for s in QSTR.findall(m.group(1)):
                if not CJK.search(s.replace("\\'", "'")):
                    leftover.append('%s :: choice %r' % (name, s))
        if "'%s'" % CATEGORY in text:            # quoted: comments may mention it
            leftover.append('%s :: category still %s' % (name, CATEGORY))
        if sample is None:
            m = re.search(r"menu_rows(?:\.\w+|\[P\.menu\]) = \{?\n?.*?(?:title|label) = '[^']*'", text, re.S)
            if m:
                sample = m.group(0)[:300]
    print('menu-bearing lua modules: expected %d translated, found %d translated' % (expected, zh))
    print('leftover English menu strings:', len(leftover))
    for line in leftover[:10]:
        print('  ', line)
    print('--- sample rebuilt menu row ---')
    print(sample)
    return 0 if not leftover and zh == expected else 1


if __name__ == '__main__':
    sys.exit(main())
