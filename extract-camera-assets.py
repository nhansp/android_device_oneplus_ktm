#!/usr/bin/env python3
"""Assemble vendor/oneplus/ktm-opluscamera from the ktm stock dump.

The package is generated output and is not version controlled -- its 171 MB
APK exceeds GitHub's 100 MB per-file limit -- so this generator is the source
of truth, the same way extract-files.py is for vendor/oneplus/ktm.
"""
import os, shutil, subprocess, sys

# Overridable so this is not pinned to one workspace.
#   STOCK_DUMP   the extracted ktm stock firmware
#   ANDROID_ROOT the AOSP tree root
STOCK = os.environ.get("STOCK_DUMP", os.path.expanduser("~/ktm-16.0.10"))
_ROOT = os.environ.get(
    "ANDROID_ROOT",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")),
)
TREE = os.path.join(_ROOT, "vendor/oneplus/ktm-opluscamera")
PROP = os.path.join(TREE, "proprietary")
STAGED = os.path.join(TREE, "staged")

# (src under STOCK, dst under proprietary/, partition var)
FILES = [
    # NOTE: OplusCamera.apk is still copied into the package (Android.bp's
    # android_app_import reads it from proprietary/), but it is NOT a
    # PRODUCT_COPY_FILES entry -- Soong installs it as a privileged module.
    ("my_product/app/OplusCamera/OplusCamera.apk",
     "product/app/OplusCamera/OplusCamera.apk", "APK"),
    ("my_product/product_overlay/framework/com.oplus.camera.unit.sdk.jar",
     "product/framework/com.oplus.camera.unit.sdk.jar", "PRODUCT"),
    ("my_product/product_overlay/framework/com.oplus.camera.unit.sdk.adapter.jar",
     "product/framework/com.oplus.camera.unit.sdk.adapter.jar", "PRODUCT"),
    ("my_product/product_overlay/etc/permissions/com.oplus.camera.unit.sdk_product.xml",
     "product/etc/permissions/com.oplus.camera.unit.sdk_product.xml", "PRODUCT"),
    # Declares all 53 com.oplus.permission.safe.* names (package "oplus", a resource-only
    # APK). Without it com.oplus.permission.safe.CAMERA is undeclared and can never be
    # granted -- see AGENTS.md 21r. Path mirrors stock; if PackageManager turns out not to
    # scan system_ext/framework, move it to system_ext/priv-app.
    ("system_ext_x/framework/oplus-framework-res.apk",
     "system_ext/framework/oplus-framework-res.apk", "SYSTEM_EXT"),
]

# Jars whose dex is inlined into the APK -- see "append the OPlus framework dex".
# Nothing in this list may also be declared as a shared library; see the XML pass.
JARS = [
    "system_x/system/framework/oplus-framework.jar",
    "my_product/product_overlay/framework/com.oplus.camera.unit.sdk.jar",
    "my_product/product_overlay/framework/com.oplus.camera.unit.sdk.adapter.jar",
]


def sh(*a):
    return subprocess.run(a, capture_output=True, text=True).stdout


