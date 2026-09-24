# Kibo patch workspace

This folder is for patching the user-supplied Kibo XAPK in GitHub Actions.

## Input required
Place the original file at `kibo/input/kibo.xapk`.

The workflow decodes the base APK, applies a conservative ad-SDK patch, rebuilds, aligns and signs it, then uploads `KIBO-PATCHED-APK`.

The first build intentionally targets ad removal only. Multiple-download behavior requires identifying Kibo's own download manager classes after a successful decoded build; it is not faked by this patch.
