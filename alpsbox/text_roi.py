# -*- coding: utf-8 -*-
"""English and Chinese strings for the ROI management module (registered with
i18n.STRINGS)."""
from .i18n import register_strings

STRINGS = {
    # Anatomical labels (shown in reports and logs)
    "roim.anat.L_proj": {
        "zh_CN": "上放射冠 左 (Superior corona radiata L)",
        "en": "Superior corona radiata L (projection fibres)"},
    "roim.anat.R_proj": {
        "zh_CN": "上放射冠 右 (Superior corona radiata R)",
        "en": "Superior corona radiata R (projection fibres)"},
    "roim.anat.L_asso": {
        "zh_CN": "上纵束 左 (Superior longitudinal fasciculus L)",
        "en": "Superior longitudinal fasciculus L (association fibres)"},
    "roim.anat.R_asso": {
        "zh_CN": "上纵束 右 (Superior longitudinal fasciculus R)",
        "en": "Superior longitudinal fasciculus R (association fibres)"},

    # describe() (printed in the processing log)
    "roim.desc.source": {"zh_CN": "    ROI 来源: %s (%s)",
                         "en": "    ROI source: %s (%s)"},
    "roim.desc.anatomy": {"zh_CN": "               解剖: %s",
                          "en": "               anatomy: %s"},

    # Error messages
    "roim.err.bundled_missing": {
        "zh_CN": "随包参考 ROI 缺失: %s\n  目录: %s\n"
                 "  这些文件来自 gbarisano/alps（MIT 许可），每个 81 体素。",
        "en": "Bundled reference ROIs are missing: %s\n  directory: %s\n"
              "  These files come from gbarisano/alps (MIT License), "
              "81 voxels each."},
    "roim.err.custom_count": {
        "zh_CN": "自定义 ROI 必须恰好 4 个，实际 %d 个",
        "en": "Exactly 4 custom ROIs are required, got %d"},
    "roim.err.file_missing": {"zh_CN": "ROI 文件不存在: %s",
                              "en": "ROI file not found: %s"},
    "roim.err.need_runner": {
        "zh_CN": "generate_spheres 需要 Runner 来调用 fslmaths",
        "en": "generate_spheres needs a Runner to call fslmaths"},
}

register_strings(STRINGS)
