#!/usr/bin/env python3
from pathlib import Path
import json
import re
import sys

root = Path(sys.argv[1])
out = Path(sys.argv[2])

patterns = {
    "cas_refs": r"com/cleveradssolutions|InterstitialAdManager|MediationManager|CAS\.buildManager|CAS;",
    "google_ads": r"com/google/android/gms/ads|AdView|InterstitialAd|RewardedAd",
    "applovin": r"com/applovin|MaxInterstitialAd|MaxAdView|MaxRewardedAd",
    "ironsource": r"com/ironsource|unity3d/ironsourceads|IronSource",
    "unity_ads": r"com/unity3d/ads|UnityAds",
    "facebook_ads": r"com/facebook/ads|AudienceNetworkAds",
    "vungle_ads": r"com/vungle/ads|Vungle",
    "monetrix_ads": r"com/monetrix/adsdk",
    "generic_ad_calls": r"loadAd|showAd|showInterstitial|interstitial|rewarded|banner|isAdReady|isReady",
}

# Skip SDK implementation code so the report exposes Kibo/application call sites.
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

hits = {k: [] for k in patterns}
interesting_files = {}

for base in root.glob("smali*"):
    if not base.is_dir():
        continue
    for f in base.rglob("*.smali"):
        p = str(f).replace("\\", "/")
        if any(x in p for x in sdk_paths):
            continue

        lines = f.read_text(errors="ignore").splitlines()
        matched_any = False
        file_entry = []

        for k, rx in patterns.items():
            matched = [i for i, line in enumerate(lines) if re.search(rx, line, re.I)]
            if not matched:
                continue
            matched_any = True
            contexts = []
            seen = set()
            for i in matched[:20]:
                a = max(0, i - 5)
                b = min(len(lines), i + 6)
                key = (a, b)
                if key in seen:
                    continue
                seen.add(key)
                contexts.append({
                    "line": i + 1,
                    "context": [f"{j+1}: {lines[j].strip()}" for j in range(a, b)]
                })
            hits[k].append({"file": p, "contexts": contexts})

        if matched_any:
            # Keep a compact method inventory for app/obfuscated files containing ad references.
            methods = []
            for i, line in enumerate(lines):
                if line.lstrip().startswith(".method"):
                    methods.append(f"{i+1}: {line.strip()}")
            interesting_files[p] = methods[:120]

manifest = root / "AndroidManifest.xml"
report = {
    "manifest": manifest.read_text(errors="ignore") if manifest.exists() else "",
    "hits": hits,
    "interesting_files": interesting_files,
}
out.write_text(json.dumps(report, ensure_ascii=False, indent=2))
print("Kibo focused ad audit written:", out)
print(json.dumps({"hits": hits}, ensure_ascii=False, indent=2))
