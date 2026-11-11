# -*- coding: utf-8 -*-
"""Interface string localisation.

Design
------
* All interface text lives in STRINGS, split into one table per language over a
  single shared key namespace.
* A missing translation falls back to the key itself instead of raising.
* The language preference is stored in ~/.alpsbox/prefs.json and applies on the
  next start.
* Switching language needs no process restart: the interface is rebuilt.

Usage
-----
    from .i18n import t
    tk.Label(parent, text=t("proc.start"))
"""
from __future__ import annotations

import json
import os
from typing import Optional

from . import citations as _C

# Supported languages: register a new language here, then add its text to every
# STRINGS entry. The default is English (global audience); Chinese users select
# it on the welcome page or get it from system-language detection.
LANGS = {"en": "English", "zh_CN": "简体中文"}
DEFAULT_LANG = "en"

# Formal citations appended to the end of GUI advanced-parameter and source
# notes: one reference per paragraph (blank-line separated), never crammed onto
# a single line.
_REF_CITATION_ZH = _C.gui_tip_block("zh_CN")
_REF_CITATION_EN = _C.gui_tip_block("en")

PREFS_DIR = os.path.join(os.path.expanduser("~"), ".alpsbox")
PREFS_FILE = os.path.join(PREFS_DIR, "prefs.json")

_current: str = DEFAULT_LANG


