"""
.po → .mo компилятору (gettext орнотулбаса да иштейт, Windows'та да).
Колдонуу:  python scripts/compile_po.py
locale/*/LC_MESSAGES/django.po файлдарын django.mo кылып компиляциялайт.
"""
import ast
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def parse_po(path):
    messages, msgid, msgstr, section = {}, None, None, None
    fuzzy = False

    def flush():
        if msgid is not None and msgstr is not None and not fuzzy and (msgstr or msgid == ""):
            messages[msgid] = msgstr

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("#,") and "fuzzy" in line:
            fuzzy = True
        elif line.startswith("msgid "):
            flush()
            msgid, msgstr, section = ast.literal_eval(line[6:]), None, "id"
        elif line.startswith("msgstr "):
            msgstr, section = ast.literal_eval(line[7:]), "str"
        elif line.startswith('"'):
            if section == "id":
                msgid += ast.literal_eval(line)
            elif section == "str":
                msgstr += ast.literal_eval(line)
        elif not line:
            flush()
            msgid = msgstr = section = None
            fuzzy = False
    flush()
    return messages


def write_mo(messages, path):
    keys = sorted(messages)
    ids = b"".join(k.encode() + b"\0" for k in keys)
    strs = b"".join(messages[k].encode() + b"\0" for k in keys)
    n = len(keys)
    header = 7 * 4
    o_ids, o_strs = header, header + n * 8
    data_start = o_strs + n * 8
    id_table, str_table = [], []
    pos = data_start
    for k in keys:
        b = k.encode()
        id_table.append((len(b), pos))
        pos += len(b) + 1
    for k in keys:
        b = messages[k].encode()
        str_table.append((len(b), pos))
        pos += len(b) + 1
    out = struct.pack("<7I", 0x950412DE, 0, n, o_ids, o_strs, 0, 0)
    out += b"".join(struct.pack("<2I", *t) for t in id_table)
    out += b"".join(struct.pack("<2I", *t) for t in str_table)
    out += ids + strs
    path.write_bytes(out)


if __name__ == "__main__":
    for po in ROOT.glob("locale/*/LC_MESSAGES/django.po"):
        msgs = parse_po(po)
        write_mo(msgs, po.with_suffix(".mo"))
        print(f"{po.relative_to(ROOT)}: {len(msgs) - 1} котормо → django.mo")
