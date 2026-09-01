#
# Copyright (C) 2021-2026 The LineageOS Project
#
# SPDX-License-Identifier: Apache-2.0
#

# AAPT
PRODUCT_AAPT_CONFIG := normal
PRODUCT_AAPT_PREF_CONFIG := xxxhdpi

# Audio
PRODUCT_COPY_FILES += \
    $(LOCAL_PATH)/configs/audio/audio_policy_volumes.xml:$(TARGET_COPY_OUT_VENDOR)/etc/audio_policy_volumes.xml \
    $(LOCAL_PATH)/configs/audio/default_volume_tables.xml:$(TARGET_COPY_OUT_VENDOR)/etc/default_volume_tables.xml

# Boot animation
TARGET_SCREEN_HEIGHT := 2800
TARGET_SCREEN_WIDTH := 1272

# Display
PRODUCT_COPY_FILES += \
    $(LOCAL_PATH)/configs/display/displayconfig.xml:$(TARGET_COPY_OUT_VENDOR)/etc/displayconfig/display_id_4630947185118785939.xml

# Keylayout
PRODUCT_COPY_FILES += \
    $(LOCAL_PATH)/configs/keylayout/gpio-keys.kl:$(TARGET_COPY_OUT_VENDOR)/usr/keylayout/gpio-keys.kl

# LiveDisplay
$(call soong_config_set_bool,OPLUS_LINEAGE_LIVEDISPLAY_HAL,ENABLE_AF,true)

# NFC
PRODUCT_PACKAGES += \
    NfcNci 

PRODUCT_COPY_FILES += \
    $(LOCAL_PATH)/configs/nfc/libnfc-tmsTransit.conf_24851:$(TARGET_COPY_OUT_ODM)/etc/nfc/libnfc-tmsTransit.conf_24851 \
    $(LOCAL_PATH)/configs/nfc/init.thn31.nfc.rc:$(TARGET_COPY_OUT_ODM)/etc/init/init.thn31.nfc.rc

# Overlays
DEVICE_PACKAGE_OVERLAYS += \
    $(LOCAL_PATH)/overlay-lineage

PRODUCT_PACKAGES += \
    OPlusFrameworksResTarget \
    OPlusSettingsProviderResTarget \
    OPlusSettingsResTarget \
    OPlusSystemUIResTarget

# Power
$(call soong_config_set,qtipower,mode_ext_lib,power-ext-oplus)

# Recovery
PRODUCT_PACKAGES += \
    hbp-setup 
    
# Regional properties
PRODUCT_COPY_FILES += \
    $(LOCAL_PATH)/recovery/root/vendor/odm/etc/24851/build.default.prop:$(TARGET_COPY_OUT_ODM)/etc/24851/build.default.prop 

# Soong namespaces
PRODUCT_SOONG_NAMESPACES += \
    $(LOCAL_PATH)

# Touch features
$(call soong_config_set_bool,OPLUS_LINEAGE_TOUCH_HAL,ENABLE_GM,true)
$(call soong_config_set_bool,OPLUS_LINEAGE_TOUCH_HAL,ENABLE_HTPR,false)

# Udfps
TARGET_HAS_UDFPS := true

# Vibrator
$(call soong_config_set_bool,OPLUS_LINEAGE_VIBRATOR_HAL,USE_EFFECT_STREAM,true)

# Inherit from the common OEM chipset makefile.
$(call inherit-product, device/oneplus/sm8750-common/common.mk)

# Inherit from the proprietary files makefile.
$(call inherit-product, vendor/oneplus/ktm/ktm-vendor.mk)

# Inherit the stock camera package. Ships the odm/etc/camera assets our blob
# list misses, and the OPlus camera app as a privileged prebuilt that overrides
# Aperture and Camera2.
$(call inherit-product, vendor/oneplus/ktm-opluscamera/ktm-opluscamera-vendor.mk)