# =====================================================================
# Interface strings
# =====================================================================
# Layout: key = area.purpose
STRINGS = {
    # ---------------- Common ----------------
    "ok": {"zh_CN": "确定", "en": "OK"},
    "cancel": {"zh_CN": "取消", "en": "Cancel"},
    "close": {"zh_CN": "关闭", "en": "Close"},
    "save": {"zh_CN": "保存", "en": "Save"},
    "browse": {"zh_CN": "浏览", "en": "Browse"},
    "clear": {"zh_CN": "清空", "en": "Clear"},
    "export": {"zh_CN": "导出", "en": "Export"},
    "import": {"zh_CN": "导入", "en": "Import"},
    "refresh": {"zh_CN": "重新检测", "en": "Re-check"},
    "apply": {"zh_CN": "应用", "en": "Apply"},
    "reset": {"zh_CN": "恢复默认", "en": "Reset"},
    "none": {"zh_CN": "无", "en": "none"},
    "on": {"zh_CN": "开", "en": "on"},
    "off": {"zh_CN": "关", "en": "off"},
    "ready": {"zh_CN": "就绪", "en": "Ready"},
    "language": {"zh_CN": "语言", "en": "Language"},

    # ---------------- Window ----------------
    "app.title": {"zh_CN": "ALPSbox", "en": "ALPSbox"},
    "app.subtitle": {"zh_CN": "DTI-ALPS 自动化处理工具箱",
                     "en": "Automated DTI-ALPS processing toolbox"},

    # ---------------- Environment badge ----------------
    "env.checking": {"zh_CN": "检测中", "en": "Checking"},
    "env.ok": {"zh_CN": "环境正常", "en": "Environment OK"},
    "env.bad": {"zh_CN": "环境不满足", "en": "Environment incomplete"},
    "env.fail": {"zh_CN": "检测失败", "en": "Check failed"},
    "env.detail": {"zh_CN": "环境详情", "en": "Environment"},

    # ---------------- Navigation ----------------
    "nav.home": {"zh_CN": "首页", "en": "Home"},
    "nav.process": {"zh_CN": "处理", "en": "Process"},
    "nav.roi": {"zh_CN": "ROI 图解", "en": "ROI map"},
    "nav.results": {"zh_CN": "结果", "en": "Results"},
    "nav.qc": {"zh_CN": "质控", "en": "QC"},
    "nav.log": {"zh_CN": "日志", "en": "Log"},
    "nav.help": {"zh_CN": "帮助", "en": "Help"},

    # ---------------- Home page (welcome / language choice) ----------------
    "home.tagline": {
        "zh_CN": "一键算出每个被试的 DTI-ALPS 指数与质控",
        "en": "One-click DTI-ALPS values and quality control for every subject"},
    "home.subtitle": {
        "zh_CN": "选一个文件夹，点开始，拿到 ALPS + 质控 + 报告。",
        "en": "Pick a folder, press start, and get ALPS values, QC and a "
              "report."},
    "home.language": {"zh_CN": "选择语言", "en": "Choose your language"},
    "home.language_hint": {
        "zh_CN": "随时可以在右上角切换。",
        "en": "You can switch at any time from the top-right corner."},
    "home.get_started": {"zh_CN": "开始使用", "en": "Get started"},
    "home.step1_title": {"zh_CN": "选数据", "en": "Pick your data"},
    "home.step1_desc": {
        "zh_CN": "单个被试选文件夹；整个队列选根目录（每个子文件夹 = 一个被试）。",
        "en": "Choose one subject folder, or a cohort root where each "
              "subfolder is one subject."},
    "home.step2_title": {"zh_CN": "选输出目录", "en": "Choose output folder"},
    "home.step2_desc": {
        "zh_CN": "每个被试一个子目录，已完成的会自动跳过，可中断续跑。",
        "en": "One subfolder per subject; finished subjects are skipped, so "
              "runs can resume."},
    "home.step3_title": {"zh_CN": "点开始", "en": "Press start"},
    "home.step3_desc": {
        "zh_CN": "全自动处理并给出 ALPS、8 类质控指标与可打印的 HTML 报告。",
        "en": "Everything runs automatically and produces ALPS values, "
              "QC across 8 categories and a printable HTML report."},
    "home.privacy_title": {"zh_CN": "数据只在本机处理", "en": "Data stays on your machine"},
    "home.privacy": {
        "zh_CN": "不需要上传、不联网；FSL / MRtrix3 需自行安装（本工具不打包）。",
        "en": "No upload, no network access. FSL / MRtrix3 must be installed "
              "separately (they are not bundled)."},
    "home.not_title": {"zh_CN": "本工具不做什么", "en": "What this tool does not do"},
    "home.not_body": {
        "zh_CN": "不做组间统计或前后测分析（请用导出的 CSV/JSON 在下游软件完成）；"
                 "不做临床诊断；不声称是官方或标准实现。",
        "en": "It does not run group statistics or pre/post analyses (use the "
              "exported CSV/JSON downstream), does not provide clinical "
              "diagnosis, and does not claim to be an official or standard "
              "implementation."},

    # ---------------- Process page ----------------
    "proc.input": {"zh_CN": "输入", "en": "Input"},
    "proc.single": {"zh_CN": "单个被试", "en": "Single subject"},
    "proc.batch": {"zh_CN": "批量（每个子文件夹一个被试）",
                   "en": "Batch (one subject per subfolder)"},
    "proc.indir": {"zh_CN": "被试目录", "en": "Subject folder"},
    "proc.rootdir": {"zh_CN": "队列根目录", "en": "Cohort root"},
    "proc.outdir": {"zh_CN": "输出目录", "en": "Output folder"},
    "proc.hint": {
        "zh_CN": "建议先点下面的“先检查输入”，它只做文件匹配，不跑图像处理，"
                 "几秒钟就能看出每个被试能不能找到 DWI。",
        "en": "Tip: click “Check inputs” first. It only matches files, "
              "runs no image processing, and takes seconds."},
    "proc.params": {"zh_CN": "参数", "en": "Parameters"},
    "proc.threads": {"zh_CN": "线程数", "en": "Threads"},
    "proc.unring": {"zh_CN": "去 Gibbs 振铃", "en": "Gibbs unringing"},
    "proc.pipeline": {"zh_CN": "处理流程", "en": "Pipeline"},
    "proc.regqc": {"zh_CN": "配准稳健性质控", "en": "Registration robustness QC"},
    "proc.force": {"zh_CN": "强制重跑", "en": "Force re-run"},
    "proc.workers": {"zh_CN": "并行被试数", "en": "Parallel subjects"},
    "proc.workers_hint": {"zh_CN": "建议 1 到 2，受显存限制",
                          "en": "1–2 recommended (limited by GPU memory)"},
    "proc.advanced": {"zh_CN": "高级", "en": "Advanced"},
    "proc.advanced_hint": {
        "zh_CN": "默认值即推荐值。改动会改变结果口径，跨研究比较时须一并报告。",
        "en": "Defaults are recommended. Changing these alters the result "
              "definition and must be reported for cross-study comparison."},
    "proc.adv_reset": {"zh_CN": "恢复推荐值", "en": "Restore recommended"},
    "proc.adv_current": {"zh_CN": "当前生效：%s", "en": "Active: %s"},
    "proc.adv_recommended": {"zh_CN": "（推荐）", "en": " (recommended)"},
    "proc.adv_nondefault": {"zh_CN": "（非默认口径）",
                            "en": " (non-default definition)"},
    "proc.bet_f": {"zh_CN": "脑提取阈值 bet -f", "en": "Brain extraction bet -f"},
    "proc.reg_cost": {"zh_CN": "配准代价函数", "en": "Registration cost"},
    "proc.template": {"zh_CN": "配准模板", "en": "Template"},
    "proc.template_default": {"zh_CN": "默认（JHU-ICBM-FA-1mm）",
                              "en": "default (JHU-ICBM-FA-1mm)"},
    "proc.denoise": {"zh_CN": "dwidenoise 去噪", "en": "dwidenoise"},
    "tip.bet_f": {
        "zh_CN": "bet 的脑提取阈值 -f。\n\n0.5 = FSL 默认值，也是参考实现"
                 "（gbarisano/alps 的 alps.sh，MIT License）的默认值（推荐）；"
                 "0.3 是另一种常用设定，对应更大的脑掩膜。\n\n"
                 "脑掩膜会影响后续 eddy 与配准，因此不同 bet_f 得到的 ALPS "
                 "属于不同处理口径，不应直接互相比较；跨研究比较时请固定并"
                 "报告该参数。\n\n"
                 "改动后结果表会把它标记为非默认口径。"
                 + _REF_CITATION_ZH,
        "en": "bet brain-extraction -f.\n\n0.5 = FSL default and the default of "
              "the reference implementation (gbarisano/alps alps.sh, MIT "
              "License; recommended); 0.3 is another common setting that yields "
              "a larger brain mask.\n\nThe mask affects the subsequent eddy "
              "correction and registration, so results obtained with different "
              "bet_f values are different processing definitions and should not "
              "be compared directly; fix and report this parameter when "
              "comparing studies.\n\nThe results table marks changed values "
              "as a non-default definition." + _REF_CITATION_EN},
    "tip.reg_cost": {
        "zh_CN": "FA→模板的 flirt 代价函数。\n\nnormmi = 本工具默认；"
                 "corratio = flirt 默认，也是参考实现"
                 "（gbarisano/alps 的 alps.sh，MIT License）的设定。\n\n"
                 "代价函数会改变配准结果，进而改变 ALPS，属于处理口径的一部分；"
                 "换用后不要与默认口径的数值直接比较。与参考实现逐例比对时，"
                 "选 corratio 更接近其口径。" + _REF_CITATION_ZH,
        "en": "flirt cost function for FA→template.\n\nnormmi = this tool's "
              "default; corratio = flirt default and the reference "
              "implementation's setting (gbarisano/alps alps.sh, MIT License)."
              "\n\nThe cost function changes the registration and therefore "
              "ALPS; it is part of the processing definition, so do not compare "
              "values obtained with different costs directly. Choose corratio "
              "when matching the reference alps.sh runs subject by subject."
              + _REF_CITATION_EN},
    "tip.template": {
        "zh_CN": "配准目标模板。留空 = FSL 自带的 JHU-ICBM-FA-1mm。\n\n"
                 "随包 ROI 与默认流程都定义在该模板的 1 毫米空间；换模板后 "
                 "ROI、配准与 ALPS 数值都不再与默认口径可比，除非把 ROI 与"
                 "全部流程按新模板重做并重新验证。" + _REF_CITATION_ZH,
        "en": "Registration target. Empty = FSL's JHU-ICBM-FA-1mm.\n\n"
              "The bundled ROIs and the default pipeline are defined in this "
              "template's 1 mm space. With another template the ROIs, "
              "registration and ALPS values are no longer comparable to the "
              "default definition unless the ROIs and the whole pipeline are "
              "redone and revalidated in the new space." + _REF_CITATION_EN},
    "tip.denoise": {
        "zh_CN": "MRtrix3 的 dwidenoise 去噪（默认关，在去振铃之前执行）。\n\n"
                 "MRtrix3 文档要求去噪在去振铃之前，否则噪声估计会失效。"
                 "开启后属于另一种处理口径：对 ALPS 的定量影响取决于数据，"
                 "不应与默认口径的数值混比；跨研究比较时请明确报告是否去噪。"
                 + _REF_CITATION_ZH,
        "en": "MRtrix3 dwidenoise (off by default; runs before unringing)."
              "\n\nMRtrix3 documentation requires denoising before Gibbs "
              "unringing, otherwise the noise estimate is invalid. Enabling it "
              "defines a different processing definition: its effect on ALPS is "
              "data-dependent, so do not mix it with default-setting results; "
              "report whether denoising was applied when comparing studies."
              + _REF_CITATION_EN},
    "proc.browse": {"zh_CN": "浏览", "en": "Browse"},
    "proc.roi_src": {"zh_CN": "ROI 来源", "en": "ROI source"},
    "proc.roi_bundled": {
        "zh_CN": "随包参考 ROI（gbarisano/alps，MIT License）",
        "en": "Bundled reference ROIs (gbarisano/alps, MIT License)"},
    "proc.roi_sphere": {"zh_CN": "自建球 半径", "en": "Sphere, radius"},
    "proc.roi_mm": {"zh_CN": "毫米", "en": "mm"},
    "proc.roi_custom": {"zh_CN": "自定义 4 个 NIfTI", "en": "Custom 4 NIfTI"},
    "proc.choose": {"zh_CN": "选择", "en": "Choose"},
    "proc.start": {"zh_CN": "开始处理", "en": "Start"},
    "proc.stop": {"zh_CN": "停止", "en": "Stop"},
    "proc.preflight": {"zh_CN": "先检查输入", "en": "Check inputs"},
    "proc.clearlog": {"zh_CN": "清空日志", "en": "Clear log"},
    "proc.summary": {"zh_CN": "本次任务摘要", "en": "Task summary"},
    "proc.summary_empty": {
        "zh_CN": "尚未选择输入目录。单个被试就选那个被试的文件夹；"
                 "批量就选队列根目录，程序会把每个子文件夹当成一个被试。",
        "en": "No input folder selected. For a single subject pick its folder; "
              "for batch pick the cohort root; each subfolder becomes one subject."},
    "proc.mode": {"zh_CN": "模式", "en": "Mode"},
    "proc.found": {"zh_CN": "发现 %d 个子文件夹，将作为 %d 个被试处理%s",
                   "en": "%d subfolders found, treated as %d subjects%s"},
    "proc.est": {"zh_CN": "，按每人 10 到 15 分钟估算，全批约需 %.0f 到 %.0f 分钟",
                 "en": " (est. %.0f–%.0f min at 10–15 min/subject)"},
    "proc.out_to": {"zh_CN": "输出到", "en": "Output to"},
    "proc.next_hint": {"zh_CN": "接下来建议先点“先检查输入”确认都能找到 DWI。",
                       "en": "Next: click “Check inputs” to confirm every DWI is found."},
    "proc.subject_id": {"zh_CN": "被试编号取目录名", "en": "Subject ID from folder name"},
    "proc.est_time": {"zh_CN": "预计耗时 9 到 15 分钟，其中 eddy 占八成左右。",
                      "en": "Estimated 9–15 min, about 80% of it in eddy."},
    "proc.dir_missing": {"zh_CN": "目录不存在", "en": "Folder not found"},
    "proc.not_set": {"zh_CN": "（未设置）", "en": "(not set)"},

    # ---------------- Results page ----------------
    "res.title": {"zh_CN": "结果表", "en": "Results"},
    "res.count": {"zh_CN": "共 %d 条", "en": "%d rows"},
    "res.clear": {"zh_CN": "清空结果", "en": "Clear"},
    "res.import": {"zh_CN": "导入结果", "en": "Import"},
    "res.export_json": {"zh_CN": "导出 JSON", "en": "Export JSON"},
    "res.report": {"zh_CN": "生成报告", "en": "Report"},
    "msg.report_done": {
        "zh_CN": "已生成 HTML 报告：%s\n（共 %d 个被试，浏览器打开后可打印为 PDF）",
        "en": "HTML report written: %s\n(%d subjects; open in a browser to print as PDF)"},
    "res.export_csv": {"zh_CN": "导出 CSV", "en": "Export CSV"},

    # ---------------- Results table column names ----------------
    "col.subject": {"zh_CN": "被试", "en": "Subject"},    "col.status": {"zh_CN": "状态", "en": "Status"},
    "col.qc": {"zh_CN": "质控", "en": "QC"},
    "col.r_wm": {"zh_CN": "配准 r_wm", "en": "r_wm"},
    "col.roi": {"zh_CN": "ROI 体素", "en": "ROI voxels"},
    "col.rel": {"zh_CN": "抖动 mm", "en": "Jitter mm"},
    "col.abs": {"zh_CN": "漂移 mm", "en": "Drift mm"},
    "col.outlier": {"zh_CN": "离群切片", "en": "Outliers"},
    "col.method": {"zh_CN": "校正方法", "en": "Correction"},
    "col.issues": {"zh_CN": "主要问题", "en": "Issues"},
    "col.alps_L": {"zh_CN": "ALPS_L", "en": "ALPS_L"},
    "col.alps_R": {"zh_CN": "ALPS_R", "en": "ALPS_R"},
    "col.alps_mean": {"zh_CN": "ALPS_mean", "en": "ALPS_mean"},
    "col.n_vol": {"zh_CN": "体积数", "en": "Volumes"},
    "col.seconds": {"zh_CN": "耗时(s)", "en": "Time (s)"},
    "col.finished": {"zh_CN": "完成时间", "en": "Finished"},

    # ---------------- QC page ----------------
    "qc.title": {"zh_CN": "质控", "en": "Quality control"},
    "qc.overview": {"zh_CN": "质控总览", "en": "Overview"},
    "qc.total": {"zh_CN": "被试总数", "en": "Subjects"},
    "qc.pass": {"zh_CN": "通过", "en": "Pass"},
    "qc.info": {"zh_CN": "提示", "en": "Info"},
    "qc.warn": {"zh_CN": "需注意", "en": "Check"},
    "qc.fail": {"zh_CN": "不合格", "en": "Fail"},
    "qc.filter_all": {"zh_CN": "全部", "en": "All"},
    "qc.detail": {"zh_CN": "质控明细", "en": "Details"},
    "qc.recheck": {"zh_CN": "重新评估", "en": "Re-evaluate"},
    "qc.thresholds": {"zh_CN": "阈值设置", "en": "Thresholds"},
    "qc.scatter": {"zh_CN": "跨被试散点", "en": "Scatter"},
    "qc.export": {"zh_CN": "导出质控报告", "en": "Export report"},
    "qc.thresholds_now": {"zh_CN": "当前判定阈值：", "en": "Current thresholds: "},
    "qc.dblclick_hint": {
        "zh_CN": "双击某一行查看该被试的完整质控报告；也可选中后按回车。",
        "en": "Double-click a row for the full QC report, or select and press Enter."},
    "qc.no_data": {"zh_CN": "还没有结果，先到「处理」页跑一个被试。",
                   "en": "No results yet. Run a subject on the Process page first."},
    "qc.summary": {"zh_CN": "共 %d 个被试", "en": "%d subjects"},
    "qc.summary_warn": {"zh_CN": "%d 个需注意", "en": "%d to check"},
    "qc.summary_fail": {"zh_CN": "%d 个不合格", "en": "%d failed"},
    "qc.top_issue": {"zh_CN": "最常见", "en": "Most common"},
    "qc.all_pass": {"zh_CN": "全部通过，没有需要关注的问题。",
                    "en": "All passed, nothing to flag."},

    # ---------------- QC detail window ----------------
    "qcd.title": {"zh_CN": "质控报告", "en": "QC report"},
    "qcd.sash_hint": {"zh_CN": "← 拖动中间的分隔条可以调整两侧宽度 →",
                      "en": "← Drag the divider to resize panes →"},
    "qcd.save_png": {"zh_CN": "保存图片", "en": "Save image"},
    "qcd.copy_text": {"zh_CN": "复制文字报告", "en": "Copy report"},
    "qcd.no_dir": {
        "zh_CN": "找不到该被试的输出目录，无法读取 eddy 头动原始文件。\n"
                 "曲线需要读 eddy_out.eddy_movement_rms，"
                 "用「导入结果」导入汇总表时会记住它所在的目录。",
        "en": "Cannot locate this subject's output folder, so the eddy motion "
              "file is unavailable. Importing a summary table records its folder "
              "for this lookup."},
    "qcd.caption": {
        "zh_CN": "上：绝对位移（相对第 1 卷）　下：相对位移（相对前卷）；"
                 "红带标出被判为离群的体积",
        "en": "Top: drift from volume 1. Bottom: frame-to-frame motion. "
              "Red bands mark outlier volumes."},

    # ---------------- Plot toolbar ----------------
    "fig.fit": {"zh_CN": "适应窗口", "en": "Fit"},
    "fig.zoom_in": {"zh_CN": "放大", "en": "Zoom in"},
    "fig.zoom_out": {"zh_CN": "缩小", "en": "Zoom out"},
    "fig.hint": {"zh_CN": "滚轮缩放 · 拖动平移", "en": "Wheel to zoom · drag to pan"},
    "fig.fail": {"zh_CN": "绘图失败", "en": "Plot failed"},
    "fig.no_image": {"zh_CN": "图还没渲染出来。", "en": "The figure is not ready yet."},
    "fig.save_title": {"zh_CN": "保存图片", "en": "Save image"},

    # ---------------- Scatter window ----------------
    "sc.title": {"zh_CN": "跨被试散点", "en": "Cross-subject scatter"},
    "sc.x": {"zh_CN": "X", "en": "X"},
    "sc.y": {"zh_CN": "Y", "en": "Y"},
    "sc.group": {"zh_CN": "分组", "en": "Group"},
    "sc.group_auto": {"zh_CN": "按 ID 前缀", "en": "ID prefix"},
    "sc.group_column": {"zh_CN": "用 group 列", "en": "group column"},
    "sc.group_none": {"zh_CN": "不分组", "en": "No grouping"},
    "sc.hint": {
        "zh_CN": "分组口径由你定：按 ID 前缀（取第一个下划线、横线或点之前的部分）、"
                 "用数据里的 group 列，或不分组。工具本身不预设任何队列结构。",
        "en": "Grouping is up to you: by ID prefix (text before the first "
              "underscore, hyphen or dot), by a group column, or none. "
              "The tool assumes no particular cohort structure."},
    "sc.no_points": {"zh_CN": "这两个变量没有可用的数据点",
                     "en": "No data points for this variable pair"},

    # ---------------- Plot variable names ----------------
    "var.alps_mean": {"zh_CN": "ALPS 均值", "en": "ALPS mean"},
    "var.alps_L": {"zh_CN": "ALPS 左", "en": "ALPS left"},
    "var.alps_R": {"zh_CN": "ALPS 右", "en": "ALPS right"},
    "var.r_wm": {"zh_CN": "配准相关系数", "en": "Registration r_wm"},
    "var.rms_abs_mean": {"zh_CN": "漂移均值 (mm)", "en": "Drift mean (mm)"},
    "var.rms_abs_max": {"zh_CN": "漂移最大 (mm)", "en": "Drift max (mm)"},
    "var.rms_rel_mean": {"zh_CN": "抖动均值 (mm)", "en": "Jitter mean (mm)"},
    "var.rms_rel_max": {"zh_CN": "抖动最大 (mm)", "en": "Jitter max (mm)"},
    "var.n_outlier": {"zh_CN": "离群切片数", "en": "Outlier slices"},
    "var.n_vol": {"zh_CN": "体积数", "en": "Volumes"},
    "var.seconds": {"zh_CN": "处理耗时 (s)", "en": "Processing time (s)"},

    # ---------------- Log page ----------------
    "log.title": {"zh_CN": "处理日志", "en": "Log"},
    "log.save_as": {"zh_CN": "另存为", "en": "Save as"},
    "log.saved": {"zh_CN": "已保存", "en": "Saved"},

    # ---------------- Progress bar ----------------
    "prog.elapsed": {"zh_CN": "已用", "en": "Elapsed"},
    "prog.total_time": {"zh_CN": "总用时", "en": "Total"},
    "prog.current": {"zh_CN": "当前被试", "en": "Current"},
    "prog.session": {"zh_CN": "会话结果 %d 条", "en": "%d results in session"},
    "prog.session_empty": {"zh_CN": "会话结果 0 条", "en": "No results yet"},
    "prog.autosave": {"zh_CN": "自动保存，关掉再开还在",
                      "en": "auto-saved, persists after restart"},
    "prog.done": {"zh_CN": "完成 %d/%d  用时 %s", "en": "Done %d/%d in %s"},

    # ---------------- Queue messages ----------------
    "msg.start": {"zh_CN": "开始处理", "en": "Starting"},
    "msg.mode_batch": {"zh_CN": "批量", "en": "batch"},
    "msg.mode_single": {"zh_CN": "单被试", "en": "single subject"},
    "msg.input": {"zh_CN": "输入", "en": "Input"},
    "msg.output": {"zh_CN": "输出", "en": "Output"},
    "msg.done_ok": {"zh_CN": "处理结束：成功 %d / %d，总用时 %s",
                    "en": "Finished: %d/%d succeeded in %s"},
    "msg.done_none": {"zh_CN": "处理结束，没有新任务，总用时 %s",
                      "en": "Finished, no new tasks, %s elapsed"},
    "msg.result_dir": {"zh_CN": "结果目录", "en": "Results folder"},
    "msg.stop_req": {"zh_CN": "已请求停止，等当前被试结束后停下。",
                     "en": "Stop requested; will halt after the current subject."},
    "msg.stopped": {"zh_CN": "已停止，在 %d/%d 处中断。",
                    "en": "Stopped at %d/%d."},
    "msg.confirm_stop": {
        "zh_CN": "确定停止？\n\n当前被试会跑完再停，不会留下半截文件。\n"
                 "已完成的被试结果都保存着。",
        "en": "Stop now?\n\nThe current subject will finish first, so no "
              "half-written files are left. Completed results are kept."},
    "msg.confirm_close": {
        "zh_CN": "还有被试在跑。现在关闭会中断当前这个。\n"
                 "已完成的结果都已经保存。\n\n确定退出？",
        "en": "Subjects are still running. Closing now interrupts the current "
              "one. Completed results are already saved.\n\nQuit anyway?"},
    "qc.th_line": {
        "zh_CN": "r_wm ≥ %.2f　相对位移 < %.2f/%.2f mm　"
                 "绝对位移 < %.2f/%.2f mm　ROI = %d 体素",
        "en": "r_wm ≥ %.2f, jitter < %.2f/%.2f mm, "
              "drift < %.2f/%.2f mm, ROI = %d voxels"},
    "qc.th_line_noroi": {
        "zh_CN": "r_wm ≥ %.2f　相对位移 < %.2f/%.2f mm　"
                 "绝对位移 < %.2f/%.2f mm　ROI 体素不限",
        "en": "r_wm ≥ %.2f, jitter < %.2f/%.2f mm, "
              "drift < %.2f/%.2f mm, ROI voxels unrestricted"},
    "msg.starting_gui": {"zh_CN": "启动中，请稍候…", "en": "Starting, please wait…"},

    "prog.current_fmt": {"zh_CN": "当前被试：%s  %s", "en": "Current: %s  %s"},
    "prog.current_none": {"zh_CN": "当前被试：无", "en": "Current: none"},
    "roi.axial": {"zh_CN": "轴位", "en": "Axial"},
    "roi.coronal": {"zh_CN": "冠状位", "en": "Coronal"},
    "roi.layer": {"zh_CN": "层", "en": "slice"},
    "roi.L_proj": {"zh_CN": "左侧投射纤维区", "en": "L projection fiber area"},
    "roi.R_proj": {"zh_CN": "右侧投射纤维区", "en": "R projection fiber area"},
    "roi.L_asso": {"zh_CN": "左侧联络纤维区（上纵束）", "en": "L association fiber area (SLF)"},
    "roi.R_asso": {"zh_CN": "右侧联络纤维区（上纵束）", "en": "R association fiber area (SLF)"},
    "roi.fiber_proj": {"zh_CN": "投射纤维，走行上下", "en": "Projection fibers, head-foot"},
    "roi.fiber_asso": {"zh_CN": "联络纤维，走行前后", "en": "Association fibers, anterior-posterior"},
    "roi.hover_hint": {
        "zh_CN": "鼠标移到色块上可高亮；左键选中看详情；滚轮缩放；中键拖动平移。"
                 "图像按放射学惯例显示（图像左侧为右脑）。",
        "en": "Hover a patch to highlight; click to select; scroll to zoom; "
              "middle-drag to pan. Radiological convention: left of image is right brain."},
    "roip.title": {"zh_CN": "这四个 ROI 是什么", "en": "What these four ROIs are"},
    "roip.why": {"zh_CN": "为什么要测这个位置", "en": "Why this location"},
    "roip.why_body": {
        "zh_CN": "侧脑室体部层面，投射纤维与联络纤维正好互相垂直。投射纤维是上放射冠，"
                 "走行上下；联络纤维是上纵束，走行前后。血管周围间隙沿脑中动静脉走，"
                 "在这里垂直于这两束纤维，也就是左右方向。",
        "en": "At the level of the lateral ventricle body the projection and "
              "association fibers are perpendicular to each other. Projection fibers "
              "(superior corona radiata) run superior-inferior; association fibers "
              "(superior longitudinal fasciculus) run anterior-posterior. Perivascular "
              "spaces follow the cerebral vessels and here run left-right."},
    "roip.idx": {"zh_CN": "指数怎么来", "en": "How the index is built"},
    "roip.idx_body": {
        "zh_CN": "取左右方向的扩散率，除以垂直方向的扩散率。比值越大，说明沿血管周围间隙的"
                 "扩散越通畅。分母起归一化作用，扣掉个体整体扩散水平的差异。",
        "en": "Diffusivity along left-right divided by diffusivity perpendicular to it. "
              "A larger ratio means freer diffusion along the perivascular space. The "
              "denominator normalises out each subject's overall diffusivity level."},
    "roip.masks": {"zh_CN": "四个掩膜", "en": "The four masks"},
    "roip.col_name": {"zh_CN": "名称", "en": "Name"},
    "roip.col_anat": {"zh_CN": "解剖", "en": "Anatomy"},
    "roip.col_type": {"zh_CN": "类型", "en": "Type"},
    "roip.col_vox": {"zh_CN": "体素", "en": "Voxels"},
    "roip.fiber_proj": {"zh_CN": "投射纤维", "en": "Projection"},
    "roip.fiber_asso": {"zh_CN": "联络纤维", "en": "Association"},
    "roip.note": {
        "zh_CN": "掩膜来自 gbarisano/alps 公开仓库，MIT 许可，在 JHU-ICBM-FA-1mm 模板上"
                 "画成 2.5 毫米半径球。背景图在运行时从本机 FSL 读取，未随本工具分发。",
        "en": "Masks come from the public gbarisano/alps repository (MIT licence), drawn "
              "as 2.5 mm radius spheres on the JHU-ICBM-FA-1mm template. The background "
              "image is read from the local FSL install at run time and is not bundled."},
    "roi.no_template": {"zh_CN": "未找到 JHU-ICBM-FA-1mm 模板，仅显示 ROI 轮廓",
                        "en": "JHU-ICBM-FA-1mm template not found; ROI outlines only"},

    # ================= Second batch (added for gui.py) ================= 
    "col.drift_max": {"zh_CN": "漂移最大", "en": "Drift max"},
    "col.drift_mean": {"zh_CN": "漂移均值", "en": "Drift mean"},
    "col.jitter_max": {"zh_CN": "抖动最大", "en": "Jitter max"},
    "col.jitter_mean": {"zh_CN": "抖动均值", "en": "Jitter mean"},
    "col.level": {"zh_CN": "判定", "en": "Level"},
    "col.outlier_short": {"zh_CN": "离群", "en": "Outliers"},
    "env.check_err": {"zh_CN": "环境检测出错：%s", "en": "Environment check failed: %s"},
    "env.copied_body": {"zh_CN": "环境诊断信息已复制到剪贴板。",
                  "en": "Diagnostics copied to the clipboard."},
    "env.copy": {"zh_CN": "复制诊断信息", "en": "Copy diagnostics"},
    "env.fix_body": {
        "zh_CN": "缺 FSL：\n"
                 "    wget https://fsl.fmrib.ox.ac.uk/fsldownloads/fslinstaller.py\n"
                 "    python3 fslinstaller.py\n"
                 "然后写进 ~/.bashrc：\n"
                 "    export FSLDIR=$HOME/fsl\n"
                 "    . ${FSLDIR}/etc/fslconf/fsl.sh\n"
                 "    export PATH=${FSLDIR}/bin:$PATH\n"
                 "\n"
                 "FSL 在但缺命令：先看 fsl-config --version 是否 6.0.3 以上，\n"
                 "必要时执行 $FSLDIR/bin/fsl_install_atlases 补图谱。\n"
                 "\n"
                 "缺 MRtrix3（只影响去振铃，不致命）：\n"
                 "    conda install -c conda-forge -c bioconda mrtrix3\n"
                 "\n"
                 "缺 dcm2niix（只影响 DICOM 输入）：\n"
                 "    conda install -c conda-forge dcm2niix",
        "en": "FSL missing:\n"
              "    wget https://fsl.fmrib.ox.ac.uk/fsldownloads/fslinstaller.py\n"
              "    python3 fslinstaller.py\n"
              "Then add to ~/.bashrc:\n"
              "    export FSLDIR=$HOME/fsl\n"
              "    . ${FSLDIR}/etc/fslconf/fsl.sh\n"
              "    export PATH=${FSLDIR}/bin:$PATH\n"
              "\n"
              "FSL present but a command is missing: check that fsl-config --version reports 6.0.3 or newer and run $FSLDIR/bin/fsl_install_atlases if needed.\n"
              "\n"
              "MRtrix3 missing (only affects unringing, not fatal):\n"
              "    conda install -c conda-forge -c bioconda mrtrix3\n"
              "\n"
              "dcm2niix missing (only affects DICOM input):\n"
              "    conda install -c conda-forge dcm2niix"},
    "env.fix_title": {"zh_CN": "怎么修", "en": "How to fix"},
    "env.not_ok_body": {
        "zh_CN": "FSL 环境检测没通过，无法开始。\n"
                 "\n"
                 "点右上角的环境详情可以看到缺什么，\n"
                 "或者到帮助页的安装与依赖一节看安装步骤。",
        "en": "The FSL environment check did not pass, so processing cannot start.\n"
              "\n"
              "Open Environment (top right) to see what is missing, or read the Installation section on the Help page."},
    "env.not_ready": {"zh_CN": "尚未完成检测，请稍等或点重新检测。",
                  "en": "The check has not finished yet; wait a moment or click Re-check."},
    "fig.save_qc_title": {"zh_CN": "保存质控图", "en": "Save QC figure"},
    "ft.all": {"zh_CN": "所有文件", "en": "All files"},
    "ft.table_json": {"zh_CN": "表格或 JSON", "en": "Table or JSON"},
    "ft.text": {"zh_CN": "文本文件", "en": "Text files"},
    "log.all_done": {"zh_CN": "全部已完成，没有新任务。", "en": "All done, no new tasks."},
    "log.batch_total": {"zh_CN": "本批可处理 %d 个被试。",
                  "en": "%d subjects to process in this batch."},
    "log.discover_fail": {"zh_CN": "[错误] 输入发现失败：%s",
                  "en": "[error] input discovery failed: %s"},
    "log.import_results": {"zh_CN": "导入结果：%s", "en": "Imported results: %s"},
    "log.internal_error": {
        "zh_CN": "内部异常：\n"
                 "",
        "en": "Internal error:\n"
              ""},
    "log.job_count": {"zh_CN": "共 %d 个子文件夹。", "en": "%d subfolders."},
    "log.lang_switched": {"zh_CN": "界面语言已切换为 %s。", "en": "Interface language: %s."},
    "log.missing_one": {"zh_CN": "[缺失] %s", "en": "[missing] %s"},
    "log.no": {"zh_CN": "无", "en": "no"},
    "log.no_subdirs": {"zh_CN": "[错误] 目录下没有子文件夹",
                  "en": "[error] no subfolders in this folder"},
    "log.preflight": {"zh_CN": "输入预检（不跑处理）  %s",
                  "en": "Input preflight (no processing)  %s"},
    "log.preflight_sum": {"zh_CN": "结论：可跑 %d 个，不可跑 %d 个。",
                  "en": "Result: %d runnable, %d not runnable."},
    "log.restored": {"zh_CN": "已恢复上次会话的 %d 条结果。",
                  "en": "Restored %d results from the last session."},
    "log.results_cleared": {"zh_CN": "结果表已清空。", "en": "Results table cleared."},
    "log.runnable": {"zh_CN": "[可跑] %-20s json=%s  相位方向=%s",
                  "en": "[ready] %-20s json=%s  phase dir=%s"},
    "log.save_title": {"zh_CN": "保存日志", "en": "Save log"},
    "log.skipped_done": {"zh_CN": "已完成 %d 个，跳过。想重算就勾强制重跑。",
                  "en": "%d already done, skipped. Tick “Force re-run” to redo them."},
    "log.start": {"zh_CN": "开始处理  %s   模式 %s", "en": "Starting  %s   mode %s"},
    "log.started": {"zh_CN": "ALPSbox %s 已启动。", "en": "ALPSbox %s started."},
    "log.summary_fail": {"zh_CN": "[注意] 汇总写盘失败：%s",
                  "en": "[warn] writing the summary failed: %s"},
    "log.yes": {"zh_CN": "有", "en": "yes"},
    "msg.busy_title": {"zh_CN": "正在处理中", "en": "Processing"},
    "msg.confirm_clear": {
        "zh_CN": "确定清空当前结果表（%d 条）？\n"
                 "\n"
                 "只清屏，历史文件 ~/.alpsbox/history.jsonl 不受影响。\n"
                 "建议先导出 CSV 备份。",
        "en": "Clear the results table (%d rows)?\n"
              "\n"
              "This only clears the view; the history file ~/.alpsbox/history.jsonl is untouched.\n"
              "Export a CSV backup first if you are unsure."},
    "msg.copied": {"zh_CN": "已复制", "en": "Copied"},
    "msg.copied_body": {"zh_CN": "内容已复制到剪贴板。",
                  "en": "Content copied to the clipboard."},
    "msg.copy_fail": {"zh_CN": "复制失败", "en": "Copy failed"},
    "msg.export_fail": {"zh_CN": "导出失败", "en": "Export failed"},
    "msg.exported": {"zh_CN": "已导出", "en": "Exported"},
    "msg.import_done": {"zh_CN": "导入完成", "en": "Import finished"},
    "msg.import_done_body": {
        "zh_CN": "%s\n"
                 "合并后共 %d 条，原有 %d 条。",
        "en": "%s\n"
              "%d rows after merging, %d before."},
    "msg.import_fail": {"zh_CN": "导入失败", "en": "Import failed"},
    "msg.input_invalid": {"zh_CN": "输入无效", "en": "Invalid input"},
    "msg.input_invalid_body": {"zh_CN": "请先选一个存在的输入目录。",
                  "en": "Select an existing input folder first."},
    "msg.input_missing_body": {"zh_CN": "请选一个存在的输入目录。",
                  "en": "Select an existing input folder."},
    "msg.need_mpl": {"zh_CN": "需要 matplotlib：%s", "en": "matplotlib is required: %s"},
    "msg.no_data": {"zh_CN": "没有数据", "en": "No data"},
    "msg.no_image": {"zh_CN": "没有图片", "en": "No image"},
    "msg.output_invalid": {"zh_CN": "输出无效", "en": "Invalid output"},
    "msg.output_invalid_body": {"zh_CN": "请指定输出目录。", "en": "Specify an output folder."},
    "msg.plot_unavailable": {"zh_CN": "无法绘图", "en": "Cannot plot"},
    "msg.roi_invalid": {"zh_CN": "自定义 ROI 无效", "en": "Invalid custom ROI"},
    "msg.roi_invalid_body": {
        "zh_CN": "需要按顺序给 4 个 ROI：\n"
                 "左上放射冠、右上放射冠、左上纵束、右上纵束。",
        "en": "Four ROIs are required, in this order:\n"
              "L SCR, R SCR, L SLF, R SLF."},
    "msg.save_fail": {"zh_CN": "保存失败", "en": "Save failed"},
    "msg.stop_title": {"zh_CN": "停止处理", "en": "Stop processing"},
    "msg.table_empty": {"zh_CN": "结果表为空。", "en": "The results table is empty."},
    "proc.checking_input": {"zh_CN": "检查输入", "en": "Checking input"},
    "proc.completed": {"zh_CN": "完成", "en": "Done"},
    "proc.failed": {"zh_CN": "失败", "en": "Failed"},
    "proc.next_hint_single": {"zh_CN": "接下来建议先点“先检查输入”确认能找到 DWI。",
                  "en": "Next: click “Check inputs” to confirm the DWI is found."},
    "proc.pick_indir": {"zh_CN": "选择被试目录", "en": "Choose subject folder"},
    "proc.pick_out": {"zh_CN": "选择输出目录", "en": "Choose output folder"},
    "proc.pick_roi": {"zh_CN": "按顺序选 4 个 ROI：左上放射冠、右上放射冠、左上纵束、右上纵束",
                  "en": "Pick 4 ROIs in order: L SCR, R SCR, L SLF, R SLF"},
    "proc.pick_root": {"zh_CN": "选择队列根目录", "en": "Choose cohort root"},
    "proc.preparing": {"zh_CN": "准备中", "en": "Preparing"},
    "proc.read_fail": {"zh_CN": "读取目录失败", "en": "Cannot read folder"},
    "proc.starting": {"zh_CN": "开始处理 %s", "en": "Starting %s"},
    "prog.batch_line": {"zh_CN": "%d/%d  已用 %s  预计剩余 %s",
                  "en": "%d/%d  elapsed %s  remaining %s"},
    "qc.chk_flag_eddy": {"zh_CN": "把「用 eddy_correct」判为需注意",
                  "en": "Flag “eddy_correct” cases as check"},
    "qc.chk_strict_roi": {"zh_CN": "严格检查 ROI 体素数（用自建球改半径时可关闭）",
                  "en": "Strictly check ROI voxel count (turn off when resizing the sphere)"},
    "qc.confirm_reset": {"zh_CN": "把全部阈值恢复为默认值？",
                  "en": "Reset all thresholds to their defaults?"},
    "qc.count_paren": {"zh_CN": "（%d）", "en": " (%d)"},
    "qc.export_empty": {"zh_CN": "还没有可导出的质控结果。", "en": "No QC results to export yet."},
    "qc.per_subject": {"zh_CN": "逐个被试明细", "en": "Per-subject details"},
    "qc.row_lower": {"zh_CN": "下限", "en": "Lower"},
    "qc.row_max_fail": {"zh_CN": "最大不合格", "en": "Max fail"},
    "qc.row_max_warn": {"zh_CN": "最大警告", "en": "Max warn"},
    "qc.row_mean_fail": {"zh_CN": "均值不合格", "en": "Mean fail"},
    "qc.row_mean_warn": {"zh_CN": "均值警告", "en": "Mean warn"},
    "qc.row_roi_voxels": {"zh_CN": "ROI 期望体素数", "en": "Expected ROI voxels"},
    "qc.row_rwm_fail": {"zh_CN": "不合格上限", "en": "Fail ceiling"},
    "qc.row_rwm_ok": {"zh_CN": "通过下限", "en": "Pass floor"},
    "qc.row_upper": {"zh_CN": "上限", "en": "Upper"},
    "qc.row_warn": {"zh_CN": "警告", "en": "Warn"},
    "qc.save_fail_body": {"zh_CN": "无法写入 %s，请检查磁盘权限。",
                  "en": "Cannot write %s; check disk permissions."},
    "qc.save_recheck": {"zh_CN": "保存并重新评估", "en": "Save and re-evaluate"},
    "qc.saved_body": {
        "zh_CN": "阈值已保存到 %s\n"
                 "当前 %d 条结果已按新标准重新评估。",
        "en": "Thresholds saved to %s\n"
              "%d results re-evaluated with the new criteria."},
    "qc.sec_abs": {"zh_CN": "绝对位移（整体漂移，mm）", "en": "Absolute motion (drift, mm)"},
    "qc.sec_abs_hint": {"zh_CN": "相对第 1 个体积的位移。它会随扫描时长累积，序列越长数值越大，所以只作参考，阈值放得宽。",
                  "en": "Displacement relative to volume 1. It accumulates with scan length — longer series are naturally larger — so it is only a reference and the thresholds are loose."},
    "qc.sec_alps": {"zh_CN": "ALPS 合理区间", "en": "Plausible ALPS range"},
    "qc.sec_alps_hint": {"zh_CN": "超出这个范围通常意味着张量重定向或 ROI 空间出了问题。",
                  "en": "Values outside this range usually mean a tensor reorientation or ROI space problem."},
    "qc.sec_other": {"zh_CN": "其他", "en": "Other"},
    "qc.sec_out": {"zh_CN": "离群切片（条 / 每个体积）", "en": "Outlier slices (per volume)"},
    "qc.sec_out_hint": {"zh_CN": "eddy 的 repol 已自动替换这些切片，这里只反映数据质量。",
                  "en": "eddy's repol already replaced these slices; this only reflects data quality."},
    "qc.sec_reg": {"zh_CN": "配准质量（fslcc 相关系数）",
                  "en": "Registration quality (fslcc correlation)"},
    "qc.sec_reg_hint": {"zh_CN": "FA 配准到 JHU 模板后与模板的相关系数。同模板同空间时接近 1.000。",
                  "en": "Correlation between FA and the JHU template after registration. Same template and space gives values near 1.000."},
    "qc.sec_rel": {"zh_CN": "相对位移（逐卷抖动，mm）", "en": "Relative motion (frame-wise, mm)"},
    "qc.sec_rel_hint": {"zh_CN": "相对前一个体积的位移，类似 fMRI 的 frame-wise displacement。这个指标不随扫描时长累积，组间可比，是主要判据。",
                  "en": "Displacement relative to the previous volume, like fMRI frame-wise displacement. It does not accumulate with scan length, so it compares across groups; this is the primary criterion."},
    "qc.select_body": {"zh_CN": "先选中一行，再双击或按回车。",
                  "en": "Select a row first, then double-click or press Enter."},
    "qc.select_title": {"zh_CN": "选择被试", "en": "Select a subject"},
    "qc.th_bad_title": {"zh_CN": "阈值不合逻辑", "en": "Inconsistent thresholds"},
    "qc.th_hint": {"zh_CN": "改完点「保存并重新评估」，结果表里所有被试都会按新标准重判。配置存在 ~/.alpsbox/qc_config.json，下次打开仍然生效。",
                  "en": "Click “Save and re-evaluate” when done: every subject is re-judged with the new criteria. Settings live in ~/.alpsbox/qc_config.json and persist across restarts."},
    "qc.th_title": {"zh_CN": "质控阈值设置", "en": "QC thresholds"},
    "res.import_title": {"zh_CN": "导入结果（CSV、JSON 或 TSV）",
                  "en": "Import results (CSV, JSON or TSV)"},
    "sep.clause": {"zh_CN": "，", "en": ", "},
    "sep.colon": {"zh_CN": "：", "en": ": "},
    "sep.item": {"zh_CN": "、", "en": "; "},
    "sep.sentence": {"zh_CN": "。", "en": "."},
    "tip.env": {"zh_CN": "环境要求", "en": "Environment requirements"},
    "tip.input_batch": {"zh_CN": "批量目录结构", "en": "Batch folder layout"},
    "tip.input_single": {"zh_CN": "输入目录要求", "en": "Input folder requirements"},
    "tip.qc": {"zh_CN": "质控说明", "en": "QC notes"},
    "tip.qc_thresholds": {"zh_CN": "阈值怎么定", "en": "How thresholds are chosen"},
    "tip.roi_custom": {"zh_CN": "自定义 ROI", "en": "Custom ROI"},
    "tip.roi_bundled": {"zh_CN": "随包参考 ROI", "en": "Bundled ROI"},
    "tip.roi_sphere": {"zh_CN": "自建球 ROI", "en": "Sphere ROI"},
    "tip.roi_viewer": {"zh_CN": "ROI 与 ALPS 的关系", "en": "ROIs and ALPS"},
    "tip.scatter": {"zh_CN": "分组怎么算", "en": "How grouping works"},

    # Keys used by wrapped t() calls (backfill)
    "log.missing": {"zh_CN": "[缺失] %-20s %s", "en": "[missing] %-20s %s"},
    "log.skipped": {"zh_CN": "[跳过] %-20s %s", "en": "[skip] %-20s %s"},
    "log.found_dwi": {"zh_CN": "[可跑] 找到 DWI：%s",
                      "en": "[ready] DWI found: %s"},

}


