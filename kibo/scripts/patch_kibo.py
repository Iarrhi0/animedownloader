#!/usr/bin/env python3
from pathlib import Path
import re
import sys

root = Path(sys.argv[1])

# KIBO SHIELD V2
#
# Strategy:
# 1) stop ad SDK initialization where Kibo explicitly requests it;
# 2) stop ad LOAD calls, which is safer than blindly removing SHOW calls:
#    when an interstitial is never loaded, normal app code usually follows its
#    "ad unavailable" path instead of opening a blocking full-screen Activity;
# 3) force common "isLoaded/isReady" checks to false;
# 4) leave media/network traffic untouched, so Kibo can still browse/download.
#
# We deliberately do NOT fake premium/subscription state.

SDK_PATHS = (
    "/com/google/android/gms/ads/",
    "/com/google/ads/",
    "/com/applovin/",
    "/com/ironsource/",
    "/com/unity3d/ads/",
    "/com/facebook/ads/",
    "/com/adcolony/",
)

INIT_SIGNATURES = (
    "Lcom/google/android/gms/ads/MobileAds;->initialize",
    "Lcom/applovin/sdk/AppLovinSdk;->initializeSdk",
    "Lcom/ironsource/mediationsdk/IronSource;->init",
    "Lcom/unity3d/ads/UnityAds;->initialize",
    "Lcom/facebook/ads/AudienceNetworkAds;->initialize",
)

# Calls that schedule/fetch/display advertising inventory.
# Most of these return void, so replacing the invoke with a no-op is safe.
LOAD_SIGNATURES = (
    "Lcom/google/android/gms/ads/AdView;->loadAd",
    "Lcom/google/android/gms/ads/BaseAdView;->loadAd",
    "Lcom/google/android/gms/ads/interstitial/InterstitialAd;->load",
    "Lcom/google/android/gms/ads/admanager/AdManagerInterstitialAd;->load",
    "Lcom/google/android/gms/ads/rewarded/RewardedAd;->load",
    "Lcom/google/android/gms/ads/rewardedinterstitial/RewardedInterstitialAd;->load",
    "Lcom/google/android/gms/ads/appopen/AppOpenAd;->load",
    "Lcom/applovin/mediation/ads/MaxInterstitialAd;->loadAd",
    "Lcom/applovin/mediation/ads/MaxRewardedAd;->loadAd",
    "Lcom/applovin/mediation/ads/MaxAdView;->loadAd",
    "Lcom/applovin/adview/AppLovinAdView;->loadNextAd",
    "Lcom/ironsource/mediationsdk/IronSource;->loadInterstitial",
    "Lcom/ironsource/mediationsdk/IronSource;->loadRewardedVideo",
    "Lcom/unity3d/ads/UnityAds;->load",
    "Lcom/facebook/ads/InterstitialAd;->loadAd",
    "Lcom/facebook/ads/RewardedVideoAd;->loadAd",
    "Lcom/facebook/ads/AdView;->loadAd",
    "Lcom/adcolony/sdk/AdColony;->requestInterstitial",
)

# If app code asks whether a full-screen ad is ready, force "false".
READY_SIGNATURES = (
    "Lcom/google/android/gms/ads/interstitial/InterstitialAd;->isLoaded",
    "Lcom/applovin/mediation/ads/MaxInterstitialAd;->isReady",
    "Lcom/applovin/mediation/ads/MaxRewardedAd;->isReady",
    "Lcom/ironsource/mediationsdk/IronSource;->isInterstitialReady",
    "Lcom/ironsource/mediationsdk/IronSource;->isRewardedVideoAvailable",
    "Lcom/unity3d/ads/UnityAds;->isReady",
    "Lcom/facebook/ads/InterstitialAd;->isAdLoaded",
    "Lcom/facebook/ads/RewardedVideoAd;->isAdLoaded",
    "Lcom/adcolony/sdk/AdColonyInterstitial;->isExpired",
)

patched_init = 0
patched_load = 0
patched_ready = 0
files_changed = 0

for base in root.glob("smali*"):
    if not base.is_dir():
        continue
    for f in base.rglob("*.smali"):
        normalized = str(f).replace("\\", "/")

        # Do not rewrite the SDK's own implementation classes. We patch only
        # Kibo/application call sites to reduce the chance of corrupting a SDK.
        if any(p in normalized for p in SDK_PATHS):
            continue

        lines = f.read_text(errors="ignore").splitlines()
        out = []
        i = 0
        changed = False

        while i < len(lines):
            line = lines[i]

            if "invoke-" in line and any(sig in line for sig in INIT_SIGNATURES):
                out.append("    # KIBO_SHIELD_V2: ad SDK initialization skipped")
                patched_init += 1
                changed = True
                i += 1
                continue

            if "invoke-" in line and any(sig in line for sig in LOAD_SIGNATURES):
                out.append("    # KIBO_SHIELD_V2: ad load request blocked")
                patched_load += 1
                changed = True

                # Defensive handling: if this particular SDK/version returns a
                # value and the next instruction consumes move-result*, replace
                # it with a null/false value instead of leaving invalid smali.
                if i + 1 < len(lines):
                    m = re.match(r"\s*move-result(?:-object|-wide)?\s+([vp]\d+)", lines[i + 1])
                    if m:
                        reg = m.group(1)
                        if "move-result-wide" in lines[i + 1]:
                            out.append(f"    const-wide/16 {reg}, 0x0")
                        else:
                            out.append(f"    const/4 {reg}, 0x0")
                        i += 2
                        continue
                i += 1
                continue

            if "invoke-" in line and any(sig in line for sig in READY_SIGNATURES):
                out.append("    # KIBO_SHIELD_V2: ad readiness forced false")
                patched_ready += 1
                changed = True
                if i + 1 < len(lines):
                    m = re.match(r"\s*move-result\s+([vp]\d+)", lines[i + 1])
                    if m:
                        out.append(f"    const/4 {m.group(1)}, 0x0")
                        i += 2
                        continue
                # If no expected move-result follows, keep the original call.
                out[-1] = line
                patched_ready -= 1
                changed = changed and False
                i += 1
                continue

            out.append(line)
            i += 1

        if changed:
            f.write_text("\n".join(out) + "\n")
            files_changed += 1

print(
    "Kibo Shield V2 complete: "
    f"{patched_init} init call(s), "
    f"{patched_load} ad load call(s), "
    f"{patched_ready} readiness check(s) neutralized "
    f"across {files_changed} app file(s)."
)

if patched_init + patched_load + patched_ready == 0:
    print(
        "WARNING: no known ad call sites were patched. "
        "Inspect audit.json before treating this build as ad-blocked."
    )
