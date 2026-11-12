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
    "rpt.h.qc": {"zh_CN": "四、质控结果", "en": "4. QC results"},
    "rpt.h.qc_params": {"zh_CN": "五、当前质控参数",
                        "en": "5. Current QC parameters"},
    "rpt.h.qc_figs": {"zh_CN": "六、质控图", "en": "6. QC figures"},
    "rpt.h.images": {"zh_CN": "六、质控图", "en": "6. QC figures"},
    "rpt.h.method": {"zh_CN": "七、方法与处理口径",
                     "en": "7. Methods and processing settings"},
    "rpt.h.refs": {"zh_CN": "八、引用与第三方来源",
                   "en": "8. References and third-party sources"},

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
                 "去 Gibbs 振铃：%s    去噪（dwidenoise）：%s    bet -f：%s\n"
                 "TOPUP 畸变校正（双相位编码）：%s\n",
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
              "bet -f: %s\n"
              "TOPUP distortion correction (dual phase encoding): %s\n"},
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
    "rpt.caption.motion": {"zh_CN": "头动时间曲线",
                           "en": "Motion time course"},
    "rpt.caption.reg": {"zh_CN": "配准后 FA 与 ROI 位置",
                        "en": "Registered FA and ROI placement"},

    # ================= QC detail, thresholds and figures ====================
    "rpt.qc.overall": {"zh_CN": "本次质控判定：%s",
                       "en": "QC verdict: %s"},
    "rpt.qc.issues": {"zh_CN": "需要关注：%s",
                      "en": "Needs attention: %s"},
    "rpt.qc.no_issues": {"zh_CN": "没有发现需要关注的问题。",
                         "en": "No issues need attention."},
    "rpt.qc.th_check": {"zh_CN": "检查项", "en": "Check"},
    "rpt.qc.th_value": {"zh_CN": "结果", "en": "Result"},
    "rpt.qc.th_level": {"zh_CN": "等级", "en": "Level"},
    "rpt.qc.th_detail": {"zh_CN": "完整解释 / 建议",
                         "en": "Full explanation / advice"},
    "rpt.qc.advice": {"zh_CN": "建议：", "en": "Advice: "},
    "rpt.qc.note": {
        "zh_CN": "质控结果按生成本报告时的当前阈值重新计算；若结果文件来自旧版本，"
                 "文件里记录的 qc 字段可能不同。",
        "en": "QC results are re-evaluated with the thresholds current when "
              "this report was generated; a qc value stored by an older "
              "result file may differ."},
    "rpt.qc.threshold_source": {
        "zh_CN": "阈值可在界面的 QC 页修改（保存于 ~/.alpsbox/qc_config.json）；"
                 "未修改时使用默认值。",
        "en": "Thresholds can be edited on the QC page (saved to "
              "~/.alpsbox/qc_config.json); the defaults are used when "
              "unchanged."},

    "rpt.qp.th_param": {"zh_CN": "参数", "en": "Parameter"},
    "rpt.qp.th_value": {"zh_CN": "当前值", "en": "Current value"},
    "rpt.qp.th_explain": {"zh_CN": "全称与完整解释",
                          "en": "Full name and explanation"},
    "rpt.qp.roi_voxels": {"zh_CN": "ROI 体素数（roi_voxels）",
                          "en": "ROI voxel count (roi_voxels)"},
    "rpt.qp.strict": {"zh_CN": "严格模式", "en": "strict mode"},
    "rpt.qp.roi_voxels_exp": {
        "zh_CN": "每个 2.5 mm ROI 在 JHU 模板空间的体素数；期望 81。"
                 "偏离说明模板空间、ROI 半径或自定义 ROI 不一致；严格模式开启时判为需注意。",
        "en": "Voxels per 2.5 mm ROI in JHU template space; 81 expected. "
              "A deviation means inconsistent template space, ROI radius or "
              "custom ROI; flagged when strict mode is on."},
    "rpt.qp.rwm": {"zh_CN": "白质配准相关 r_wm（通过 / 失败阈值）",
                   "en": "White-matter registration r_wm (pass / fail)"},
    "rpt.qp.rwm_exp": {
        "zh_CN": "注册后 FA 与 JHU 模板的相关系数（fslcc），越高越好。"
                 "≥通过阈值为通过，<失败阈值为不合格，介于两者为提示/需注意。",
        "en": "Correlation between registered FA and the JHU template "
              "(fslcc); higher is better. ≥ pass threshold = pass, < fail "
              "threshold = fail, in between = info / check."},
    "rpt.qp.rel": {"zh_CN": "帧间相对位移 warn / fail（均值）",
                   "en": "Frame-wise relative motion warn / fail (mean)"},
    "rpt.qp.rel_exp": {
        "zh_CN": "相对上一帧的头动（mm）；不随扫描时长累积，"
                 "适合跨被试、跨协议比较，是头动判定的主指标。",
        "en": "Motion relative to the previous volume (mm); does not "
              "accumulate with scan duration, suitable for comparison across "
              "subjects/protocols and used as the primary motion criterion."},
    "rpt.qp.relmax": {"zh_CN": "帧间相对位移 warn / fail（最大值）",
                      "en": "Frame-wise relative motion warn / fail (max)"},
    "rpt.qp.relmax_exp": {
        "zh_CN": "逐帧计算后取最大值；对单帧大运动更敏感。",
        "en": "Maximum over volumes; more sensitive to a single large movement."},
    "rpt.qp.abs": {"zh_CN": "绝对位移 warn / fail（均值）",
                   "en": "Absolute motion warn / fail (mean)"},
    "rpt.qp.abs_exp": {
        "zh_CN": "相对第 1 个 volume 的漂移（mm）；会随扫描时长累积，"
                 "只作参考，跨协议比较需谨慎。",
        "en": "Drift relative to volume 1 (mm); accumulates with scan "
              "duration, reference only; compare across protocols with care."},
    "rpt.qp.absmax": {"zh_CN": "绝对位移 warn / fail（最大值）",
                      "en": "Absolute motion warn / fail (max)"},
    "rpt.qp.absmax_exp": {
        "zh_CN": "绝对位移的最大值；用于发现单次大漂移。",
        "en": "Maximum absolute displacement; flags a single large drift."},
    "rpt.qp.outlier": {"zh_CN": "离群切片比例 warn / fail",
                       "en": "Outlier-slice ratio warn / fail"},
    "rpt.qp.outlier_exp": {
        "zh_CN": "eddy --repol 判定的离群切片数 / 体积数；"
                 "比例越高说明越多切片被替换，应结合运动指标一起看。",
        "en": "Outlier slices flagged by eddy --repol divided by number of "
              "volumes; higher means more slices replaced; read together with "
              "motion metrics."},
    "rpt.qp.alps": {"zh_CN": "ALPS 合理范围",
                    "en": "ALPS plausible range"},
    "rpt.qp.alps_exp": {
        "zh_CN": "超出该范围判为需注意，用于发现异常值；不是诊断阈值。",
        "en": "Outside this range = check; used to flag implausible values, "
              "not a diagnostic threshold."},
    "rpt.qp.flags": {"zh_CN": "严格 ROI / eddy_correct 标记",
                     "en": "Strict ROI / eddy_correct flags"},
    "rpt.qp.flags_exp": {
        "zh_CN": "严格 ROI：按 81 体素判定；eddy_correct：不重定向张量、"
                 "存在已知 MD/FA 低估偏差，计入需注意。",
        "en": "Strict ROI: compare with 81 voxels; eddy_correct: no tensor "
              "reorientation and a known MD/FA underestimation bias, flagged "
              "as check."},
    "rpt.qc.regqc_check": {"zh_CN": "配准稳健性 regqc",
                           "en": "Registration robustness regqc"},
    "rpt.qc.regqc_value": {"zh_CN": "极差 %.2f%%；最大偏离 %.2f%%",
                           "en": "range %.2f%%; max deviation %.2f%%"},
    "rpt.qc.regqc_detail": {
        "zh_CN": "12 次 ±0.5° / 0.5 mm 配准矩阵扰动下 ALPS 的变化范围；"
                 "阈值 <6% 通过、6–10% 提示、>10% 需注意。",
        "en": "ALPS range under 12 perturbations of the registration matrix "
              "(±0.5° / 0.5 mm); thresholds <6% pass, 6–10% info, >10% "
              "check."},
    "rpt.qc.issue_sep": {"zh_CN": "；", "en": "; "},
    "rpt.qp.regqc": {"zh_CN": "regqc 判定带（扰动 ±0.5° / 0.5 mm）",
                     "en": "regqc bands (perturbation ±0.5° / 0.5 mm)"},
    "rpt.qp.regqc_exp": {
        "zh_CN": "对配准矩阵做 12 次小扰动，量化每个被试的 ALPS 极差："
                 "<6% 通过；6–10% 提示；>10% 需注意。"
                 "该指标直接衡量结果对配准误差的敏感度。",
        "en": "Perturbs the registration matrix 12 times and measures the "
              "per-subject ALPS range: <6% pass; 6–10% info; >10% check. "
              "It directly measures sensitivity to registration error."},
    "rpt.on": {"zh_CN": "开", "en": "on"},
    "rpt.off": {"zh_CN": "关", "en": "off"},
    "rpt.fig.motion_note": {
        "zh_CN": "上图为相对第 1 个 volume 的绝对位移，下图为帧间相对位移；"
                 "红带为 eddy 判定的离群切片，虚线为当前 warn/fail 阈值。",
        "en": "Top: absolute displacement relative to volume 1; bottom: "
              "frame-wise relative displacement. Red bands mark eddy outlier "
              "slices; dashed lines are the current warn/fail thresholds."},
    "rpt.fig.reg_note": {
        "zh_CN": "背景为配准到模板空间的 FA（FA_in_mni），彩色为四个 2.5 mm ROI；"
                 "用于检查 FA→模板配准与 ROI 落位，而不是只看相关数字。",
        "en": "Background: FA warped to template space (FA_in_mni); coloured "
              "overlays: the four 2.5 mm ROIs. Used to inspect FA→template "
              "registration and ROI placement, not only the correlation "
              "number."},
    "rpt.fig.none": {
        "zh_CN": "未生成质控图（缺少 FA_in_mni 或 eddy 运动文件）。",
        "en": "No QC figure was generated (FA_in_mni or eddy motion file is "
              "missing)."},
    "rpt.batch.th_rwm": {"zh_CN": "r_wm", "en": "r_wm"},
    "rpt.batch.th_rel": {"zh_CN": "帧间位移 均值/最大 (mm)",
                         "en": "Frame-wise motion mean/max (mm)"},
    "rpt.batch.th_outlier": {"zh_CN": "离群切片",
                             "en": "Outlier slices"},
    "rpt.batch.th_method": {"zh_CN": "校正方法", "en": "Correction"},
    "rpt.batch.th_issues": {"zh_CN": "质控问题", "en": "QC issues"},
    "rpt.batch.qc_note": {
        "zh_CN": "本报告只给出逐被试结果与质控，不做组间统计；"
                 "组水平分析请在导出 CSV/JSON 后用统计软件完成。",
        "en": "This report gives per-subject results and QC only; no "
              "group-level statistics. Analyse the exported CSV/JSON "
              "downstream."},

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
    "rpt.h.qc_details": {"zh_CN": "逐被试质控详情（点击展开）",
                         "en": "Per-subject QC details (click to expand)"},
    "rpt.batch.details_hint": {
        "zh_CN": "每个展开项包含该被试的完整质控检查、解释与可用的质控图。",
        "en": "Each entry contains the subject's full QC check table, "
              "explanations and any available QC figures."},
}

register_strings(STRINGS)
