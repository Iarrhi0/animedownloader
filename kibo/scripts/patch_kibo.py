#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1])

# Keep AndroidManifest.xml structurally untouched. The previous line-based
# component removal could corrupt multi-line XML declarations.
# Neutralize only explicit ad-SDK initialization call sites in app code.
signatures = (
    "Lcom/google/android/gms/ads/MobileAds;->initialize",
    "Lcom/applovin/sdk/AppLovinSdk;->initializeSdk",
    "Lcom/ironsource/mediationsdk/IronSource;->init",
    "Lcom/unity3d/ads/UnityAds;->initialize",
)

sdk_paths = (
    "/com/google/android/gms/ads/",
    "/com/applovin/",
    "/com/ironsource/",
    "/com/unity3d/ads/",
    "/com/facebook/ads/",
    "/com/adcolony/",
)

patched = 0
for base in root.glob("smali*"):
    if not base.is_dir():
        continue
    for f in base.rglob("*.smali"):
        normalized = str(f).replace("\\", "/")
        if any(p in normalized for p in sdk_paths):
            continue
        text = f.read_text(errors="ignore")
        out = []
        changed = False
        for line in text.splitlines():
            if "invoke-" in line and any(sig in line for sig in signatures):
                out.append("    # KIBO_PATCH: ad SDK initialization disabled")
                changed = True
                patched += 1
            else:
                out.append(line)
        if changed:
            f.write_text("\n".join(out) + "\n")

print(f"Kibo patch complete: {patched} ad initialization call(s) neutralized.")
