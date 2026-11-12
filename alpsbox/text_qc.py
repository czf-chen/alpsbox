# -*- coding: utf-8 -*-
"""English and Chinese strings for quality control and QC figures (registered
with i18n.STRINGS, key prefix ``qcx.``).

Scope
-----
* ``qc.py``: the four-level verdict labels and marks, the name, description and
  advice of each check item, the issue lists (issues / notes), threshold
  validation messages, the single-subject and batch summary reports, and the
  verdict summary lines.
* ``plotting.py``: titles, axis labels, legends and in-figure annotations of the
  motion time-series plot and the cross-subject scatter plot, plus the
  RuntimeError message used when plotting is unavailable.
* ``roi_preview.py``: the hints drawn on the slice preview image and the
  RuntimeError message used when a dependency is missing.

Conventions
-----------
* The Chinese entries reproduce the current code verbatim (the existing tests
  assert on Chinese text); the English entries are new translations. The type,
  order and number of placeholders correspond one-to-one between the two sides
  (e.g. ``%.3f``, ``%-20s``).
* Internal level keys ``ok/info/warn/fail`` and the CSV/JSON field names are not
  translated; only the human-readable labels are (pass / info / check / fail).
* Technical terms are copied verbatim: ALPS, FSL, eddy, eddy_correct, repol,
  vecreg, fslcc, dcm2niix, b0, .json, FA_in_mni.nii.gz, ROI, mm, %, etc.
* In-figure text follows the interface language by default; if no usable
  Chinese font is installed in Chinese mode, the plotting module falls back to
  English automatically to avoid missing-glyph boxes (see ``plotting._lbl``).
"""
from .i18n import register_strings, t

