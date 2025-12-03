#!/usr/bin/env python3
"""
Parse DataSetup/os_info.txt and build an os_function_database.json containing:
- function/class/other entries with name, signature, description
- tokenization (token ids and tokens) using the underlying transformer tokenizer
- embeddings computed with sentence-transformers

Usage:
    pip install sentence-transformers transformers torch
    python DataSetup/embedder.py --input DataSetup/os_info.txt --output sublimePlugin/os_function_database.json
"""

import os
import re
import json
import argparse
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer
import numpy as np

RE_FUNC = re.compile(r'^Function:\s*(.+)$')
RE_CLASS = re.compile(r'^Class:\s*(.+)$')
RE_SIGNATURE = re.compile(r'^Signature:\s*(.+)$')
RE_DESCRIPTION = re.compile(r'^Description:\s*(.*)$')

DEFAULT_MODEL = "all-MiniLM-L6-v2"

def parse_os_info_file(path):
    entries = []
    with open(path, 'r', encoding='utf-8') as f:
        lines = [ln.rstrip('\n') for ln in f]

    i = 0
    n = len(lines)
    current = None

    def push_current():
        nonlocal current
        if current:
            # Normalize description
            current['description'] = current.get('description', '').strip()
            entries.append(current)
            current = None

    while i < n:
        ln = lines[i].strip()
        mfunc = RE_FUNC.match(ln)
        mclass = RE_CLASS.match(ln)

        if mfunc:
            # push previous
            push_current()
            current = {'type': 'function', 'name': mfunc.group(1).strip(), 'signature': '', 'description': ''}
            i += 1
            continue

        if mclass:
            push_current()
            current = {'type': 'class', 'name': mclass.group(1).strip(), 'signature': '', 'description': ''}
            i += 1
            continue

        msign = RE_SIGNATURE.match(ln)
        if msign and current is not None:
            current['signature'] = msign.group(1).strip()
            i += 1
            continue

        mdesc = RE_DESCRIPTION.match(ln)
        if mdesc and current is not None:
            desc_line = mdesc.group(1)
            # gather subsequent lines until blank or next Function/Class/OTHER MEMBERS marker
            desc_lines = [desc_line]
            j = i + 1
            while j < n:
                nxt = lines[j]
                if nxt.strip() == "":
                    desc_lines.append("")
                    j += 1
                    continue
                if RE_FUNC.match(nxt.strip()) or RE_CLASS.match(nxt.strip()) or nxt.startswith("OTHER MEMBERS") or nxt.startswith("="):
                    break
                # If the next line starts with a field marker (like "Signature:"), stop
                if RE_SIGNATURE.match(nxt.strip()):
                    break
                desc_lines.append(nxt)
                j += 1
            current['description'] = "\n".join(desc_lines).strip()
            i = j
            continue

        # handle "OTHER MEMBERS" - simple parsing: lines like "NAME: TYPE = VALUE"
        if ln.startswith("OTHER MEMBERS") or ln.startswith("OTHER MEMBERS ("):
            push_current()
            # consume until SUMMARY or end
            i += 1
            while i < n and not lines[i].startswith("SUMMARY") and not lines[i].startswith("="):
                # try to parse lines like "name: type = value"
                line = lines[i].strip()
                if ":" in line:
                    name, rest = line.split(':', 1)
                    entries.append({'type': 'other', 'name': name.strip(), 'signature': '', 'description': rest.strip()})
                i += 1
            continue

        i += 1

    push_current()
    return entries

def build_database(input_path, output_path, model_name=DEFAULT_MODEL, max_length=512):
    # parse
    entries = parse_os_info_file(input_path)
    if len(entries) == 0:
        print("No entries parsed from", input_path)
        return False

    # prepare texts
    texts = []
    for e in entries:
        s = e.get('name', '')
        if e.get('signature'):
            s += " " + e['signature']
        if e.get('description'):
            s += "\n" + e['description']
        texts.append(s)

    # load models
    print("Loading embedding model:", model_name)
    embedder_model = SentenceTransformer(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    # compute embeddings (numpy array)
    embeddings = embedder_model.encode(texts, show_progress_bar=True, convert_to_numpy=True)

    # compute tokenization (ids & tokens) for each text
    tokenized = []
    for txt in texts:
        tok = tokenizer(txt, truncation=True, max_length=max_length, return_attention_mask=False)
        token_ids = tok['input_ids']
        # convert ids back to token strings where possible
        tokens = tokenizer.convert_ids_to_tokens(token_ids)
        tokenized.append({'input_ids': token_ids, 'tokens': tokens})

    # prepare JSON database
    db = {
        'meta': {
            'source': os.path.basename(input_path),
            'model': model_name,
            'num_entries': len(entries)
        },
        'entries': []
    }

    for e, t, emb, tok in zip(entries, texts, embeddings, tokenized):
        db['entries'].append({
            'type': e.get('type', 'function'),
            'name': e.get('name', ''),
            'signature': e.get('signature', ''),
            'description': e.get('description', ''),
            'text': t,
            'tokens': tok['tokens'],
            'input_ids': tok['input_ids'],
            'embedding': emb.tolist()
        })

    # write json
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

    print("Database written to", output_path)
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build os function embedding DB")
    parser.add_argument('--input', '-i', default='DataSetup/os_info.txt', help='Path to os_info.txt')
    parser.add_argument('--output', '-o', default='sublimePlugin/os_function_database.json', help='Output JSON database path')
    parser.add_argument('--model', '-m', default=DEFAULT_MODEL, help='Sentence-transformers model name')
    args = parser.parse_args()

    build_database(args.input, args.output, model_name=args.model)