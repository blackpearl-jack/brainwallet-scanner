#!/usr/bin/env python3
"""Brainwallet Scanner - GitHub Actions Edition"""
import hashlib, urllib.request, sys, os
from concurrent.futures import ThreadPoolExecutor, as_completed

HITS_FILE = "hits.txt"
CHECKPOINT = "checkpoint.txt"
WORKERS = 8

def brain_addr(phrase):
    h = hashlib.sha256(phrase.encode()).hexdigest()
    try:
        from bitcoin import privkey_to_address
        return privkey_to_address(h)
    except: return None

def check_bal(addr):
    try:
        url = "https://blockchain.info/q/addressbalance/" + addr
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        return int(urllib.request.urlopen(req, timeout=8).read())
    except: return None

def process(phrase, idx, total):
    addr = brain_addr(phrase)
    if addr is None: return None
    bal = check_bal(addr)
    if bal and bal > 0:
        return f"[{bal/1e8:.8f} BTC] [{idx}/{total}] {phrase[:50]} | {addr}"
    return None

def load_list(path):
    words = []
    with open(path, "r", encoding="latin-1", errors="ignore") as f:
        for line in f:
            w = line.strip()
            if 3 <= len(w) <= 80: words.append(w)
    return words

def load_check():
    if os.path.exists(CHECKPOINT):
        with open(CHECKPOINT) as f: return int(f.readline().strip())
    return 0

def save_check(idx):
    with open(CHECKPOINT, "w") as f: f.write(f"{idx}\n")

path = sys.argv[1] if len(sys.argv) > 1 else "rockyou.txt"
words = load_list(path)
total = len(words)
start_idx = load_check()
batch_end = min(start_idx + 5000, total)
words = words[start_idx:batch_end]
print(f"[*] Brainwallet Scanner")
print(f"[*] Range: {start_idx:,} - {batch_end:,} / {total:,}")

hits = 0
count = 0
with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    futures = {}
    for i, w in enumerate(words):
        idx = start_idx + i
        futures[ex.submit(process, w, idx, total)] = idx
        if len(futures) >= 50 or (i == len(words) - 1):
            for f in as_completed(list(futures.keys())):
                r = f.result()
                count += 1
                if r:
                    hits += 1
                    print(f"FIRE {r}")
                    with open(HITS_FILE, "a") as fh: fh.write(r + "\n")
            futures = {}
            if count % 50 == 0:
                pct = (start_idx + count) / total * 100
                print(f"  [{pct:.2f}%] Checked: {start_idx+count:,} | Hits: {hits}")

save_check(batch_end)
print(f"\n[*] Done: {count} checked, {hits} hits")
if hits > 0: print("FOUND_BTC=1")