# =====================================================================
# Language state
# =====================================================================
def get_lang() -> str:
    return _current


def set_lang(lang: str, save: bool = True) -> str:
    """Switch the interface/output language.

    With save=True the choice is written to ~/.alpsbox/prefs.json (an explicit
    user choice, as made by the GUI/CLI); tests and temporary switches can pass
    save=False so that the stored preference is left untouched.
    """
    global _current
    if lang in LANGS:
        _current = lang
        if save:
            save_pref({"lang": lang})
    return _current


def register_strings(mapping: dict) -> None:
    """Register the string table of another module.

    Each module maintains its own table, so STRINGS does not grow without
    bound. Convention: keys carry a module prefix (e.g. "qcx." / "rpt." /
    "pipe." / "cli."), and existing keys are never overwritten (the main GUI
    table wins).
    """
    for key, entry in mapping.items():
        if key in STRINGS:
            continue
        STRINGS[key] = entry


def t(key: str, *args, **kwargs) -> str:
    """Return the string for the current language, falling back to the key."""
    entry = STRINGS.get(key)
    if not entry:
        return key
    s = entry.get(_current) or entry.get(DEFAULT_LANG) or key
    if args or kwargs:
        try:
            return s % (args if args else kwargs)
        except Exception:
            return s
    return s


