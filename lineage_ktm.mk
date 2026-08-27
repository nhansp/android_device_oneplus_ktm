#
# Copyright (C) 2021-2026 The LineageOS Project
#
# SPDX-License-Identifier: Apache-2.0
#

# Inherit from those products. Most specific first.
$(call inherit-product, $(SRC_TARGET_DIR)/product/core_64_bit_only.mk)
$(call inherit-product, $(SRC_TARGET_DIR)/product/full_base_telephony.mk)

# Inherit from ktm device
$(call inherit-product, device/oneplus/ktm/device.mk)

# Inherit some common Lineage stuff.
$(call inherit-product, vendor/lineage/config/common_full_phone.mk)

PRODUCT_NAME := lineage_ktm
PRODUCT_DEVICE := ktm
PRODUCT_MANUFACTURER := OnePlus
PRODUCT_BRAND := OnePlus
PRODUCT_MODEL := PLQ110

EVO_BUILD_TYPE := Unofficial
TARGET_BOOT_ANIMATION_RES := 1080
TARGET_BUILD_APERTURE_CAMERA := true
TARGET_INCLUDE_ACCORD := false

PRODUCT_GMS_CLIENTID_BASE := android-oneplus

PRODUCT_BUILD_PROP_OVERRIDES += \
    BuildDesc="qssi-user 16 BP2A.250605.015 1762272835359 release-keys" \
    BuildFingerprint=OnePlus/PLQ110/OP6113L1:16/BP2A.250605.015/B.146141d_c644d2_c644d1:user/release-keys \
    DeviceName=OP6113L1 \
    DeviceProduct=PLQ110 \
    SystemDevice=OP6113L1 \
    SystemName=PLQ110
    
