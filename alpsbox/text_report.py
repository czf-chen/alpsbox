# -*- coding: utf-8 -*-
"""English and Chinese strings for the report module (registered with
i18n.STRINGS).

The Chinese originals are reproduced verbatim from the existing reports (the
current tests assert on Chinese text); the English entries are new
translations. Placeholders (%s / %d / %.3f / %+.1f / %% ...) and their order
are kept identical on both sides. Terminology, units (mm, %, r_wm, regqc,
bet -f, vecreg, eddy_correct) and the references themselves are not
translated; all citations are provided by alpsbox/citations.py.
"""
from .i18n import register_strings

STRINGS = {
    # ================= interpret(): verdict and per-line interpretation =====
    "rpt.verdict.noalps": {"zh_CN": "未得到有效 ALPS 值",
                           "en": "No valid ALPS value"},
    "rpt.line.noalps": {
        "zh_CN": "该被试未能算出 ALPS，请查看质控报告与日志。",
        "en": "ALPS could not be computed for this subject; see the QC report "
              "and the log."},
    "rpt.line.alps_index": {"zh_CN": "ALPS 指数（双侧均值）= %.3f",
                            "en": "ALPS index (bilateral mean) = %.3f"},
    "rpt.line.compare_head": {"zh_CN": "与文献参考比较：",
                              "en": "Compared with published references:"},
    "rpt.line.ref_taoka": {
        "zh_CN": "  · Taoka 2017 健康对照 1.35 ± 0.20 → 本被试 %+.1f 个标准差（z = %.2f）",
        "en": "  · Taoka 2017 healthy controls 1.35 ± 0.20 → this subject "
              "%+.1f SD (z = %.2f)"},
    "rpt.line.plausible": {"zh_CN": "  · 落在常见合理范围 %.1f–%.1f 内",
                           "en": "  · Within the plausible range %.1f–%.1f"},
    "rpt.line.implausible": {
        "zh_CN": "  · ⚠️ 超出常见合理范围 %.1f–%.1f，建议核查数据质量",
        "en": "  · ⚠️ Outside the plausible range %.1f–%.1f; check data quality"},

    "rpt.line.asym": {"zh_CN": "左右差异：L = %.3f，R = %.3f，不对称度 %.1f%%",
                      "en": "Left-right difference: L = %.3f, R = %.3f, "
                            "asymmetry %.1f%%"},
    "rpt.line.asym_large": {
        "zh_CN": "  ⚠️ 左右差异偏大（>15%%），可能与局部配准或伪影有关。",
        "en": "  ⚠️ Left-right asymmetry is large (>15%), possibly related to "
              "local registration or artefacts."},

    "rpt.line.qc_head": {"zh_CN": "质控要点：", "en": "QC highlights:"},
    "rpt.line.rwm_good": {"zh_CN": "  · 配准质量良好（r_wm = %.3f）",
                          "en": "  · Registration quality good (r_wm = %.3f)"},
    "rpt.line.rwm_ok": {"zh_CN": "  · 配准可接受（r_wm = %.3f）",
                        "en": "  · Registration acceptable (r_wm = %.3f)"},
    "rpt.line.rwm_bad": {"zh_CN": "  · ⚠️ 配准可疑（r_wm = %.3f），结果需谨慎解释",
                         "en": "  · ⚠️ Registration questionable "
                               "(r_wm = %.3f); interpret with care"},
    "rpt.line.motion_low": {"zh_CN": "  · 头动小（帧间相对位移 %.2f mm）",
                            "en": "  · Head motion low (frame-to-frame "
                                  "displacement %.2f mm)"},
    "rpt.line.motion_mid": {"zh_CN": "  · 头动中等（帧间相对位移 %.2f mm）",
                            "en": "  · Head motion moderate (frame-to-frame "
                                  "displacement %.2f mm)"},
    "rpt.line.motion_high": {"zh_CN": "  · ⚠️ 头动较大（帧间相对位移 %.2f mm）",
                             "en": "  · ⚠️ Head motion high (frame-to-frame "
                                   "displacement %.2f mm)"},
    "rpt.line.outlier_ok": {"zh_CN": "  · 离群体积 %d/%d（%.0f%%），正常",
                            "en": "  · Outlier volumes %d/%d (%.0f%%), normal"},
    "rpt.line.outlier_high": {"zh_CN": "  · ⚠️ 离群体积 %d/%d（%.0f%%），偏多",
                              "en": "  · ⚠️ Outlier volumes %d/%d (%.0f%%), "
                                    "too many"},
    "rpt.line.eddy_correct": {
        "zh_CN": "  · ⚠️ 该被试因缺少 JSON 元数据回落到 eddy_correct，存在已知的 MD/FA 低估偏差",
        "en": "  · ⚠️ Missing JSON metadata forced a fallback to eddy_correct, "
              "which has a known MD/FA underestimation bias"},
    "rpt.line.regqc_pass": {
        "zh_CN": "  · 配准稳健：12 次矩阵扰动下 ALPS 极差 %.1f%%，稳定",
        "en": "  · Registration robust: ALPS range %.1f%% over 12 matrix "
              "perturbations, stable"},
    "rpt.line.regqc_info": {
        "zh_CN": "  · ⚠️ 配准较敏感：扰动下 ALPS 极差 %.1f%%，结果对配准精度较依赖",
        "en": "  · ⚠️ Registration somewhat sensitive: ALPS range %.1f%% under "
              "perturbation; the result depends on registration accuracy"},
    "rpt.line.regqc_warn": {
        "zh_CN": "  · ⚠️ 配准高度敏感：扰动下 ALPS 极差 %.1f%%，建议复核配准后再使用该结果",
        "en": "  · ⚠️ Registration highly sensitive: ALPS range %.1f%% under "
              "perturbation; review the registration before using this result"},
    "rpt.line.qc_value": {"zh_CN": "  · 质控判定：%s", "en": "  · QC verdict: %s"},

    "rpt.verdict.ok": {"zh_CN": "处理成功，质量良好",
                       "en": "Processed successfully, quality good"},
    "rpt.verdict.info": {"zh_CN": "处理成功，有轻微提示",
                         "en": "Processed successfully, minor notes"},
    "rpt.verdict.warn": {"zh_CN": "处理成功，但需注意若干质控项",
                         "en": "Processed successfully, but several QC items "
                               "need attention"},
    "rpt.verdict.fail": {"zh_CN": "该被试结果不建议直接使用",
                         "en": "This subject's result is not recommended for "
                               "direct use"},

    # ================= Reference-definition labels (refs from interpret) ====
    "rpt.ref.taoka": {"zh_CN": "Taoka 2017, 认知正常对照",
                      "en": "Taoka 2017, cognitively normal controls"},

    # ================= Single-subject report: title and table rows =========
    "rpt.title.single": {"zh_CN": "ALPS 分析报告", "en": "ALPS analysis report"},
    "rpt.row.subject": {"zh_CN": "被试", "en": "Subject"},
    "rpt.row.time": {"zh_CN": "分析时间", "en": "Analysis time"},
    "rpt.row.method": {"zh_CN": "校正方法", "en": "Distortion correction"},
    "rpt.row.nvol": {"zh_CN": "体积数", "en": "Volumes"},
    "rpt.row.alps_L": {"zh_CN": "<b>ALPS 左</b>", "en": "<b>ALPS left</b>"},
    "rpt.row.alps_R": {"zh_CN": "<b>ALPS 右</b>", "en": "<b>ALPS right</b>"},
    "rpt.row.alps_mean": {"zh_CN": "<b>ALPS 双侧均值</b>",
                          "en": "<b>ALPS bilateral mean</b>"},

    "rpt.row.dxx_L_proj": {"zh_CN": "Dxx 投射区 左", "en": "Dxx projection L"},
    "rpt.row.dyy_L_proj": {"zh_CN": "Dyy 投射区 左", "en": "Dyy projection L"},
    "rpt.row.dxx_L_asso": {"zh_CN": "Dxx 联络区 左", "en": "Dxx association L"},
    "rpt.row.dzz_L_asso": {"zh_CN": "Dzz 联络区 左", "en": "Dzz association L"},
    "rpt.row.dxx_R_proj": {"zh_CN": "Dxx 投射区 右", "en": "Dxx projection R"},
    "rpt.row.dyy_R_proj": {"zh_CN": "Dyy 投射区 右", "en": "Dyy projection R"},
    "rpt.row.dxx_R_asso": {"zh_CN": "Dxx 联络区 右", "en": "Dxx association R"},
    "rpt.row.dzz_R_asso": {"zh_CN": "Dzz 联络区 右", "en": "Dzz association R"},

    "rpt.qc.rwm": {"zh_CN": "白质配准相关 r_wm",
                   "en": "White-matter registration r_wm"},
    "rpt.qc.rel_mean": {"zh_CN": "头动 帧间相对位移 均值",
                        "en": "Head motion, frame-to-frame mean"},
    "rpt.qc.rel_max": {"zh_CN": "头动 帧间相对位移 最大",
                       "en": "Head motion, frame-to-frame max"},
    "rpt.qc.abs_mean": {"zh_CN": "头动 绝对位移 均值",
                        "en": "Head motion, absolute mean"},
    "rpt.qc.abs_max": {"zh_CN": "头动 绝对位移 最大",
                       "en": "Head motion, absolute max"},
    "rpt.qc.outlier_n": {"zh_CN": "离群体积数", "en": "Outlier volumes"},
    "rpt.qc.verdict": {"zh_CN": "质控判定", "en": "QC verdict"},
    "rpt.qc.regqc_range": {"zh_CN": "配准稳健性 regqc 极差（%）",
                           "en": "Registration robustness regqc range (%)"},
    "rpt.qc.regqc_maxdev": {"zh_CN": "配准稳健性 最大偏离（%）",
                            "en": "Registration robustness max deviation (%)"},
    "rpt.qc.regqc_level": {"zh_CN": "配准稳健性判定",
                           "en": "Registration robustness verdict"},
    "rpt.qc.t1_alps": {"zh_CN": "【T1 辅助】ALPS", "en": "[T1-assisted] ALPS"},
    "rpt.qc.t1_rwm": {"zh_CN": "【T1 辅助】r_wm", "en": "[T1-assisted] r_wm"},
    "rpt.qc.t1_regqc_range": {"zh_CN": "【T1 辅助】regqc 极差（%）",
                              "en": "[T1-assisted] regqc range (%)"},

    "rpt.table.item": {"zh_CN": "项目", "en": "Item"},
    "rpt.table.value": {"zh_CN": "值", "en": "Value"},
    "rpt.sub.generated": {"zh_CN": "由 ALPSbox 自动生成 · %s",
                          "en": "Generated automatically by ALPSbox · %s"},

    # ================= Single-subject report: headings and notes ===========
    "rpt.h.results": {"zh_CN": "一、结果", "en": "1. Results"},
    "rpt.h.verdict": {"zh_CN": "二、结论与判读",
                      "en": "2. Conclusion and interpretation"},
    "rpt.h.diffusivity": {"zh_CN": "三、八个扩散率分量（×10⁻³ mm²/s）",
                          "en": "3. Eight diffusivity components "
                                "(×10⁻³ mm²/s)"},
    "rpt.h.qc": {"zh_CN": "四、质控", "en": "4. Quality control"},
    "rpt.h.images": {"zh_CN": "五、图像", "en": "5. Images"},
    "rpt.h.method": {"zh_CN": "六、方法与处理口径",
                     "en": "6. Methods and processing settings"},
    "rpt.h.refs": {"zh_CN": "七、引用与第三方来源",
                   "en": "7. References and third-party sources"},

    "rpt.note.no_threshold": {
        "zh_CN": "说明：ALPS 目前尚无公认的诊断阈值，上述参考区间仅用于判断数值是否合理，"
                 "不构成临床诊断。",
        "en": "Note: ALPS has no accepted diagnostic threshold; the reference "
              "ranges above only indicate whether a value is plausible and are "
              "not a clinical diagnosis."},
    "rpt.method.block": {
        "zh_CN": "ALPS = mean(Dxx_proj, Dxx_asso) / mean(Dyy_proj, Dzz_asso)\n"
                 "\n"
                 "ROI：JHU-ICBM-FA-1mm 模板上 2.5 mm 半径球，每区 81 体素\n"
                 "     （与 Taoka 2017 原文的 5 mm 直径一致）\n"
                 "配准：FA → %s，flirt 12 DOF，代价函数 %s\n"
                 "张量重定向：vecreg（T' = R·T·Rᵀ，Alexander 2001；Tatekawa 2023）\n"
                 "去 Gibbs 振铃：%s    去噪（dwidenoise）：%s    bet -f：%s\n",
        "en": "ALPS = mean(Dxx_proj, Dxx_asso) / mean(Dyy_proj, Dzz_asso)\n"
              "\n"
              "ROI: 2.5 mm radius spheres on the JHU-ICBM-FA-1mm template, "
              "81 voxels per region\n"
              "     (matching the 5 mm diameter of the original Taoka 2017 "
              "paper)\n"
              "Registration: FA → %s, flirt 12 DOF, cost function %s\n"
              "Tensor reorientation: vecreg (T' = R·T·Rᵀ, Alexander 2001; "
              "Tatekawa 2023)\n"
              "Gibbs unringing: %s    denoising (dwidenoise): %s    "
              "bet -f: %s\n"},
    "rpt.note.method": {
        "zh_CN": "以上为本次结果的实际处理口径；与其它研究比较时请先核对全部参数。"
                 "ALPS 对预处理参数（脑提取阈值、配准代价、模板、去噪等）敏感，"
                 "不同口径的结果不应直接混比。",
        "en": "These are the processing settings actually used for this result; "
              "check every parameter before comparing with other studies. ALPS "
              "is sensitive to preprocessing (brain-extraction threshold, "
              "registration cost, template, denoising, etc.), and results from "
              "different definitions should not be mixed directly."},
    "rpt.note.term": {
        "zh_CN": "术语：本工具所称「参考实现」（旧文档中叫「官方 alps.sh」）专指 "
                 "gbarisano/alps；ALPS 没有官方标准实现。",
        "en": "Terminology: 'reference implementation' in this tool means "
              "gbarisano/alps specifically (called 'official alps.sh' in older "
              "documentation); ALPS has no official standard implementation."},

    # ================= Figure captions =====================================
    # Matches the image filenames collected by cli.py.
    "rpt.caption.roi": {"zh_CN": "ROI 位置", "en": "ROI position"},
    "rpt.caption.motion": {"zh_CN": "头动曲线", "en": "Motion traces"},

    # ================= Batch report ========================================
    # Counts and a per-subject table only; no group-level statistics.
    "rpt.title.batch": {"zh_CN": "ALPS 批量分析报告",
                        "en": "ALPS batch analysis report"},
    "rpt.batch.failed": {"zh_CN": "失败", "en": "Failed"},
    "rpt.batch.th_subject": {"zh_CN": "被试", "en": "Subject"},
    "rpt.batch.th_qc": {"zh_CN": "质控", "en": "QC"},
    "rpt.batch.th_conclusion": {"zh_CN": "结论", "en": "Verdict"},
    "rpt.batch.count": {"zh_CN": "被试数 %d（成功 %d）",
                        "en": "Subjects %d (succeeded %d)"},
    "rpt.h.summary": {"zh_CN": "汇总", "en": "Summary"},
    "rpt.h.per_subject": {"zh_CN": "逐被试结果",
                          "en": "Per-subject results"},
}

register_strings(STRINGS)
