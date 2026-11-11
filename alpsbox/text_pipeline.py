# -*- coding: utf-8 -*-
"""Bilingual (zh_CN / en) text for the processing pipeline, batch runs and
rescan (registered in i18n.STRINGS).

Covers every user-visible string in pipeline.py (per-step log lines, warnings,
RuntimeError messages, T1 / TOPUP / regqc output), batch.py (batch progress and
the full qc_report.txt) and rescan.py (rescan QC summary). The Chinese values
are the reference text (regression tests assert on them); the English values
are their translations.

qc_report.txt keeps only per-subject QC warnings plus the necessary counts
(total / failure list / method distribution); group-level descriptive
statistics such as cohort mean/SD/range are intentionally out of scope, so no
strings exist for them here.

Conventions
-----------
* The values carry their own indentation and bracketed log-level prefixes so
  the log layout is unchanged; English uses terse engineering markers such as
  ``[warn]`` / ``[note]`` / ``[skip]`` in place of the Chinese ones.
* Technical terms, file names, commands and method labels (eddy_gpu,
  eddy_correct, dtifit, vecreg, bvec, FSL, MRtrix3, TOPUP, regqc,
  bet -f 0.5 ...) are reproduced verbatim, never translated.
* Placeholders keep the same type, order and count as the Chinese original.
"""
from .i18n import register_strings

