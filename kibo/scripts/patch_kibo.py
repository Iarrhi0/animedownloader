#!/usr/bin/env python3
from pathlib import Path
import re,sys
root=Path(sys.argv[1])
manifest=root/"AndroidManifest.xml"
s=manifest.read_text(errors="ignore")
# Disable manifest-declared components belonging to common ad SDKs.
ad_tokens=("com.google.android.gms.ads","com.applovin","com.ironsource","com.unity3d.ads","com.facebook.ads","com.adcolony")
lines=[]
for line in s.splitlines():
    if any(t in line for t in ad_tokens) and any(x in line for x in ("<activity","<service","<receiver","<provider")):
        continue
    lines.append(line)
manifest.write_text("\n".join(lines))
# Patch common ad SDK calls in app-owned smali only. We deliberately do not alter media/auth/DRM code.
appdirs=[p for p in root.glob("smali*") if p.is_dir()]
patterns=[
    ("Lcom/google/android/gms/ads/MobileAds;->initialize", "admob"),
    ("Lcom/applovin/sdk/AppLovinSdk;->initializeSdk", "applovin"),
    ("Lcom/ironsource/mediationsdk/IronSource;->init", "ironsource"),
    ("Lcom/unity3d/ads/UnityAds;->initialize", "unity"),
]
count=0
for base in appdirs:
    for f in base.rglob("*.smali"):
        # Leave third-party SDK implementation trees intact; patch call sites only.
        p=str(f).replace("\\","/")
        if any(x in p for x in ("/com/google/android/gms/ads/","/com/applovin/","/com/ironsource/","/com/unity3d/ads/","/com/facebook/ads/","/com/adcolony/")):
            continue
        txt=f.read_text(errors="ignore")
        old=txt
        # Replace SDK init invoke lines with no-op. This is intentionally conservative.
        out=[]
        for line in txt.splitlines():
            if "invoke-" in line and any(sig in line for sig,_ in patterns):
                out.append("    # KIBO_PATCH ad init disabled: "+line.strip())
                count+=1
            else:
                out.append(line)
        if txt!=old or count:
            new="\n".join(out)+"\n"
            if new!=txt: f.write_text(new)
print("Kibo patch complete; ad init calls disabled:",count)