STRINGS = {
    # =================================================================
    # qc.py: four-level verdicts
    # =================================================================
    "qcx.level.ok": {"zh_CN": "通过", "en": "Pass"},
    "qcx.level.info": {"zh_CN": "提示", "en": "Info"},
    "qcx.level.warn": {"zh_CN": "需注意", "en": "Check"},
    "qcx.level.fail": {"zh_CN": "不合格", "en": "Fail"},
    "qcx.mark.ok": {"zh_CN": "[通过]", "en": "[pass]"},
    "qcx.mark.info": {"zh_CN": "[提示]", "en": "[info]"},
    "qcx.mark.warn": {"zh_CN": "[注意]", "en": "[check]"},
    "qcx.mark.fail": {"zh_CN": "[不合格]", "en": "[fail]"},

    # ---- Common values ----
    "qcx.unnamed": {"zh_CN": "未命名", "en": "unnamed"},
    "qcx.status_ok": {"zh_CN": "成功", "en": "Success"},
    "qcx.status_unknown": {"zh_CN": "未知", "en": "Unknown"},
    "qcx.untested": {"zh_CN": "未测", "en": "not measured"},
    "qcx.missing": {"zh_CN": "缺失", "en": "missing"},
    "qcx.count_slices": {"zh_CN": "%d 条", "en": "%d slices"},
    "qcx.count_per_vol": {"zh_CN": "%d 条（%.2f/体积）",
                          "en": "%d slices (%.2f/volume)"},

    # ---- Punctuation used when joining fragments ----
    "qcx.join_semicolon": {"zh_CN": "；", "en": "; "},
    "qcx.join_enum": {"zh_CN": "、", "en": ", "},
    "qcx.note_prefix": {"zh_CN": "提示：", "en": "Note: "},
    "qcx.all_normal": {
        "zh_CN": "各项指标均在正常范围。",
        "en": "All metrics are within the normal range."},

    # ---- Check item names ----
    "qcx.chk.run": {"zh_CN": "处理状态", "en": "Processing status"},
    "qcx.chk.roi": {"zh_CN": "ROI 体素数", "en": "ROI voxels"},
    "qcx.chk.r_wm": {"zh_CN": "配准质量", "en": "Registration quality"},
    "qcx.chk.motion": {"zh_CN": "头动", "en": "Head motion"},
    "qcx.chk.motion_rel": {"zh_CN": "相对位移", "en": "Relative motion"},
    "qcx.chk.motion_abs": {"zh_CN": "绝对位移", "en": "Absolute motion"},
    "qcx.chk.motion_rel_mm": {"zh_CN": "相对位移（均值/最大）",
                              "en": "Relative motion (mean/max)"},
    "qcx.chk.motion_abs_mm": {"zh_CN": "绝对位移（均值/最大）",
                              "en": "Absolute motion (mean/max)"},
    "qcx.chk.outlier": {"zh_CN": "离群切片", "en": "Outlier slices"},
    "qcx.chk.method": {"zh_CN": "校正方法", "en": "Correction method"},
    "qcx.chk.alps_mean": {"zh_CN": "ALPS 均值", "en": "ALPS mean"},
    "qcx.chk.alps_L": {"zh_CN": "ALPS 左", "en": "ALPS left"},
    "qcx.chk.alps_R": {"zh_CN": "ALPS 右", "en": "ALPS right"},

    # =================================================================
    # qc.py: check descriptions (detail) and advice (advice)
    # =================================================================
    # ---- 1. Processing status ----
    "qcx.d.run": {
        "zh_CN": "pipeline 是否完整跑完。",
        "en": "Whether the pipeline ran to completion."},
    # ---- 2. ROI voxel count ----
    "qcx.d.roi_empty": {
        "zh_CN": "期望每个 ROI 为 %d 体素，实际有 ROI 为空。",
        "en": "Expected %d voxels per ROI, but at least one ROI is empty."},
    "qcx.a.roi_empty": {
        "zh_CN": "多半是配准失败或 ROI 与图像不在同一空间。"
                 "检查该被试的 FA_in_mni.nii.gz 与模板是否对齐。",
        "en": "Most likely the registration failed or the ROI and the image "
              "are not in the same space. Check that this subject's "
              "FA_in_mni.nii.gz is aligned with the template."},
    "qcx.d.roi_bad": {
        "zh_CN": "期望每个 ROI 为 %d 体素，有 %d 个不符。",
        "en": "Expected %d voxels per ROI; %d do not match."},
    "qcx.a.roi_bad": {
        "zh_CN": "若改过自建球半径，体素数本来就会变，"
                 "可以到阈值设置里关掉「严格检查 ROI 体素数」。"
                 "用随包参考 ROI 时出现偏离，检查数据是否被重采样过。",
        "en": "If you changed a custom sphere radius, the voxel count will "
              "change by design — turn off \"strict ROI voxel check\" in the "
              "threshold settings. With the bundled reference ROIs, a "
              "mismatch suggests the data were resampled."},
    "qcx.d.roi_ok": {
        "zh_CN": "四个 ROI 均为 %d 体素，与随包参考掩膜一致。",
        "en": "All four ROIs have %d voxels, matching the bundled reference "
              "masks."},
    "qcx.d.roi_skip": {
        "zh_CN": "ROI 体素数已按设置跳过严格检查。",
        "en": "Strict ROI voxel check is disabled in the settings."},
    "qcx.d.roi_missing": {
        "zh_CN": "记录里没有 ROI 体素信息。",
        "en": "No ROI voxel information in this record."},
    # ---- 3. Registration quality ----
    "qcx.d.r_wm_missing": {
        "zh_CN": "没有 r_wm 值。通常是本机缺 fslcc，或该被试没跑到质控步。",
        "en": "No r_wm value. Usually fslcc is missing on this machine, or "
              "this subject never reached the QC step."},
    "qcx.d.r_wm_ok": {
        "zh_CN": "FA 与模板的相关系数 %.3f，配准良好。",
        "en": "FA–template correlation %.3f; registration looks good."},
    "qcx.d.r_wm_warn": {
        "zh_CN": "相关系数 %.3f，低于设定下限 %.2f。",
        "en": "Correlation %.3f, below the configured floor %.2f."},
    "qcx.a.r_wm_warn": {
        "zh_CN": "看该被试的 FA_in_mni.nii.gz 是否明显错位；必要时重跑配准。"
                 "配准质量差的被试，其 ALPS 对预处理参数（如 bet 阈值、配准代价）"
                 "可能更敏感；跨研究比较时建议固定并报告全部参数。"
                 "注意：r_wm 绝对值随分辨率、序列与模板而变，不宜跨数据集"
                 "直接比较，应在同一队列内横向判断。",
        "en": "Check whether this subject's FA_in_mni.nii.gz is clearly "
              "misaligned; rerun the registration if needed. In subjects with "
              "poor registration quality, ALPS can be more sensitive to "
              "preprocessing parameters such as the bet threshold and the "
              "registration cost; fix and report all parameters when comparing "
              "studies. Note: r_wm depends on resolution, sequence and template, "
              "so absolute values should not be compared across datasets; judge "
              "within the same cohort."},
    "qcx.d.r_wm_fail": {
        "zh_CN": "相关系数 %.3f，低于 %.2f，配准很可能失败。",
        "en": "Correlation %.3f, below %.2f — the registration most likely "
              "failed."},
    "qcx.a.r_wm_fail": {
        "zh_CN": "该被试的 ALPS 不建议采用。检查 b0 提取、脑掩膜与初始朝向；"
                 "若确认图像本身有问题，应在统计中剔除并说明。",
        "en": "This subject's ALPS is not recommended for use. Check b0 "
              "extraction, the brain mask and the initial orientation; if the "
              "images themselves are bad, exclude the subject from statistics "
              "and state why."},
    # ---- 4. Head motion ----
    "qcx.d.motion_missing": {
        "zh_CN": "没有 eddy 运动指标。回落到 eddy_correct 或没有 json 时会缺这一项。"
                 "可用 alpsbox rescan 从已有 eddy 输出补算。",
        "en": "No eddy motion metrics. This item is missing when the pipeline "
              "fell back to eddy_correct or no .json was available. Use "
              "\"alpsbox rescan\" to recompute them from existing eddy output."},
    "qcx.d.motion_rel_missing": {
        "zh_CN": "缺少相对位移（逐卷抖动）数据。",
        "en": "Relative (frame-wise) motion data are missing."},
    "qcx.d.motion_rel_fail": {
        "zh_CN": "逐卷位移超过上界（均值 %.2f、最大 %.2f mm）。",
        "en": "Frame-wise displacement exceeds the upper bound "
              "(mean %.2f, max %.2f mm)."},
    "qcx.a.motion_rel_fail": {
        "zh_CN": "抖动大时 eddy 校正后仍会有残影，ALPS 可能不可靠，建议剔除。",
        "en": "With large jitter, eddy-corrected images still carry ghosting "
              "and ALPS may be unreliable; consider excluding the subject."},
    "qcx.d.motion_rel_warn": {
        "zh_CN": "高于常用阈值（均值 %.2f、最大 %.2f mm）。",
        "en": "Above the usual thresholds (mean %.2f, max %.2f mm)."},
    "qcx.a.motion_rel_warn": {
        "zh_CN": "建议把相对位移作为协变量放进统计，或做剔除前后两次分析。",
        "en": "Consider adding relative motion as a covariate, or analysing "
              "the data both with and without exclusion."},
    "qcx.d.motion_rel_ok": {
        "zh_CN": "逐卷位移正常，这个指标不随扫描时长累积，可跨组比较。",
        "en": "Frame-wise displacement is normal; this metric does not "
              "accumulate with scan length, so it is comparable across "
              "groups."},
    "qcx.d.motion_abs_missing": {
        "zh_CN": "缺少绝对位移（相对参考卷）数据。",
        "en": "Absolute (relative to the reference volume) motion data are "
              "missing."},
    "qcx.d.motion_abs_fail": {
        "zh_CN": "整体漂移超过上界（均值 %.2f、最大 %.2f mm）。",
        "en": "Overall drift exceeds the upper bound (mean %.2f, max %.2f mm)."},
    "qcx.a.motion_abs_fail": {
        "zh_CN": "漂移大会让配准变糊。注意这个值随扫描时长累积，"
                 "不同体积数的序列不能直接比。",
        "en": "Large drift blurs the registration. Note that this value "
              "accumulates with scan length, so sequences with different "
              "volume counts cannot be compared directly."},
    "qcx.d.motion_abs_warn": {
        "zh_CN": "整体漂移偏大（均值 %.2f、最大 %.2f mm）。",
        "en": "Overall drift is on the high side (mean %.2f, max %.2f mm)."},
    "qcx.a.motion_abs_warn": {
        "zh_CN": "这个指标随扫描时长累积，长序列天然更大，"
                 "组间比较时请用相对位移。",
        "en": "This metric accumulates with scan length and is naturally "
              "larger for long sequences; use relative motion when comparing "
              "groups."},
    "qcx.d.motion_abs_ok": {
        "zh_CN": "整体漂移在可接受范围。",
        "en": "Overall drift is acceptable."},
    # ---- 5. Outlier slices ----
    "qcx.d.outlier_missing": {
        "zh_CN": "没有 eddy 离群报告。",
        "en": "No eddy outlier report."},
    "qcx.d.outlier_hi": {
        "zh_CN": "平均每个体积 %.2f 条离群切片，超过设定值 %.2f。",
        "en": "%.2f outlier slices per volume on average, above the "
              "configured %.2f."},
    "qcx.a.outlier_hi": {
        "zh_CN": "离群切片已被 eddy 的 repol 替换，但数量多说明数据质量一般，"
                 "建议结合原始图像判断。",
        "en": "eddy's repol has already replaced these slices, but a high "
              "count indicates mediocre data quality; judge together with the "
              "raw images."},
    "qcx.d.outlier_ok": {
        "zh_CN": "离群切片比例正常，且已由 repol 替换。",
        "en": "The outlier slice fraction is normal and these slices have "
              "been replaced by repol."},
    # ---- 6. Correction method ----
    "qcx.d.method_eddy_correct": {
        "zh_CN": "回落到 eddy_correct。该命令不做张量重定向，且有已知偏差"
                 "（扩散率与各向异性会被低估）。"
                 "**不建议把该被试的 ALPS 与其他用 eddy 处理的被试直接比较。**",
        "en": "Fell back to eddy_correct. That command does not reorient "
              "tensors and is known to bias the result (diffusivity and "
              "anisotropy are underestimated). "
              "**Do not compare this subject's ALPS directly with subjects "
              "processed by full eddy.**"},
    "qcx.a.method_eddy_correct": {
        "zh_CN": "补上 .json（dcm2niix 加 -b o）后重跑，才能用完整 eddy；"
                 "否则应在统计中单独报告或排除。",
        "en": "Rerun after supplying the .json (dcm2niix with -b o) so full "
              "eddy can be used; otherwise report this subject separately in "
              "the statistics or exclude it."},
    "qcx.d.method_cpu": {
        "zh_CN": "eddy 在 CPU 上运行，结果可用，只是慢。",
        "en": "eddy ran on the CPU; the result is usable, just slower."},
    "qcx.d.method_ok": {
        "zh_CN": "使用完整 eddy（含 repol），这是推荐路径。",
        "en": "Full eddy (with repol) was used — this is the recommended "
              "path."},
    # ---- 7. ALPS values ----
    "qcx.d.alps_missing": {
        "zh_CN": "没有算出这一项。",
        "en": "This value could not be computed."},
    "qcx.d.alps_range": {
        "zh_CN": "超出设定范围 %.2f–%.2f。",
        "en": "Outside the configured range %.2f–%.2f."},
    "qcx.a.alps_range": {
        "zh_CN": "先排查张量重定向是否执行（vecreg）、ROI 是否在正确空间。"
                 "若确认无误，可作为离群值在统计中说明。",
        "en": "First check that tensor reorientation (vecreg) ran and that the "
              "ROI is in the correct space. If everything checks out, report "
              "it as an outlier in the statistics."},

    # =================================================================
    # qc.py: issue list (issues) and notes (notes)
    # =================================================================
    "qcx.i.run_failed": {"zh_CN": "处理未完成", "en": "Processing incomplete"},
    "qcx.i.roi_empty": {"zh_CN": "ROI 为空", "en": "Empty ROI"},
    "qcx.i.roi_bad": {"zh_CN": "ROI 体素数偏离", "en": "ROI voxel count off"},
    "qcx.i.r_wm_warn": {"zh_CN": "配准偏低",
                        "en": "Registration on the low side"},
    "qcx.i.r_wm_fail": {"zh_CN": "配准失败", "en": "Registration failed"},
    "qcx.i.jitter_big": {"zh_CN": "抖动过大", "en": "Excessive jitter"},
    "qcx.i.jitter_slight": {"zh_CN": "抖动偏大",
                            "en": "Jitter on the high side"},
    "qcx.i.drift_big": {"zh_CN": "整体漂移大", "en": "Large overall drift"},
    "qcx.i.outlier_big": {"zh_CN": "离群切片偏多",
                          "en": "Too many outlier slices"},
    "qcx.i.outlier_slight": {"zh_CN": "离群切片略多",
                             "en": "Slightly many outlier slices"},
    "qcx.i.eddy_correct": {"zh_CN": "用了 eddy_correct",
                           "en": "eddy_correct was used"},
    "qcx.i.alps_missing": {"zh_CN": "%s 缺失", "en": "%s missing"},
    "qcx.i.alps_range": {"zh_CN": "%s 超出范围", "en": "%s out of range"},
    "qcx.n.drift": {"zh_CN": "整体漂移偏大",
                    "en": "Overall drift on the high side"},
    "qcx.n.drift_val": {"zh_CN": "整体漂移偏大（%.2f mm）",
                        "en": "Overall drift on the high side (%.2f mm)"},
    "qcx.n.cpu_eddy": {"zh_CN": "用了 CPU 版 eddy",
                       "en": "CPU version of eddy used"},

    # =================================================================
    # qc.py: threshold validation
    # =================================================================
    "qcx.v.r_wm_order": {
        "zh_CN": "r_wm：不合格阈值不能高于通过阈值",
        "en": "r_wm: the fail threshold must not exceed the pass threshold"},
    "qcx.v.rel_mean": {
        "zh_CN": "相对位移均值：不合格阈值不能低于警告阈值",
        "en": "Relative motion mean: the fail threshold must not be below the "
              "warn threshold"},
    "qcx.v.rel_max": {
        "zh_CN": "相对位移最大值：不合格阈值不能低于警告阈值",
        "en": "Relative motion max: the fail threshold must not be below the "
              "warn threshold"},
    "qcx.v.abs_mean": {
        "zh_CN": "绝对位移均值：不合格阈值不能低于警告阈值",
        "en": "Absolute motion mean: the fail threshold must not be below the "
              "warn threshold"},
    "qcx.v.abs_max": {
        "zh_CN": "绝对位移最大值：不合格阈值不能低于警告阈值",
        "en": "Absolute motion max: the fail threshold must not be below the "
              "warn threshold"},
    "qcx.v.outlier": {
        "zh_CN": "离群比例：不合格阈值不能低于警告阈值",
        "en": "Outlier fraction: the fail threshold must not be below the warn "
              "threshold"},
    "qcx.v.alps_range": {
        "zh_CN": "ALPS 区间：下限必须小于上限",
        "en": "ALPS range: the lower bound must be below the upper bound"},
    "qcx.v.roi_voxels": {
        "zh_CN": "ROI 体素数必须为正整数",
        "en": "ROI voxel count must be a positive integer"},
    "qcx.v.nan": {
        "zh_CN": "%s 不是有效数字",
        "en": "%s is not a valid number"},
    "qcx.vn.r_wm_ok": {"zh_CN": "r_wm 通过", "en": "r_wm pass"},
    "qcx.vn.r_wm_fail": {"zh_CN": "r_wm 不合格", "en": "r_wm fail"},
    "qcx.vn.rel_mean": {"zh_CN": "相对位移均值",
                        "en": "relative motion mean"},
    "qcx.vn.abs_mean": {"zh_CN": "绝对位移均值",
                        "en": "absolute motion mean"},
    "qcx.vn.alps_min": {"zh_CN": "ALPS 下限", "en": "ALPS lower bound"},

    # =================================================================
    # qc.py: single-subject report / batch summary
    # =================================================================
    "qcx.r.subject": {"zh_CN": "被试：%s", "en": "Subject: %s"},
    "qcx.r.overall": {"zh_CN": "总体判定：%s", "en": "Overall: %s"},
    "qcx.r.thresholds": {"zh_CN": "判定阈值：%s", "en": "Thresholds: %s"},
    "qcx.r.check_line": {"zh_CN": "%s %s：%s", "en": "%s %s: %s"},
    "qcx.r.advice": {"zh_CN": "        建议：%s", "en": "        Advice: %s"},
    "qcx.r.attention": {"zh_CN": "需要关注：%s",
                        "en": "Needs attention: %s"},
    "qcx.r.no_attention": {"zh_CN": "没有发现需要关注的问题。",
                           "en": "No issues need attention."},
    "qcx.b.title": {"zh_CN": "ALPSbox 质控汇总", "en": "ALPSbox QC summary"},
    "qcx.b.total": {"zh_CN": "被试总数：%d", "en": "Subjects: %d"},
    "qcx.b.counts": {
        "zh_CN": "通过：%d    提示：%d    需注意：%d    不合格：%d",
        "en": "Pass: %d    Info: %d    Check: %d    Fail: %d"},
    "qcx.b.top_issues": {"zh_CN": "最常见的问题：",
                         "en": "Most common issues:"},
    "qcx.b.issue_line": {"zh_CN": "  %-20s %d 个被试",
                         "en": "  %-20s %d subjects"},
    "qcx.b.bad_subjects": {"zh_CN": "需要关注的被试：",
                           "en": "Subjects needing attention:"},
    "qcx.b.all_pass": {"zh_CN": "所有被试均通过质控。",
                       "en": "All subjects passed QC."},

    # =================================================================
    # plotting.py: motion time-series plot
    # =================================================================
    "qcx.plot.motion_title": {
        "zh_CN": "%s   头动随体积变化（n=%d）",
        "en": "%s   head motion over volumes (n=%d)"},
    "qcx.plot.outlier_vols": {"zh_CN": "    离群体积：%s",
                              "en": "    outlier volumes: %s"},
    "qcx.plot.abs_ylabel": {"zh_CN": "绝对位移（mm）",
                            "en": "Absolute displacement (mm)"},
    "qcx.plot.rel_ylabel": {"zh_CN": "逐卷位移（mm）",
                            "en": "Frame-wise displacement (mm)"},
    "qcx.plot.xlabel": {"zh_CN": "体积序号", "en": "Volume index"},
    "qcx.plot.legend_warn": {"zh_CN": "警告 %.2f", "en": "warn %.2f"},
    "qcx.plot.legend_fail": {"zh_CN": "不合格 %.2f", "en": "fail %.2f"},
    "qcx.plot.legend_warn_max": {"zh_CN": "警告（最大） %.2f",
                                 "en": "warn(max) %.2f"},
    "qcx.plot.mean_max": {"zh_CN": "均值 %.3f    最大 %.3f",
                          "en": "mean %.3f    max %.3f"},

    # ---- plotting.py: registration/ROI overview for the HTML report ----
    "qcx.plot.reg_title": {
        "zh_CN": "%s：配准后 FA（模板空间）与四个 ROI",
        "en": "%s: FA in template space with the four ROIs"},
    "qcx.plot.reg_axial": {"zh_CN": "轴位", "en": "Axial"},
    "qcx.plot.reg_coronal": {"zh_CN": "冠状位", "en": "Coronal"},
    "qcx.plot.reg_sagittal": {"zh_CN": "矢状位", "en": "Sagittal"},
    "qcx.plot.reg_fa": {"zh_CN": "灰阶：FA_in_mni",
                        "en": "Grey: FA_in_mni"},
    "qcx.plot.reg_roi": {"zh_CN": "彩色：2.5 mm ROI（各 81 体素）",
                         "en": "Colours: 2.5 mm ROIs (81 voxels each)"},
    "qcx.plot.no_fa": {"zh_CN": "没有找到 FA_in_mni.nii.gz",
                       "en": "FA_in_mni.nii.gz was not found"},
    "qcx.plot.reg_shape": {"zh_CN": "FA 与 ROI 掩膜尺寸不一致",
                           "en": "FA and ROI mask shapes differ"},
    "qcx.plot.roi_missing_s": {"zh_CN": "ROI 文件缺失: %s",
                               "en": "ROI file missing: %s"},

    # ---- plotting.py: cross-subject scatter ----
    "qcx.plot.scatter_title": {"zh_CN": "跨被试质控散点图",
                               "en": "QC scatter across subjects"},
    "qcx.plot.group_all": {"zh_CN": "全部被试（n=%d）",
                           "en": "all subjects (n=%d)"},
    "qcx.plot.group_n": {"zh_CN": "%s（n=%d）", "en": "%s (n=%d)"},
    "qcx.plot.var_alps_mean": {"zh_CN": "ALPS 均值", "en": "ALPS mean"},
    "qcx.plot.var_alps_L": {"zh_CN": "ALPS 左", "en": "ALPS left"},
    "qcx.plot.var_alps_R": {"zh_CN": "ALPS 右", "en": "ALPS right"},
    "qcx.plot.var_r_wm": {"zh_CN": "配准 r_wm", "en": "Registration r_wm"},
    "qcx.plot.var_abs_mean": {"zh_CN": "绝对位移均值（mm）",
                              "en": "Absolute motion mean (mm)"},
    "qcx.plot.var_abs_max": {"zh_CN": "绝对位移最大（mm）",
                             "en": "Absolute motion max (mm)"},
    "qcx.plot.var_rel_mean": {"zh_CN": "相对位移均值（mm）",
                              "en": "Rel. motion mean (mm)"},
    "qcx.plot.var_rel_max": {"zh_CN": "相对位移最大（mm）",
                             "en": "Rel. motion max (mm)"},
    "qcx.plot.var_outlier": {"zh_CN": "离群切片数", "en": "Outlier slices"},
    "qcx.plot.var_vol": {"zh_CN": "体积数", "en": "Volumes"},
    "qcx.plot.var_seconds": {"zh_CN": "处理耗时（s）",
                             "en": "Processing time (s)"},

    # ---- plotting.py: grouping modes (shown in the GUI dropdown) ----
    "qcx.plot.group_auto": {"zh_CN": "按 ID 前缀", "en": "By ID prefix"},
    "qcx.plot.group_column": {"zh_CN": "用 group 列",
                              "en": "Use group column"},
    "qcx.plot.group_none": {"zh_CN": "不分组", "en": "No grouping"},

    # ---- plotting.py: error messages ----
    "qcx.plot.need_mpl": {"zh_CN": "需要 matplotlib",
                          "en": "matplotlib is required"},
    "qcx.plot.no_motion": {"zh_CN": "没有找到可用的头动数据",
                           "en": "No usable head-motion data found"},
    "qcx.plot.no_points": {"zh_CN": "这两个变量没有可用的数据点",
                           "en": "No usable data points for these two "
                                 "variables"},

    # =================================================================
    # roi_preview.py
    # =================================================================
    "qcx.roi.no_template": {
        "zh_CN": "未找到 JHU-ICBM-FA-1mm 模板，仅显示 ROI 轮廓",
        "en": "JHU-ICBM-FA-1mm template not found; showing ROI outlines only"},
    "qcx.roi.need_nibabel": {"zh_CN": "需要 nibabel",
                             "en": "nibabel is required"},
    "qcx.roi.need_pillow": {"zh_CN": "需要 Pillow",
                            "en": "Pillow is required"},
    "qcx.roi.files_missing": {"zh_CN": "ROI 文件缺失: %s",
                              "en": "ROI file missing: %s"},
}

