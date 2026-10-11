#!/usr/bin/env python3
"""One-command re-localization for a new Armored Overhaul version.

usage: update_zh.py <original-zip> [output-zip]

1. unzip the mod next to the zip (<stem>-extract)
2. pull every lua/bin out of its patches into extracted/ (fresh)
3. diff against baseline/ — the sources the current rules were written against
4. apply the translation rules (translate.py — aborts naming the stale rule)
5. scan translated sources for menu texts still lacking CJK (new options the
   rules do not cover yet)
6. rebuild patches + pack the zip (build_zh.py — round-trip verified)
7. verify the new zip against the original (verify_zh.py)
8. success: snapshot extracted/ into baseline/ for the next update
"""
import json
import difflib
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PATCH = '9ba626afa44a3aa3.patch_0'
KNOWN_GUID = '370555ae-cb28-4b9d-96d0-8381505c3f89'
CJK = re.compile(r'[\u4e00-\u9fff]')
# (regex, group holding the string, kind) for user-facing menu texts
PATTERNS = [
    (re.compile(r"(label|description|title) = '((?:[^'\\]|\\.)*)'"), 2, 'text'),
    (re.compile(r"spec\.mod = '((?:[^'\\]|\\.)*)'"), 1, 'category'),
]
# {name = '...'} rows: menu choice tables (e.g. Tank Core's vehicle list) are
# user-facing, but the mod's internal identification tables also carry a name
# plus hull/mat/tex/slot fields and never reach the screen — those are notes.
NAMED = re.compile(r"\{name = '((?:[^'\\]|\\.)*)'")
INTERNAL = re.compile(r"\{name = '(?:[^'\\]|\\.)*'[^}]{0,240}?(?:hull|mat|tex|slot|res) =")
CHOICES = re.compile(r"choices = \{([^}]*)\}")
QSTR = re.compile(r"'((?:[^'\\]|\\.)*)'")


def run(script, *args):
    print(f'--- {Path(script).name} {" ".join(map(str, args))}')
    return subprocess.run([sys.executable, str(ROOT / script), *map(str, args)]).returncode


def diff_baseline(baseline):
    """Report lua changes vs the snapshot the current rules match."""
    src = ROOT / 'extracted'
    changed = added = removed = 0
    for f in sorted(src.rglob('*.lua')):
        rel = f.relative_to(src)
        old = baseline / rel
        if not old.exists():
            added += 1
            print('NEW lua:', rel)
        elif f.read_bytes() != old.read_bytes():
            changed += 1
            print('CHANGED lua:', rel)
            diff = difflib.unified_diff(old.read_text('utf-8').splitlines(),
                                        f.read_text('utf-8').splitlines(), lineterm='')
            for line in list(diff)[2:22]:
                print('   ', line)
    for f in sorted(baseline.rglob('*.lua')):
        rel = f.relative_to(baseline)
        if not (src / rel).exists():
            removed += 1
            print('REMOVED lua:', rel)
    if not (changed or added or removed):
        print('diff: menu sources unchanged since the last translation')
    return changed, added, removed


def untranslated_scan():
    """Split menu text still lacking CJK into real gaps and internal-table notes."""
    gaps, notes = [], []
    for f in sorted((ROOT / 'extracted_zh').rglob('*.lua')):
        text = f.read_text('utf-8')
        rel = f.relative_to(ROOT / 'extracted_zh')
        for pattern, group, kind in PATTERNS:
            for m in pattern.finditer(text):
                s = m.group(group).replace("\\'", "'")
                if not CJK.search(s):
                    gaps.append(f'{rel}: {kind} {s!r}')
        for m in CHOICES.finditer(text):
            for s in QSTR.findall(m.group(1)):
                s = s.replace("\\'", "'")
                if not CJK.search(s):
                    gaps.append(f'{rel}: choice {s!r}')
        internal = [m.span() for m in INTERNAL.finditer(text)]
        for m in NAMED.finditer(text):
            s = m.group(1).replace("\\'", "'")
            if any(lo <= m.start() < hi for lo, hi in internal):
                if not CJK.search(s):
                    notes.append(f'{rel}: internal table name {s!r}')
                continue                       # vehicle/material table: log only
            if not CJK.search(s):
                gaps.append(f'{rel}: name {s!r}')
    return gaps, notes


def main(argv):
    if len(argv) < 2:
        raise SystemExit(__doc__)
    src_zip = Path(argv[1])
    out_zip = Path(argv[2]) if len(argv) > 2 else src_zip.with_name(src_zip.stem + '-zh-Hans.zip')
    extract = src_zip.with_name(src_zip.stem + '-extract')

    # 1) unzip
    if extract.exists():
        shutil.rmtree(extract)
    with zipfile.ZipFile(src_zip) as zf:
        zf.extractall(extract)
    print(f'unpacked {src_zip.name} -> {extract.name}/')

    # manifest sanity: same GUID means the manager treats it as an update
    manifest = json.loads((extract / 'manifest.json').read_text('utf-8'))
    if manifest.get('Guid', '').lower() != KNOWN_GUID:
        print(f"WARNING manifest Guid {manifest.get('Guid')} differs from the translated {KNOWN_GUID}")

    # 2) extract patch resources
    if (ROOT / 'extracted').exists():
        shutil.rmtree(ROOT / 'extracted')
    patches = sorted(extract.rglob(PATCH))
    if not patches:
        print(f'no {PATCH} in the mod — layout changed?')
        return 1
    for p in patches:
        if run('patch_tool.py', 'extract', p, ROOT / 'extracted' / p.parent.relative_to(extract)):
            return 1

    # 3) diff vs baseline
    baseline = ROOT / 'baseline'
    if baseline.exists():
        diff_baseline(baseline)
    else:
        print('diff: no baseline yet (first run for these rules)')

    # 4) rules
    if run('translate.py') != 0:
        print('\n>> 规则未命中：打开 ArmoredOverhaul-zh-Hans/translate.py，'
              '按上面的 diff / 报错把过期规则改成新英文的译文，然后重跑本命令。')
        return 1

    # 5) untranslated menu text (new or renamed options the rules do not cover)
    gaps, notes = untranslated_scan()
    print(f'untranslated menu texts: {len(gaps)} (plus {len(notes)} internal-table note(s))')
    for gap in gaps[:20]:
        print('   ', gap)
    for note in notes[:10]:
        print('    note:', note)
    if gaps:
        print('\n>> 上面这些菜单文本还没有中文规则（多半是新增/改名选项）：'
              '在 translate.py 里补规则后重跑本命令，不用安装这一版。')
        return 1

    # 6) rebuild + pack, 7) verify
    if run('build_zh.py', extract, out_zip) != 0:
        return 1
    if run('verify_zh.py', src_zip, out_zip) != 0:
        print('>> 校验未通过：不要安装这份 zip；按输出排查后重跑。')
        return 1

    # 8) snapshot for the next update
    if baseline.exists():
        shutil.rmtree(baseline)
    shutil.copytree(ROOT / 'extracted', baseline)
    print(f'baseline refreshed -> {baseline.name}/')
    print(f'OK: {out_zip}')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
