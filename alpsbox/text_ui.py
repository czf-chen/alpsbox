# -*- coding: utf-8 -*-
"""Interface strings for ALPSbox widgets, sessions and prompts (registered with
i18n.STRINGS).

These strings used to be scattered under alpsbox/ui/; they are now all shown in
the current interface language.
"""
from .i18n import register_strings

STRINGS = {
    "ui.status_ok": {"zh_CN": "成功", "en": "ok"},
    "ui.status_failed": {"zh_CN": "失败", "en": "Failed"},
    "ui.status_fail": {"zh_CN": "失败", "en": "failed"},
    "ui.file_missing": {"zh_CN": "文件不存在", "en": "File not found"},
    "ui.no_data_rows": {"zh_CN": "文件里没有数据行",
                        "en": "The file contains no data rows"},
    "ui.bad_json": {"zh_CN": "JSON 结构无法识别（需要 records 数组）",
                    "en": "Unrecognised JSON structure (expected a records array)"},
    "ui.import_json": {"zh_CN": "导入 %d 条（JSON）",
                       "en": "Imported %d records (JSON)"},
    "ui.import_n": {"zh_CN": "导入 %d 条（%s）",
                    "en": "Imported %d records (%s)"},
    "ui.read_fail": {"zh_CN": "读取失败: %s", "en": "Read failed: %s"},
    "ui.projection_note": {"zh_CN": "（最大值投影）", "en": " (maximum projection)"},
    "ui.plot_fail": {"zh_CN": "绘图失败：%s", "en": "Plot failed: %s"},
    "ui.roi_preview_unavailable": {"zh_CN": "ROI 预览不可用：%s",
                                   "en": "ROI preview unavailable: %s"},
    "ui.help_title": {"zh_CN": "说明", "en": "Help"},
}

register_strings(STRINGS)