register_strings(STRINGS)


# =====================================================================
# Utilities
# =====================================================================
def english(key: str, *args) -> str:
    """Return the English wording, independent of the current language.

    In-figure text has to fall back to English when no Chinese font is
    available on this machine (see plotting._lbl).
    """
    entry = STRINGS.get(key)
    if not entry:
        return key
    s = entry.get("en") or entry.get("zh_CN") or key
    if args:
        try:
            return s % args
        except Exception:
            return s
    return s


class LangDict(dict):
    """Dictionary with a fixed key set whose values are translated live in the
    current language.

    Used for mappings that historically stored human-readable text as the value
    (``qc.LEVEL_LABEL``, ``plotting.GROUP_MODES``,
    ``plotting.SCATTER_VARS``). The keys are unchanged, so existing code that
    looks values up by reverse mapping or passes keys as arguments is
    unaffected.

    key_map : {original key: i18n key name}
    tr      : value lookup function, i18n.t by default; in-figure text can pass
              a wrapper with font fallback.
    """

    def __init__(self, key_map, tr=None):
        # The underlying store still holds the Chinese originals, so
        # dict(LEVEL_LABEL) / copy() and similar return Chinese, matching the
        # behaviour of the plain dict these replaced.
        defaults = {}
        for k, key in key_map.items():
            entry = STRINGS.get(key) or {}
            defaults[k] = entry.get("zh_CN") or entry.get("en") or key
        super().__init__(defaults)
        self._key_map = dict(key_map)
        self._tr = tr

    def _lookup(self, k):
        fn = self._tr or t
        return fn(self._key_map[k])

    def __getitem__(self, k):
        if k in self._key_map:
            return self._lookup(k)
        raise KeyError(k)

    def get(self, k, default=None):
        if k in self._key_map:
            return self._lookup(k)
        return default

    def items(self):
        return [(k, self._lookup(k)) for k in self._key_map]

    def values(self):
        return [self._lookup(k) for k in self._key_map]

    def copy(self):
        return dict(self.items())
