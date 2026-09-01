#
# Copyright (C) 2021-2025 The LineageOS Project
#
# SPDX-License-Identifier: Apache-2.0
#

# Partitions
BOARD_SUPER_PARTITION_SIZE := 17272340480

# Include the common OEM chipset BoardConfig.
include device/oneplus/sm8750-common/BoardConfigCommon.mk

DEVICE_PATH := device/oneplus/ktm

# Assert
TARGET_OTA_ASSERT_DEVICE := OP6113L1,PLQ110

# Display
TARGET_SCREEN_DENSITY := 560

# Framework Manifest
DEVICE_FRAMEWORK_COMPATIBILITY_MATRIX_FILE += $(DEVICE_PATH)/framework_compatibility_manifest.xml

# Kernel
TARGET_KERNEL_ADDITIONAL_FLAGS += CONFIG_KTM_DTB=y

# Properties
TARGET_ODM_PROP += $(DEVICE_PATH)/odm.prop
TARGET_PRODUCT_PROP += $(DEVICE_PATH)/product.prop
TARGET_SYSTEM_EXT_PROP += $(DEVICE_PATH)/system_ext.prop
TARGET_VENDOR_PROP += $(DEVICE_PATH)/vendor.prop

# Recovery
TARGET_RECOVERY_UI_MARGIN_HEIGHT := 103

# SELinux
BOARD_VENDOR_SEPOLICY_DIRS += $(DEVICE_PATH)/sepolicy/vendor
SYSTEM_EXT_PUBLIC_SEPOLICY_DIRS += $(DEVICE_PATH)/sepolicy/public
SYSTEM_EXT_PRIVATE_SEPOLICY_DIRS += $(DEVICE_PATH)/sepolicy/private

# Include the proprietary files BoardConfig.
include vendor/oneplus/ktm/BoardConfigVendor.mk