STRINGS = {
    # ================= pipeline.py: inputs and preprocessing =================
    "pipe.fsl_dir_unset": {
        "zh_CN": "FSLDIR 未设置",
        "en": "FSLDIR is not set"},
    "pipe.err_no_template": {
        "zh_CN": "找不到 JHU-ICBM-FA-1mm 模板: %s\n"
                 "  该图谱随 FSL 分发（位于 $FSLDIR/data/atlases/JHU/）。\n"
                 "  若你的 FSL 未安装 atlas，请运行 $FSLDIR/bin/fsl_install_atlases 或手动下载。",
        "en": "JHU-ICBM-FA-1mm template not found: %s\n"
              "  This atlas ships with FSL (in $FSLDIR/data/atlases/JHU/).\n"
              "  If your FSL has no atlases, run $FSLDIR/bin/fsl_install_atlases or download it manually."},
    "pipe.warn_line": {
        "zh_CN": "      [警告] %s",
        "en": "      [warn] %s"},
    "pipe.step.input": {
        "zh_CN": "    [0] 输入",
        "en": "    [0] Input"},
    "pipe.n_vol": {
        "zh_CN": "        体积数: %d",
        "en": "        Volumes: %d"},

    # ---- denoising / unringing / eddy ----
    "pipe.denoise_skip": {
        "zh_CN": "    [0.5] 去噪: 跳过（未找到 dwidenoise）",
        "en": "    [0.5] Denoise: skipped (dwidenoise not found)"},
    "pipe.denoise_run": {
        "zh_CN": "    [0.5] 去噪 (dwidenoise)",
        "en": "    [0.5] Denoise (dwidenoise)"},
    "pipe.unring_skip_no_mrtrix": {
        "zh_CN": "    [1] 去振铃: 跳过（未安装 MRtrix3）",
        "en": "    [1] Unringing: skipped (MRtrix3 not installed)"},
    "pipe.unring_run": {
        "zh_CN": "    [1] 去 Gibbs 振铃 (mrdegibbs)",
        "en": "    [1] Gibbs unringing (mrdegibbs)"},
    "pipe.unring_skip_opt": {
        "zh_CN": "    [1] 去振铃: 按参数跳过",
        "en": "    [1] Unringing: skipped by option"},
    "pipe.eddy_run": {
        "zh_CN": "    [2] 涡流+运动校正",
        "en": "    [2] Eddy-current + motion correction"},
    "pipe.eddy_cached": {
        "zh_CN": "    [2] 已有 dwi_eddy.nii.gz，跳过校正",
        "en": "    [2] dwi_eddy.nii.gz exists, skipping correction"},
    "pipe.err_bvec_missing": {
        "zh_CN": "缺少旋转后的 bvec：%s",
        "en": "rotated bvec is missing: %s"},
    "pipe.step.bet": {
        "zh_CN": "    [3] 脑提取 (bet)",
        "en": "    [3] Brain extraction (bet)"},
    "pipe.step.dtifit": {
        "zh_CN": "    [4] 张量拟合 (dtifit --save_tensor)",
        "en": "    [4] Tensor fitting (dtifit --save_tensor)"},
    "pipe.err_no_tensor": {
        "zh_CN": "dtifit 未生成张量: %s",
        "en": "dtifit produced no tensor: %s"},
    "pipe.step.flirt": {
        "zh_CN": "    [5] FA 配准到模板 (flirt 12 DOF, cost=%s)",
        "en": "    [5] Registering FA to template (flirt 12 DOF, cost=%s)"},
    "pipe.step.vecreg": {
        "zh_CN": "    [6] ★张量重定向 (vecreg, T' = R·T·Rᵀ)",
        "en": "    [6] ★Tensor reorientation (vecreg, T' = R·T·Rᵀ)"},
    "pipe.step.roi": {
        "zh_CN": "    [7] ROI",
        "en": "    [7] ROI"},
    "pipe.err_roi_empty": {
        "zh_CN": "以下 ROI 为空，配准可能失败: %s",
        "en": "these ROIs are empty, registration probably failed: %s"},
    "pipe.roi_voxels": {
        "zh_CN": "        体素数: %s",
        "en": "        Voxels: %s"},
    "pipe.step.fslstats": {
        "zh_CN": "    [8] ROI 内分量均值 (fslstats -k -m)",
        "en": "    [8] Mean tensor components inside ROIs (fslstats -k -m)"},

    # ---- T1-assisted registration (paired comparison, experimental) ----
    "pipe.step.t1": {
        "zh_CN": "    [9.7] T1 辅助配准（FA→T1→JHU-FA 复合变换）",
        "en": "    [9.7] T1-assisted registration (FA→T1→JHU-FA composite)"},
    "pipe.t1_skip_missing": {
        "zh_CN": "        跳过：T1 文件不存在: %s",
        "en": "        [skip] T1 file not found: %s"},
    "pipe.t1_mat_preset": {
        "zh_CN": "        T1→模板 使用预计算矩阵: %s",
        "en": "        T1→template uses the precomputed matrix: %s"},
    "pipe.t1_fail_copy": {
        "zh_CN": "        失败：读取 --t1-mat %s",
        "en": "        failed: reading --t1-mat %s"},
    "pipe.t1_warn_no_mat": {
        "zh_CN": "        [警告] 未提供 --t1-mat，现场做直接跨模态配准"
                 "（易收敛失败，建议提供预计算矩阵）",
        "en": "        [warn] no --t1-mat given, running a direct cross-modal "
              "registration (may fail to converge; a precomputed matrix is "
              "recommended)"},
    "pipe.t1_fail_flirt": {
        "zh_CN": "        失败：配准未生成矩阵",
        "en": "        failed: registration produced no matrix"},
    "pipe.t1_fail_compose": {
        "zh_CN": "        失败：矩阵复合 %s",
        "en": "        failed: matrix composition %s"},
    "pipe.t1_fail_alps": {
        "zh_CN": "        失败：ALPS %s",
        "en": "        failed: ALPS %s"},
    "pipe.t1_regqc_skip": {
        "zh_CN": "        regqc(T1) 跳过：%s",
        "en": "        regqc(T1) skipped: %s"},
    "pipe.t1_done": {
        "zh_CN": "        T1 辅助: ALPS_t1=%.6f（S1=%.6f）  r_wm_t1=%.4f",
        "en": "        T1-assisted: ALPS_t1=%.6f (S1=%.6f)  r_wm_t1=%.4f"},
    "pipe.t1_regqc": {
        "zh_CN": "        T1 regqc: 极差 %.2f%%（S1: %.2f%%）",
        "en": "        T1 regqc: range %.2f%% (S1: %.2f%%)"},

    # ---- registration robustness QC (regqc) ----
    "pipe.step.regqc": {
        "zh_CN": "    [9.5] 配准稳健性质控（12 次矩阵扰动）",
        "en": "    [9.5] Registration robustness QC (12 matrix perturbations)"},
    "pipe.regqc_skip_import": {
        "zh_CN": "        跳过：regqc 模块导入失败（%s）",
        "en": "        [skip] cannot import the regqc module (%s)"},
    "pipe.regqc_skip_roi": {
        "zh_CN": "        跳过：ROI 不完整",
        "en": "        [skip] incomplete ROIs"},
    "pipe.regqc_skip": {
        "zh_CN": "        跳过：%s",
        "en": "        [skip] %s"},
    "pipe.regqc_base": {
        "zh_CN": "        ALPS 基准 %.4f，扰动下范围 [%.4f, %.4f]",
        "en": "        ALPS baseline %.4f, perturbed range [%.4f, %.4f]"},
    "pipe.regqc_summary": {
        "zh_CN": "        极差 %.2f%%  最大偏离 %.2f%%  → %s（%s）",
        "en": "        Range %.2f%%  max deviation %.2f%%  → %s (%s)"},

    # ================= pipeline.py: eddy branch =================
    "pipe.acqp_warn": {
        "zh_CN": "        [警告] 无法生成 acqp: %s",
        "en": "        [warn] cannot build acqp: %s"},
    "pipe.acqp_fallback": {
        "zh_CN": "        -> 回落 eddy_correct",
        "en": "        -> falling back to eddy_correct"},
    "pipe.eddy_done_tag": {
        "zh_CN": "        eddy 完成（%s%s）",
        "en": "        eddy done (%s%s)"},
    "pipe.eddy_done_gpu": {
        "zh_CN": "        eddy 完成（%s + --repol）",
        "en": "        eddy done (%s + --repol)"},
    "pipe.eddy_not_shelled": {
        "zh_CN": "        [检测到 Data not shelled] 用 --data_is_shelled 重试",
        "en": "        [Data not shelled detected] retrying with --data_is_shelled"},
    "pipe.eddy_warn_gpu_fallback": {
        "zh_CN": "        [警告] %s 失败，回落 CPU 版 eddy",
        "en": "        [warn] %s failed, falling back to CPU eddy"},
    "pipe.eddy_done_cpu": {
        "zh_CN": "        eddy 完成（CPU + --repol）",
        "en": "        eddy done (CPU + --repol)"},
    "pipe.eddy_warn_fallback": {
        "zh_CN": "        [警告] eddy 失败，回落 eddy_correct",
        "en": "        [warn] eddy failed, falling back to eddy_correct"},
    "pipe.eddy_correct_note": {
        "zh_CN": "        ⚠ 注意：eddy_correct 有已知偏差（MD/FA 会被低估）",
        "en": "        ⚠ note: eddy_correct has known bias (MD underestimated "
              "by ~6.6%, FA by ~10%)"},
    "pipe.eddy_no_json": {
        "zh_CN": "        [注意] 无可用 json，无法做完整 eddy",
        "en": "        [note] no usable json, so full eddy is not possible"},

    # ---- TOPUP ----
    "pipe.topup_cached_stale": {
        "zh_CN": "        TOPUP: 已有结果未包含 TOPUP，重新处理",
        "en": "        TOPUP: cached result has no TOPUP; re-running"},
    "pipe.topup_reuse": {
        "zh_CN": "        TOPUP: 已有结果，复用",
        "en": "        TOPUP: existing result reused"},
    "pipe.topup_skip": {
        "zh_CN": "        TOPUP: 跳过（%s）",
        "en": "        TOPUP: skipped (%s)"},
    "pipe.topup_skip_cfg": {
        "zh_CN": "        TOPUP: 跳过（找不到 b02b0.cnf 配置）",
        "en": "        TOPUP: skipped (b02b0.cnf config not found)"},
    "pipe.topup_cfg": {
        "zh_CN": "        TOPUP: 使用配置 %s",
        "en": "        TOPUP: using config %s"},
    "pipe.topup_cfg_missing": {
        "zh_CN": "        TOPUP: 跳过（指定的配置不存在: %s）",
        "en": "        TOPUP: skipped (specified config not found: %s)"},
    "pipe.topup_start": {
        "zh_CN": "        TOPUP: 双相位编码畸变校正",
        "en": "        TOPUP: dual phase-encoding distortion correction"},
    "pipe.topup_pe": {
        "zh_CN": "          第一套 PE = %s，第二套 PE = %s",
        "en": "          PE set 1 = %s, PE set 2 = %s"},
    "pipe.topup_fail": {
        "zh_CN": "        TOPUP: 失败，继续用单相位编码流程",
        "en": "        TOPUP: failed, continuing with the single phase-encoding path"},
    "pipe.topup_done": {
        "zh_CN": "        TOPUP: 完成（%s）",
        "en": "        TOPUP: done (%s)"},

    # ---- eddy failure diagnostics ----
    "pipe.eddy_diag_head": {
        "zh_CN": "        ---- %s 失败诊断 (exit=%d) ----",
        "en": "        ---- %s failure diagnostics (exit=%d) ----"},
    "pipe.eddy_diag_reason": {
        "zh_CN": "        原因: 参数格式未被识别（FSL eddy 要求 --key=value 等号格式）",
        "en": "        cause: arguments not recognised (FSL eddy requires the "
              "--key=value form)"},

    # ---- eddy_correct / bvec validation ----
    "pipe.err_fdt_rotate": {
        "zh_CN": "需要 fdt_rotate_bvecs 来旋转 bvec（eddy_correct 不自动做）",
        "en": "fdt_rotate_bvecs is required to rotate the bvec "
              "(eddy_correct does not do it automatically)"},
    "pipe.eddy_correct_done": {
        "zh_CN": "        eddy_correct 完成（注意：有已知的 MD/FA 低估偏差）",
        "en": "        eddy_correct done (note: known MD/FA underestimation bias)"},
    "pipe.err_bvec_rows": {
        "zh_CN": "bvec 应有 3 行，实际 %d 行: %s",
        "en": "bvec must have 3 rows, got %d: %s"},
    "pipe.err_bvec_cols": {
        "zh_CN": "bvec 列数(%d) 与体积数(%d) 不一致: %s",
        "en": "bvec has %d columns but there are %d volumes: %s"},
    "pipe.err_bvec_zero": {
        "zh_CN": "bvec 全为 0（旋转失败的表现）: %s",
        "en": "bvec is all zeros (a sign of a failed rotation): %s"},

    # ================= pipeline.py: QC output =================
    "pipe.step.qc": {
        "zh_CN": "    [10] 质控",
        "en": "    [10] QC"},
    "pipe.qc_abs": {
        "zh_CN": "        绝对位移 均值=%.3f 最大=%.3f mm",
        "en": "        Displacement from volume 1: mean=%.3f max=%.3f mm"},
    "pipe.qc_rel": {
        "zh_CN": "        相对位移 均值=%.3f 最大=%.3f mm",
        "en": "        Frame-to-frame displacement: mean=%.3f max=%.3f mm"},
    "pipe.qc_outlier": {
        "zh_CN": "        离群切片 %d 条",
        "en": "        Outlier slices: %d"},

    # ================= batch.py: batch progress =================
    "pipe.batch.start": {
        "zh_CN": "\n[%d/%d] %s 开始",
        "en": "\n[%d/%d] %s starting"},

    # ================= batch.py：qc_report.txt =================
    "pipe.qcr.title": {
        "zh_CN": " ALPSbox 质控报告   %s",
        "en": " ALPSbox QC report   %s"},
    "pipe.qcr.total": {
        "zh_CN": "  总数 %d   成功 %d   失败 %d",
        "en": "  Total %d   OK %d   Failed %d"},
    "pipe.qcr.failed": {
        "zh_CN": " 失败清单",
        "en": " Failures"},
    "pipe.qcr.methods": {
        "zh_CN": " 校正方法分布",
        "en": " Correction methods"},
    "pipe.qcr.topup": {
        "zh_CN": " TOPUP 双相位编码畸变校正",
        "en": " TOPUP dual phase-encoding distortion correction"},
    "pipe.qcr.topup_line": {"zh_CN": "  %-26s %d", "en": "  %-26s %d"},
    "pipe.qcr.warnings": {
        "zh_CN": " 质控告警",
        "en": " QC warnings"},
    "pipe.qcr.warn_subject": {
        "zh_CN": "  [注意] %s",
        "en": "  [note] %s"},
    "pipe.qcr.warn_roi": {
        "zh_CN": "ROI %s 体素数=%d（期望 %d）",
        "en": "ROI %s voxels=%d (expected %d)"},
    "pipe.qcr.warn_rwm": {
        "zh_CN": "r_wm=%.3f < %.2f（配准可能有问题）",
        "en": "r_wm=%.3f < %.2f (registration may be off)"},
    "pipe.qcr.warn_rms": {
        "zh_CN": "运动过大 RMS_max=%.2f mm > %.1f",
        "en": "excess motion RMS_max=%.2f mm > %.1f"},
    "pipe.qcr.no_warn": {
        "zh_CN": "  无（全部通过）",
        "en": "  none (all passed)"},

    # ================= rescan.py: rescan QC summary =================
    "pipe.rescan.scanned": {
        "zh_CN": "扫描到 %d 个被试，其中 %d 个有可用头动数据",
        "en": "Scanned %d subjects, %d with usable motion data"},
    "pipe.rescan.stat": {
        "zh_CN": "均值 %.3f 最大 %.3f 中位 %.3f",
        "en": "mean %.3f max %.3f median %.3f"},
    "pipe.rescan.abs_line": {
        "zh_CN": "绝对位移（相对参考卷，mm）: %s",
        "en": "Displacement from reference volume (mm): %s"},
    "pipe.rescan.rel_line": {
        "zh_CN": "相对位移（相对前卷，  mm）: %s",
        "en": "Frame-to-frame displacement (mm): %s"},
    "pipe.rescan.abs_dist": {
        "zh_CN": "绝对位移最大值分布:",
        "en": "Distribution of max displacement from reference volume:"},
    "pipe.rescan.rel_dist": {
        "zh_CN": "相对位移最大值分布:",
        "en": "Distribution of max frame-to-frame displacement:"},
    "pipe.rescan.pct": {
        "zh_CN": "  %3d%% 分位 = %.3f mm",
        "en": "  %3d%% percentile = %.3f mm"},
}

register_strings(STRINGS)
