#!/usr/bin/env python3
from pathlib import Path
import json
import sys

root = Path(sys.argv[1])
out = Path(sys.argv[2])

sdk_paths = (
    "/com/google/android/gms/ads/",
    "/com/google/ads/",
    "/com/applovin/",
    "/com/ironsource/",
    "/com/unity3d/ads/",
    "/com/unity3d/ironsourceads/",
    "/com/facebook/ads/",
    "/com/adcolony/",
    "/com/cleveradssolutions/",
    "/com/monetrix/adsdk/",
    "/com/vungle/",
    "/com/mbridge/",
    "/com/bytedance/",
)

needles = (
    "cleveradssolutions",
    "interstitialadmanager",
    "mediationmanager",
    "loadad",
    "showad",
    "showinterstitial",
    "interstitial",
    "rewarded",
    "google/android/gms/ads",
    "applovin",
    "ironsource",
    "unityads",
    "facebook/ads",
    "vungle",
    "monetrix",
)

hits = []

for base in root.glob("smali*"):
    if not base.is_dir():
        continue
    for f in base.rglob("*.smali"):
        p = str(f).replace("\\", "/")
        if any(x in p for x in sdk_paths):
            continue
        text = f.read_text(errors="ignore")
        low = text.lower()
        if not any(n in low for n in needles):
            continue

        lines = text.splitlines()
        match_indexes = [
            i for i, line in enumerate(lines)
            if any(n in line.lower() for n in needles)
        ]
        contexts = []
        covered = set()
        for i in match_indexes[:40]:
            a = max(0, i - 8)
            b = min(len(lines), i + 9)
            if any(j in covered for j in range(a, b)):
                continue
            covered.update(range(a, b))
            contexts.append({
                "line": i + 1,
                "context": [f"{j+1}: {lines[j].strip()}" for j in range(a, b)]
            })

        methods = [
            f"{i+1}: {line.strip()}"
            for i, line in enumerate(lines)
            if line.lstrip().startswith(".method")
        ]
        hits.append({"file": p, "contexts": contexts, "methods": methods[:100]})

report = {"application_ad_hits": hits}
out.write_text(json.dumps(report, ensure_ascii=False, indent=2))

print("=== KIBO APPLICATION AD CALL SITES ===")
for h in hits:
    print("\nFILE:", h["file"])
    for c in h["contexts"]:
        print("  around line", c["line"])
        for line in c["context"]:
            print("   ", line)
print("\nFocused Kibo audit written:", out)
