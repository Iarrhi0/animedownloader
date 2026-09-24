#!/usr/bin/env python3
from pathlib import Path
import json,re,sys
root=Path(sys.argv[1]); out=Path(sys.argv[2])
patterns={
 "google_ads":r"com/google/android/gms/ads|AdView|InterstitialAd|RewardedAd",
 "applovin":r"com/applovin|MaxInterstitialAd|MaxAdView",
 "ironsource":r"com/ironsource|IronSource",
 "unity_ads":r"com/unity3d/ads|UnityAds",
 "facebook_ads":r"com/facebook/ads|AudienceNetworkAds",
 "adcolony":r"com/adcolony",
 "generic_ad_calls":r"loadAd|showAd|showInterstitial|interstitial|rewarded|banner"
}
hits={k:[] for k in patterns}
for base in root.glob("smali*"):
 if not base.is_dir(): continue
 for f in base.rglob("*.smali"):
  p=str(f).replace("\\","/")
  # Report application call sites, not thousands of SDK implementation classes.
  if any(x in p for x in ("/com/google/android/gms/ads/","/com/applovin/","/com/ironsource/","/com/unity3d/ads/","/com/facebook/ads/","/com/adcolony/")): continue
  t=f.read_text(errors="ignore")
  for k,rx in patterns.items():
   if re.search(rx,t,re.I):
    lines=[f"{i+1}: {line.strip()}" for i,line in enumerate(t.splitlines()) if re.search(rx,line,re.I)]
    hits[k].append({"file":p,"lines":lines[:30]})
manifest=root/"AndroidManifest.xml"
report={"manifest":manifest.read_text(errors="ignore") if manifest.exists() else "","hits":hits}
out.write_text(json.dumps(report,ensure_ascii=False,indent=2))
print("Kibo audit written:",out)