def main():
    os.makedirs(PROP, exist_ok=True)
    os.makedirs(STAGED, exist_ok=True)

    copied = []
    for src, dst, part in FILES:
        s = os.path.join(STOCK, src)
        if not os.path.exists(s):
            print("MISSING FROM DUMP: " + src)
            continue
        d = os.path.join(PROP, dst)
        os.makedirs(os.path.dirname(d), exist_ok=True)
        if not (os.path.exists(d) and os.path.getsize(d) == os.path.getsize(s)):
            shutil.copy2(s, d)
        copied.append((dst, part))

    # --- odm/etc/camera assets present in stock but absent from ktm's blob list ---
    listed = set()
    pf = os.path.join(_ROOT, "device/oneplus/ktm/proprietary-files.txt")
    with open(pf) as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            p = line.split(";")[0].split("|")[0].strip().lstrip("-")
            if p.startswith("odm/etc/camera/"):
                listed.add(p)

    stock_cam = []
    base = os.path.join(STOCK, "odm/etc/camera")
    for root, _, names in os.walk(base):
        for n in names:
            full = os.path.join(root, n)
            rel = os.path.relpath(full, STOCK)
            stock_cam.append(rel)

    def _excluded(path):
        """-> reason, or None if the file is safe for PRODUCT_COPY_FILES."""
        base = os.path.basename(path)
        if base in ("Android.mk", "Android.bp", "Android.mk.orig"):
            return "stray build file (Kati/Soong would try to read it)"
        try:
            with open(path, "rb") as fh:
                if fh.read(4) == b"\x7fELF":
                    return "ELF prebuilt (PRODUCT_COPY_FILES forbids these)"
        except OSError:
            pass
        return None

    missing = sorted(set(stock_cam) - listed)
    skipped = []
    keep = []
    for rel in missing:
        why = _excluded(os.path.join(STOCK, rel))
        if why:
            skipped.append((rel, why))
            stale = os.path.join(PROP, rel)          # drop it if a previous run copied it
            if os.path.exists(stale):
                os.remove(stale)
        else:
            keep.append(rel)
    missing = keep
    if skipped:
        print("excluded %d file(s) from PRODUCT_COPY_FILES:" % len(skipped))
        for rel, why in skipped:
            print("    %s\n        %s" % (rel, why))
        print("    ^ if any of these are actually needed, add a soong module for them")

    for rel in missing:
        d = os.path.join(PROP, rel)
        os.makedirs(os.path.dirname(d), exist_ok=True)
        src_f = os.path.join(STOCK, rel)
        if not (os.path.exists(d) and os.path.getsize(d) == os.path.getsize(src_f)):
            shutil.copy2(src_f, d)
        copied.append((rel, "ODM"))

    # --- staged-only: oplus-framework.jar (NOT wired into the build, see README) ---
    os.makedirs(os.path.join(STAGED, "system/framework"), exist_ok=True)
    shutil.copy2(os.path.join(STOCK, "system_x/system/framework/oplus-framework.jar"),
                 os.path.join(STAGED, "system/framework/oplus-framework.jar"))

    # --------------- normalise + validate shipped XML ---------------
    # ColorOS ships at least one permissions XML with "<? xml" (a space before
    # the PI target). AOSP's systemfeatures-gen-tool parses every permissions
    # XML in the product at build time and rejects it, which is fatal to
    # systemfeatures-gen-srcs and therefore to nearly the whole build.
    # Normalise here, then parse, so a future stock drop that is malformed some
    # other way fails in this script instead of minutes into a build.
    import xml.dom.minidom

    inlined = set(os.path.basename(j) for j in JARS)
    fixed = 0
    unshared = 0
    for root, _, names in os.walk(PROP):
        for n in names:
            if not n.endswith(".xml"):
                continue
            fp = os.path.join(root, n)
            raw = open(fp, "rb").read()
            norm = raw.replace(b"<? xml", b"<?xml", 1)
            if norm != raw:
                open(fp, "wb").write(norm)
                fixed += 1
            try:
                doc = xml.dom.minidom.parse(fp)
            except Exception as e:
                raise SystemExit(
                    "malformed XML would break the build: %s\n  %s" % (fp, e)
                )
            # A <library> entry makes the jar a *parent* class loader of every app
            # that <uses-library>s it, and parent-first resolution means the jar's
            # own copy of a class wins over the app's. The JARS above are inlined
            # into the APK precisely because they reference com.oplus.wrapper.*,
            # which exists nowhere on this device but inside the APK -- so the
            # shared-library copy can never resolve it, and the app dies on the
            # first SDK call. Drop the declaration and let the inlined dex serve.
            # See AGENTS.md 21ao.
            drop = [e for e in doc.getElementsByTagName("library")
                    if os.path.basename(e.getAttribute("file")) in inlined]
            for e in drop:
                print("xml: %s: not declaring shared library %s (inlined into the APK)"
                      % (n, e.getAttribute("name")))
                e.parentNode.removeChild(e)
                unshared += 1
            if drop:
                with open(fp, "wb") as fh:
                    fh.write(doc.toxml("utf-8"))
    print("xml: %d normalised, %d shared-library declarations dropped, all parse"
          % (fixed, unshared))

    # --------------- append the OPlus framework dex ---------------
    # Stock's 33 dex carry none of the com.oplus.* framework classes the app
    # touches before onCreate. Append them from the jars stock keeps on
    # BOOTCLASSPATH and in product_overlay/framework. See AGENTS.md 21aj.
    import zipfile

    apk = os.path.join(PROP, "product/app/OplusCamera/OplusCamera.apk")

    def _dex_names(path):
        with zipfile.ZipFile(path) as z:
            return sorted(n for n in z.namelist()
                          if n.startswith("classes") and n.endswith(".dex"))

    have = _dex_names(apk)
    if len(have) > 33:
        print("apk: framework dex already appended (%d dex)" % len(have))
    else:
        nxt = len(have) + 1
        added = []
        with zipfile.ZipFile(apk, "a", zipfile.ZIP_STORED) as out:
            for jar in JARS:
                jp = os.path.join(STOCK, jar)
                if not os.path.isfile(jp):
                    raise SystemExit("missing jar for dex append: " + jp)
                with zipfile.ZipFile(jp) as jz:
                    for n in _dex_names(jp):
                        # ZIP_STORED: a privileged app's dex must not be compressed.
                        out.writestr("classes%d.dex" % nxt, jz.read(n))
                        added.append("classes%-2d <- %s!%s" % (nxt, os.path.basename(jar), n))
                        nxt += 1
        # The stock v2 signature is void now; strip it so Soong re-signs cleanly.
        subprocess.run(["zip", "-q", "-d", apk,
                        "META-INF/*.RSA", "META-INF/*.SF", "META-INF/MANIFEST.MF"],
                       capture_output=True)
        print("apk: appended %d dex" % len(added))
        for a in added:
            print("       " + a)

    # Validate what actually matters now that the APK is rebuilt rather than
    # presigned: the expected dex count, and that none of them are compressed.
    with zipfile.ZipFile(apk) as z:
        dex = [i for i in z.infolist()
               if i.filename.startswith("classes") and i.filename.endswith(".dex")]
        deflated = [i.filename for i in dex if i.compress_type != zipfile.ZIP_STORED]
    if len(dex) != 37:
        raise SystemExit("apk: expected 37 dex after append, found %d" % len(dex))
    if deflated:
        raise SystemExit("apk: dex must be uncompressed for a priv-app, these are not: %s"
                         % ", ".join(deflated))
    print("apk: %d dex, all uncompressed" % len(dex))

    # ---------------- makefiles ----------------
    part_var = {"PRODUCT": "$(TARGET_COPY_OUT_PRODUCT)", "ODM": "$(TARGET_COPY_OUT_ODM)",
                "SYSTEM_EXT": "$(TARGET_COPY_OUT_SYSTEM_EXT)"}
    prefix = {"PRODUCT": "product/", "ODM": "odm/", "SYSTEM_EXT": "system_ext/"}
    copied = [(d, p) for d, p in copied if p != "APK"]   # Soong installs the APK
    lines = []
    for dst, part in copied:
        rel = dst[len(prefix[part]):]
        lines.append("    $(LOCAL_PATH)/proprietary/%s:%s/%s" % (dst, part_var[part], rel))

    odm_lines = [l for l, p in zip(lines, [p for _, p in copied]) if p == "ODM"]
    app_lines = [l for l, p in zip(lines, [p for _, p in copied]) if p != "ODM"]

    mk = """# Automatically generated by device/oneplus/ktm/extract-camera-assets.py
# Source: OnePlus Ace 6 (ktm) CN stock, ColorOS 16.0.10
#
# Stock ships the camera app on /my_product, an OPlus-only partition that does
# not exist in an AOSP build. Everything from there is remapped to /product.

LOCAL_PATH := vendor/oneplus/ktm-opluscamera

# ---------------------------------------------------------------------------
# The odm/etc/camera assets.
#
# 127 files stock ships and our blob list does not -- ML models, colour LUTs,
# tuning configs, calibration and an algorithm licence. They are consumed by
# the CamX-CHI pipeline, so they improve capture for EVERY camera app on the
# device and do not depend on the OPlus camera app being installed.
# ---------------------------------------------------------------------------
PRODUCT_COPY_FILES += \\
%s

# ---------------------------------------------------------------------------
# The camera app's supporting files.
#
# com.oplus.camera.unit.sdk{,.adapter}.jar are declared as shared libraries by
# the permissions XML next to them. oplus-framework-res.apk (package "oplus")
# declares all 53 com.oplus.permission.safe.* names -- without it
# com.oplus.permission.safe.CAMERA is undeclared and can never be granted.
# ---------------------------------------------------------------------------
PRODUCT_COPY_FILES += \\
%s \\
    $(LOCAL_PATH)/permissions/privapp-permissions-oplus-camera.xml:$(TARGET_COPY_OUT_PRODUCT)/etc/permissions/privapp-permissions-oplus-camera.xml

# ---------------------------------------------------------------------------
# The app itself. Built by Android.bp as a privileged, presigned prebuilt that
# overrides Aperture and Camera2, so it becomes the only camera on the device.
# ---------------------------------------------------------------------------
PRODUCT_PACKAGES += \\
    OplusCamera
""" % (" \\\n".join(odm_lines), " \\\n".join(app_lines))

    with open(os.path.join(TREE, "ktm-opluscamera-vendor.mk"), "w") as fh:
        fh.write(mk)

    with open(os.path.join(TREE, "BoardConfigVendor.mk"), "w") as fh:
        fh.write("# vendor/oneplus/ktm-opluscamera\n"
                 "# No board-level configuration is required: every artifact in this\n"
                 "# package is a copied file, not a built module.\n")

    print("files copied: %d" % len(copied))
    print("  product: %d" % sum(1 for _, p in copied if p == "PRODUCT"))
    print("  odm/etc/camera (gap vs proprietary-files.txt): %d" % len(missing))
    print("tree size: " + sh("du", "-sh", TREE).split()[0])


if __name__ == "__main__":
    main()