def load_pref() -> dict:
    try:
        if os.path.isfile(PREFS_FILE):
            with open(PREFS_FILE, encoding="utf-8") as fh:
                d = json.load(fh)
            if isinstance(d, dict):
                return d
    except Exception:
        pass
    return {}


def save_pref(d: dict) -> bool:
    try:
        os.makedirs(PREFS_DIR, exist_ok=True)
        cur = load_pref()
        cur.update(d)
        tmp = PREFS_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(cur, fh, ensure_ascii=False, indent=1)
        os.replace(tmp, PREFS_FILE)
        return True
    except Exception:
        return False


def init_lang() -> str:
    """Initialise the language at start-up: always English.

    English is the primary language of the project and its documentation.
    Other languages are chosen explicitly (GUI home page or ``--lang``) for the
    running session. A saved preference is not applied automatically, so every
    new start is reproducible and begins from the documented default.
    """
    global _current
    _current = DEFAULT_LANG
    return _current


def detect_system_lang() -> str:
    """Guess the language from the system locale.

    Only used to preselect on first start; the welcome page always lets the
    user confirm.
    """
    import locale as _locale
    cands = []
    for k in ("LC_ALL", "LC_MESSAGES", "LANGUAGE", "LANG"):
        v = os.environ.get(k)
        if v:
            cands.append(v)
    try:
        loc = _locale.getlocale()[0] or ""
        cands.append(loc)
    except Exception:
        pass
    try:
        dl = _locale.getdefaultlocale()[0] or ""
        cands.append(dl)
    except Exception:
        pass
    for c in cands:
        c = str(c).lower()
        if c.startswith("zh"):
            return "zh_CN"
        if c.startswith("en"):
            return "en"
        if c.startswith(("ja", "ko", "de", "fr", "es")):
            # No text for these languages yet: fall back to English. The
            # welcome page can be extended.
            return "en"
    return DEFAULT_LANG


def available_langs() -> list:
    """For the welcome-page language picker: [(code, localised name), ...]."""
    return [(code, name) for code, name in LANGS.items()]
