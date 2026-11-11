# -*- coding: utf-8 -*-
"""Bilingual (zh_CN / en) text for the CLI, environment checks, input
discovery, the FSL wrapper and registration QC.

This module centralises every user-visible string from ``cli.py``,
``config.py``, ``inputs.py``, ``fsl.py``, ``acqp.py`` and ``regqc.py``
(CLI help, print and error messages, environment-check output, exception
text) and registers them in the :mod:`alpsbox.i18n` STRINGS table.

Conventions
-----------
* Key prefixes: ``cli.`` is used only by the command-line entry point,
  ``misc.`` is shared by the remaining library modules.
* The Chinese values are the reference text (regression tests assert on
  them); the English values are their translations. Placeholders
  (%s / %d / %.3f / %-20s) keep the same type, order and count as the
  Chinese original in every entry.
* Technical terms, CLI option names, paths, FSL / MRtrix3 terminology and
  file suffixes are reproduced verbatim, never translated.
* Log level prefixes and indentation (for example the bracketed "note",
  "error" and "skip" markers) are preserved in both languages; the English
  values use terse engineering markers such as
  ``[warn]`` / ``[error]`` / ``[skip]`` / ``[note]``.
"""
from .i18n import register_strings

STRINGS = {
    # =================================================================
    # cli.py -- top-level description, subcommands and option help
    # =================================================================
    "cli.description": {
        "zh_CN": "ALPSbox —— DTI-ALPS 自动化处理工具箱 (v%s)",
        "en": "ALPSbox — automated DTI-ALPS processing toolbox (v%s)"},
    "cli.epilog": {
        "zh_CN": "命令行入口。\n"
                 "\n"
                 "用法示例\n"
                 "--------\n"
                 "    # 环境自检\n"
                 "    alpsbox check\n"
                 "\n"
                 "    # 单被试\n"
                 "    alpsbox run /path/to/sub_001 --out ./results/sub_001\n"
                 "\n"
                 "    # 批量（根目录下每个子文件夹一个被试）\n"
                 "    alpsbox batch /path/to/cohort --out ./results --workers 1\n"
                 "\n"
                 "    # 只看输入能不能找到，不跑\n"
                 "    alpsbox dryrun /path/to/cohort\n"
                 "\n"
                 "引用与第三方来源\n"
                 "----------------\n"
                 "ALPS 方法：Taoka T, et al. Japanese Journal of Radiology.\n"
                 "2017;35(4):172-178. doi:10.1007/s11604-017-0617-z\n"
                 "\n"
                 "「参考实现」（旧称「官方 alps.sh」）专指开源仓库 gbarisano/alps\n"
                 "（https://github.com/gbarisano/alps，commit e6f58e7，2025-09-12，\n"
                 "MIT License）；其要求的配套论文：Liu X, Barisano G, et al.\n"
                 "Aging and Disease. 2024;15(4):1885-1898. doi:10.14336/AD.2023.0321-2\n"
                 "（ALPS 没有官方标准实现；本工具不打包、不修改该仓库代码，\n"
                 "随包 ROI 掩膜复制自该仓库，MIT License）。\n"
                 "完整引用见仓库 CITATION.cff、docs/CITATIONS.md、\n"
                 "alpsbox/data/ROIs_JHU_ALPS/PROVENANCE.md 与 GUI「帮助 → 参考文献」。\n",
        "en": "Command line entry point.\n"
              "\n"
              "Usage examples\n"
              "--------------\n"
              "    # environment self-check\n"
              "    alpsbox check\n"
              "\n"
              "    # single subject\n"
              "    alpsbox run /path/to/sub_001 --out ./results/sub_001\n"
              "\n"
              "    # batch (one subject per subfolder of the root)\n"
              "    alpsbox batch /path/to/cohort --out ./results --workers 1\n"
              "\n"
              "    # only check that the inputs are found; run nothing\n"
              "    alpsbox dryrun /path/to/cohort\n"
              "\n"
              "Citation and third-party provenance\n"
              "-----------------------------------\n"
              "ALPS method: Taoka T, et al. Japanese Journal of Radiology.\n"
              "2017;35(4):172-178. doi:10.1007/s11604-017-0617-z\n"
              "\n"
              "The \"reference implementation\" (the script historically called alps.sh)\n"
              "means only the open-source repository gbarisano/alps\n"
              "(https://github.com/gbarisano/alps, commit e6f58e7, 2025-09-12,\n"
              "MIT License); its required companion paper: Liu X, Barisano G, et al.\n"
              "Aging and Disease. 2024;15(4):1885-1898. doi:10.14336/AD.2023.0321-2\n"
              "(ALPS has no standard reference implementation; this tool neither bundles\n"
              "nor modifies that repository's code, and the bundled ROI masks are copied\n"
              "from it under the MIT License).\n"
              "Full citations: CITATION.cff, docs/CITATIONS.md,\n"
              "alpsbox/data/ROIs_JHU_ALPS/PROVENANCE.md and the GUI \"Help → References\" page.\n"},

    # ---- subcommand descriptions ----
    "cli.cmd.gui": {"zh_CN": "启动图形界面（推荐）",
                    "en": "start the graphical interface (recommended)"},
    "cli.cmd.check": {"zh_CN": "检测 FSL / MRtrix3 / dcm2niix 环境",
                      "en": "check the FSL / MRtrix3 / dcm2niix environment"},
    "cli.cmd.dryrun": {"zh_CN": "只检查输入能否找到，不跑处理",
                       "en": "only check that inputs are found; run nothing"},
    "cli.cmd.run": {"zh_CN": "处理单个被试", "en": "process a single subject"},
    "cli.cmd.batch": {"zh_CN": "批量处理整个队列",
                      "en": "process a whole cohort"},
    "cli.cmd.rescan": {"zh_CN": "从已有 eddy 输出重算头动与离群，不重跑处理",
                       "en": "recompute motion and outliers from existing eddy "
                             "output; no reprocessing"},
    "cli.cmd.report": {"zh_CN": "一键生成 HTML 报告（单例或整批），可用浏览器打印成 PDF",
                       "en": "generate the HTML report (single subject or whole "
                             "batch); printable as PDF in a browser"},

    # ---- positional arguments ----
    "cli.arg.root_batch": {"zh_CN": "队列根目录（每个子目录一个被试）",
                           "en": "cohort root (one subject per subfolder)"},
    "cli.arg.subject_dir": {"zh_CN": "被试目录", "en": "subject folder"},
    "cli.arg.out": {"zh_CN": "输出目录", "en": "output folder"},
    "cli.arg.name": {"zh_CN": "被试 ID（默认取目录名）",
                     "en": "subject ID (default: folder name)"},
    "cli.arg.batch_root": {"zh_CN": "队列根目录", "en": "cohort root"},
    "cli.arg.workers": {"zh_CN": "并行进程数（默认 1；GPU 显存有限，建议 1-2）",
                        "en": "parallel worker processes (default 1; GPU memory "
                              "is limited, 1-2 recommended)"},
    "cli.arg.no_resume": {"zh_CN": "不跳过已完成被试",
                          "en": "do not skip finished subjects"},
    "cli.arg.rescan_root": {"zh_CN": "结果目录（含各被试子目录）",
                            "en": "results folder (contains the subject subfolders)"},
    "cli.arg.json": {"zh_CN": "把重算结果写回各被试的 alps_result.json",
                     "en": "write recomputed values back into each subject's "
                           "alps_result.json"},
    "cli.arg.tsv": {"zh_CN": "要重写的汇总 TSV 路径", "en": "summary TSV to rewrite"},
    "cli.arg.tsv_out": {"zh_CN": "TSV 输出路径（默认原地覆盖）",
                        "en": "TSV output path (default: overwrite in place)"},
    "cli.arg.no_backup": {"zh_CN": "不生成 .bak 备份",
                          "en": "do not create .bak backups"},
    "cli.arg.report_root": {"zh_CN": "结果根目录（含各被试子目录）或单个被试目录",
                            "en": "results root (with subject subfolders) or a "
                                  "single subject folder"},
    "cli.arg.out_html": {"zh_CN": "输出 HTML 路径", "en": "output HTML path"},

    # ---- common options ----
    "cli.opt.fsl_dir": {"zh_CN": "显式指定 FSLDIR", "en": "explicit FSLDIR"},
    "cli.opt.threads": {"zh_CN": "线程数（默认 4）",
                        "en": "number of threads (default 4)"},
    "cli.opt.no_unring": {"zh_CN": "跳过去 Gibbs 振铃",
                          "en": "skip Gibbs unringing"},
    "cli.opt.denoise": {"zh_CN": "启用 dwidenoise 去噪（需 MRtrix3；会在去振铃之前执行）",
                        "en": "enable dwidenoise denoising (needs MRtrix3; runs "
                              "before unringing)"},
    "cli.opt.bet_f": {
        "zh_CN": "bet 脑提取的 -f 阈值（默认 0.5，与 FSL 和 gbarisano/alps.sh 一致；"
                 "0.3 是另一种常用设定，会得到更大的脑掩膜）",
        "en": "bet brain-extraction -f (default 0.5, matching FSL and "
              "gbarisano/alps.sh; 0.3 is another common setting that yields a "
              "larger brain mask)"},
    "cli.opt.reg_cost": {
        "zh_CN": "FA→模板配准的 flirt 代价函数（默认 normmi；"
                 "corratio 是 flirt 默认值，也是 gbarisano/alps.sh 的设定。"
                 "切换会改变配准结果进而改变 ALPS，属高级选项）",
        "en": "flirt cost function for FA→template registration (default normmi; "
              "corratio is the flirt default and what gbarisano/alps.sh uses. "
              "Switching changes the registration and hence ALPS; advanced "
              "option)"},
    "cli.opt.t1": {
        "zh_CN": "结构像辅助配准（实验性）：给已做脑提取的 T1 NIfTI，"
                 "同一次运行里额外用 FA→T1→JHU-FA 复合变换算一遍 ALPS，"
                 "写入 alps_t1 / r_wm_t1 / regqc_t1_*（主结果不受影响）",
        "en": "T1-assisted registration (experimental): pass a brain-extracted "
              "T1 NIfTI and an extra ALPS pass is computed with the composite "
              "FA→T1→JHU-FA transform, written to alps_t1 / r_wm_t1 / "
              "regqc_t1_* (the main result is unaffected)"},
    "cli.opt.t1_mat": {
        "zh_CN": "预计算的 T1→模板 4x4 仿射矩阵（配合 --t1 使用）。"
                 "推荐用 T1→MNI→JHU-FA 的复合矩阵，避免直接跨模态配准跑飞。",
        "en": "precomputed T1→template 4x4 affine (used with --t1). A composite "
              "T1→MNI→JHU-FA matrix is recommended to avoid an unstable direct "
              "cross-modal registration."},
    "cli.opt.regqc": {
        "zh_CN": "配准稳健性质控：对配准矩阵做 12 次微小扰动，"
                 "量化 ALPS 对配准的敏感度（每例约 1-2 分钟）",
        "en": "registration robustness QC: 12 small perturbations of the "
              "registration matrix quantify ALPS sensitivity to registration "
              "(about 1-2 min per subject)"},
    "cli.opt.dwi2": {"zh_CN": "第二套 DWI（必须是相反的相位编码方向，首个 volume 为 b0）",
                     "en": "second DWI (must have the opposite phase-encoding "
                           "direction and a b0 first volume)"},
    "cli.opt.bval2": {"zh_CN": "第二套 DWI 的 bval", "en": "bval of the second DWI"},
    "cli.opt.bvec2": {"zh_CN": "第二套 DWI 的 bvec", "en": "bvec of the second DWI"},
    "cli.opt.json2": {"zh_CN": "第二套 DWI 的 BIDS json",
                      "en": "BIDS json of the second DWI"},
    "cli.opt.topup_auto": {
        "zh_CN": "自动检测 TOPUP：在每个被试文件夹里寻找相位编码方向相反的第二套 DWI，"
                 "找到就启用 TOPUP（批量模式推荐；单被试模式还会检查上级目录中的少量"
                 "相邻文件夹，用于 AP/PA 分文件夹导出的情况）。批量预检会阻止把同一"
                 "被试的 AP/PA 放成两个被试文件夹，并检查配对的一致性",
        "en": "auto-detect TOPUP: look for a second DWI with the opposite "
              "phase-encoding direction in each subject folder and use it for "
              "TOPUP when present (recommended for batch mode; in single-subject "
              "mode a few sibling folders of the same parent are also checked, "
              "for AP/PA exports split across folders). Batch preflight blocks a "
              "layout where one subject's AP/PA are split into two subject "
              "folders, and checks pair consistency"},
    "cli.opt.topup_config": {
        "zh_CN": "TOPUP 配置文件（b02b0.cnf）路径；默认自动在 FSL 安装目录中查找",
        "en": "path to the TOPUP configuration file (b02b0.cnf); by default it "
              "is searched for inside the FSL installation"},
    "cli.opt.radius": {"zh_CN": "自建球 ROI 半径 mm（默认 2.5；仅 --no-bundled-roi 时生效）",
                       "en": "sphere ROI radius in mm (default 2.5; only used "
                             "with --no-bundled-roi)"},
    "cli.opt.no_bundled_roi": {
        "zh_CN": "不用随包参考 ROI（来自 gbarisano/alps，MIT License；"
                 "引用见 docs/CITATIONS.md），改为按坐标生成球。"
                 "旧名 --no-official-roi 保留兼容",
        "en": "do not use the bundled reference ROIs (from gbarisano/alps, MIT "
              "License; citation in docs/CITATIONS.md); generate spheres from "
              "coordinates instead. The legacy name --no-official-roi is still "
              "accepted"},
    "cli.opt.custom_rois": {"zh_CN": "4 个自定义 ROI，逗号分隔，顺序 L_proj,R_proj,L_asso,R_asso",
                            "en": "4 custom ROIs, comma-separated, in the order "
                                  "L_proj,R_proj,L_asso,R_asso"},
    "cli.opt.template": {"zh_CN": "自定义模板路径（默认 JHU-ICBM-FA-1mm）",
                         "en": "custom template path (default JHU-ICBM-FA-1mm)"},
    "cli.opt.no_html": {"zh_CN": "不自动生成 HTML 报告（默认单例/批处理跑完会自动生成）",
                        "en": "do not generate the HTML report automatically (it "
                              "is generated after a single-subject or batch run "
                              "by default)"},
    "cli.opt.force": {"zh_CN": "忽略已有结果，强制重跑",
                      "en": "ignore existing results and re-run"},
    "cli.opt.lang": {"zh_CN": "输出语言（默认英文；auto 等同英文；显式指定不写入偏好）",
                     "en": "output language (default English; auto is an alias "
                           "for English; an explicit value is not saved)"},

    # ---- check ----
    "cli.check.bad": {"zh_CN": "\n环境不满足运行条件，请先修复上面的错误。",
                      "en": "\nEnvironment is not ready; fix the errors above first."},
    "cli.check.ok": {"zh_CN": "\n环境可用。", "en": "\nEnvironment OK."},

    # ---- dryrun ----
    "cli.dryrun.found": {"zh_CN": "\n发现 %d 个被试目录\n",
                         "en": "\n%d subject folders found\n"},
    "cli.dryrun.header": {"zh_CN": " 输入发现结果", "en": " Input discovery result"},
    "cli.dryrun.summary": {"zh_CN": "\n可运行 %d / 共 %d",
                           "en": "\n%d runnable / %d total"},

    # ---- missing numpy notice ----
    "cli.numpy.warn": {
        "zh_CN": "[注意] 当前 python 解释器没有 numpy：%s\n"
                 "       HTML 报告生成将不可用；--regqc 已不依赖 numpy，可正常使用。\n"
                 "       常见原因：PATH 里 MRtrix3 自带的 python3 抢占了系统 python3。\n"
                 "       解决：改用 /usr/bin/python3 -m alpsbox ...，"
                 "或把 MRtrix3 的 bin 放到 PATH 末尾。\n",
        "en": "[warn] the current python interpreter has no numpy: %s\n"
              "       HTML report generation will be unavailable; --regqc no "
              "longer needs numpy and still works.\n"
              "       Common cause: a python3 shipped with MRtrix3 shadows the "
              "system python3 on PATH.\n"
              "       Fix: run /usr/bin/python3 -m alpsbox ... or put MRtrix3's "
              "bin at the end of PATH.\n"},

    # ---- run ----
    "cli.err.discover": {"zh_CN": "\n[错误] 输入发现失败: %s",
                         "en": "\n[error] input discovery failed: %s"},
    "cli.warn.read_json": {"zh_CN": "[警告] 读取 %s 失败: %s",
                           "en": "[warn] cannot read %s: %s"},
    "cli.dual.header": {"zh_CN": "\n第二套 DWI: %s", "en": "\nSecond DWI: %s"},
    "cli.dual.on": {"zh_CN": "启用（%s）", "en": "enabled (%s)"},
    "cli.dual.off": {"zh_CN": "不可用 · ", "en": "unavailable · "},
    "cli.run.subject": {"zh_CN": "\n被试: %s", "en": "\nSubject: %s"},
    "cli.run.outdir": {"zh_CN": "输出目录: %s", "en": "Output folder: %s"},
    "cli.run.verdict": {"zh_CN": " 自动判读: %s", "en": " Automatic reading: %s"},
    "cli.run.report": {"zh_CN": "\n报告: %s（浏览器打开，可打印为 PDF）",
                       "en": "\nReport: %s (open in a browser; printable as PDF)"},
    "cli.warn.report": {"zh_CN": "[提示] 自动报告生成失败（不影响结果）: %s",
                        "en": "[note] automatic report generation failed "
                              "(results unaffected): %s"},

    # ---- batch ----
    "cli.err.no_subdirs": {"zh_CN": "[错误] 在 %s 下没找到任何子目录",
                           "en": "[error] no subfolders found under %s"},
    "cli.batch.found": {"zh_CN": "发现 %d 个被试目录",
                        "en": "%d subject folders found"},
    "cli.batch.skipped": {"zh_CN": "已完成 %d 个，跳过（用 --force 强制重跑）",
                          "en": "%d already done, skipped (use --force to re-run them)"},
    "cli.batch.preflight": {"zh_CN": "输入可用 %d；不可用 %d",
                            "en": "%d inputs usable; %d not usable"},
    "cli.batch.skip_row": {"zh_CN": "  [跳过] %-20s %s",
                           "en": "  [skip] %-20s %s"},
    "cli.batch.all_done": {"zh_CN": " 全部 %d 个被试均已完成，已重新生成汇总表",
                           "en": " All %d subjects are already done; summary "
                                 "tables regenerated"},
    "cli.batch.csv": {"zh_CN": "\n结果表 : %s", "en": "\nResults : %s"},
    "cli.batch.qc": {"zh_CN": "质控   : %s", "en": "QC      : %s"},
    "cli.err.no_good": {"zh_CN": "[错误] 没有任何可用被试",
                        "en": "[error] no usable subject"},
    "cli.batch.done": {"zh_CN": " 批处理完成  用时 %.1f 分钟",
                       "en": " Batch finished in %.1f min"},
    "cli.batch.csv_n": {"zh_CN": "\n结果表 : %s（共 %d 例）",
                        "en": "\nResults : %s (%d subjects)"},
    "cli.batch.report": {"zh_CN": "报告   : %s（浏览器打开，可直接打印为 PDF）",
                         "en": "Report  : %s (open in a browser; printable as PDF)"},

    # ---- rescan ----
    "cli.err.no_dir": {"zh_CN": "[错误] 目录不存在: %s",
                       "en": "[error] folder not found: %s"},
    "cli.rescan.header": {"zh_CN": " 重扫质控  %s", "en": " Rescan QC  %s"},
    "cli.rescan.none": {"zh_CN": "没有找到任何 eddy_movement_rms，确认这是个结果目录吗？",
                        "en": "No eddy_movement_rms found; is this a results folder?"},
    "cli.rescan.json_updated": {"zh_CN": "\n已更新 %d 个 alps_result.json（原文件备份为 .bak）",
                                "en": "\nUpdated %d alps_result.json files "
                                      "(originals backed up as .bak)"},
    "cli.rescan.row_updated": {"zh_CN": "已更新 %d 个 alps_row.txt（原文件备份为 .bak）",
                               "en": "Updated %d alps_row.txt files "
                                     "(originals backed up as .bak)"},
    "cli.rescan.nothing": {"zh_CN": "\n各被试目录里既没有 alps_result.json 也没有 alps_row.txt，"
                                    "只重写了汇总表。",
                           "en": "\nNeither alps_result.json nor alps_row.txt "
                                 "exists in the subject folders; only the summary "
                                 "table was rewritten."},
    "cli.rescan.tsv_missing": {"zh_CN": "\n[注意] 指定的 TSV 不存在: %s",
                               "en": "\n[note] the given TSV does not exist: %s"},
    "cli.rescan.tsv_written": {"zh_CN": "\n已重写表格: %s",
                               "en": "\nTable rewritten: %s"},
    "cli.err.tsv_write": {"zh_CN": "\n[错误] 表格重写失败: %s",
                          "en": "\n[error] rewriting the table failed: %s"},
    "cli.rescan.scan_only": {"zh_CN": "\n（只扫描，未写任何文件。加 --json 或 --tsv 才会写回）",
                             "en": "\n(scan only, nothing written. Add --json or "
                                   "--tsv to write back)"},

    # ---- report ----
    "cli.err.report_numpy": {"zh_CN": "[错误] 生成 HTML 报告需要 numpy，"
                                       "请用带 numpy 的 python 运行。",
                             "en": "[error] HTML reports need numpy; run this "
                                   "with a python that has numpy."},
    "cli.report.cap_roi": {"zh_CN": "ROI 位置", "en": "ROI location"},
    "cli.report.cap_motion": {"zh_CN": "头动曲线", "en": "Motion traces"},
    "cli.report.single": {"zh_CN": "已生成单例报告: %s",
                          "en": "Single-subject report written: %s"},
    "cli.err.no_result_json": {"zh_CN": "[错误] %s 下没有找到 alps_result.json",
                               "en": "[error] no alps_result.json found under %s"},
    "cli.report.skip_row": {"zh_CN": "  [跳过] %s: %s", "en": "  [skip] %s: %s"},
    "cli.report.batch": {"zh_CN": "已生成批量报告: %s（%d 个被试）",
                         "en": "Batch report written: %s (%d subjects)"},

    # ---- gui startup failure ----
    "misc.nii_filter": {"zh_CN": "NIfTI 文件", "en": "NIfTI files"},
    "cli.err.gui_import": {"zh_CN": "[错误] 无法加载 GUI：%s",
                           "en": "[error] cannot load the GUI: %s"},
    "cli.gui.tk_hint": {"zh_CN": "        需要 tkinter。在 Ubuntu 上可装: "
                                 "sudo apt install python3-tk",
                        "en": "        tkinter is required. On Ubuntu: "
                              "sudo apt install python3-tk"},
    "cli.err.gui_start": {"zh_CN": "[错误] GUI 启动失败：%s",
                          "en": "[error] the GUI failed to start: %s"},
    "cli.gui.wsl_hint": {"zh_CN": "        若在 WSL 中运行，请确认 WSLg 可用"
                                  "（echo $DISPLAY 应有值）。",
                         "en": "        Under WSL, make sure WSLg works "
                               "(echo $DISPLAY should print a value)."},
    "cli.gui.display_hint": {"zh_CN": "        需要图形桌面会话：Linux 请确认 "
                                     "DISPLAY 有值（X11 或 Wayland）；macOS 请"
                                     "确认 python3 -c 'import tkinter' 能通过。",
                            "en": "        A desktop session is required: on "
                                  "Linux check that DISPLAY is set (X11 or "
                                  "Wayland); on macOS check python3 -c "
                                  "'import tkinter'."},

    # =================================================================
    # config.py -- environment checks (shared by the GUI and CLI check)
    # =================================================================
    "misc.env.title": {"zh_CN": " ALPSbox 环境检测",
                       "en": " ALPSbox environment check"},
    "misc.env.eddy_use": {"zh_CN": "  eddy 将使用 : %s",
                          "en": "  eddy will use: %s"},
    "misc.env.not_found": {"zh_CN": "未找到", "en": "not found"},
    "misc.env.not_found_unring": {"zh_CN": "未找到（去振铃不可用）",
                                  "en": "not found (unringing unavailable)"},
    "misc.env.not_found_dicom": {"zh_CN": "未找到（DICOM 输入不可用）",
                                 "en": "not found (DICOM input unavailable)"},
    "misc.env.unknown": {"zh_CN": "未知", "en": "unknown"},
    "misc.env.fsl_required": {"zh_CN": "  FSL 必需命令：",
                              "en": "  FSL required commands:"},
    "misc.env.missing": {"zh_CN": "缺失", "en": "missing"},
    "misc.env.missing_list": {"zh_CN": "  !! 缺失的 FSL 命令: %s",
                              "en": "  !! missing FSL commands: %s"},
    "misc.env.warn_line": {"zh_CN": "  [注意] %s", "en": "  [warn] %s"},
    "misc.env.error_line": {"zh_CN": "  [错误] %s", "en": "  [error] %s"},
    "misc.env.fsldir_missing": {"zh_CN": "指定的 FSLDIR 不存在: %s",
                                "en": "the given FSLDIR does not exist: %s"},
    "misc.env.no_mrdegibbs": {"zh_CN": "未找到 mrdegibbs（MRtrix3），"
                                        "将跳过去 Gibbs 振铃",
                              "en": "mrdegibbs (MRtrix3) not found; Gibbs "
                                    "unringing will be skipped"},
    "misc.env.no_fsl": {
        "zh_CN": "未找到 FSL。请先安装 FSL 6.0.7+ 并设置 $FSLDIR。\n"
                 "        安装: https://fsl.fmrib.ox.ac.uk/fsl/docs/#/install/index\n"
                 "        ALPSbox 不随附 FSL —— FSL 许可禁止再分发。",
        "en": "FSL not found. Install FSL 6.0.7+ and set $FSLDIR.\n"
              "        Install: https://fsl.fmrib.ox.ac.uk/fsl/docs/#/install/index\n"
              "        ALPSbox does not bundle FSL — the FSL licence forbids "
              "redistribution."},
    "misc.env.fsl_missing_cmds": {"zh_CN": "FSL 缺少命令: %s",
                                  "en": "FSL is missing commands: %s"},
    "misc.env.no_eddy": {"zh_CN": "未找到任何 eddy 二进制",
                         "en": "no eddy binary found"},
    "misc.env.fsl_version": {"zh_CN": "FSL 版本: %s", "en": "FSL version: %s"},

    # =================================================================
    # inputs.py -- input discovery
    # =================================================================
    "misc.dwi.no_second": {"zh_CN": "未提供第二套 DWI",
                           "en": "no second DWI provided"},
    "misc.dwi.second_incomplete": {"zh_CN": "第二套 DWI 缺少 bval 或 bvec",
                                   "en": "the second DWI has no bval or bvec"},
    "misc.dwi.pe_missing": {
        "zh_CN": "缺少相位编码方向信息（json 里的 PhaseEncodingDirection），"
                 "无法确认两套数据方向相反",
        "en": "phase-encoding direction missing (PhaseEncodingDirection in the "
              "json); cannot confirm that the two datasets run in opposite "
              "directions"},
    "misc.dwi.pe_other_axis": {"zh_CN": "两套数据的相位编码方向不是同一轴（%s vs %s）",
                               "en": "the two datasets have phase-encoding "
                                     "directions on different axes (%s vs %s)"},
    "misc.dwi.pe_same": {
        "zh_CN": "两套数据的相位编码方向相同（%s），TOPUP 要求方向相反。"
                 "如果确实是两组相反 PE 数据，请检查 json 是否正确。",
        "en": "the two datasets have the same phase-encoding direction (%s), but "
              "TOPUP needs opposite directions. If these really are two "
              "opposite-PE datasets, check that the json is correct."},
    "misc.dwi.json_missing": {"zh_CN": "    json : 未找到（无法做完整 eddy）",
                              "en": "    json : not found (full eddy not possible)"},
    "misc.dwi.json2_missing": {"zh_CN": "    json2: 未找到（TOPUP 需要）",
                               "en": "    json2: not found (TOPUP needs it)"},
    "misc.dwi.note_line": {"zh_CN": "    [注意] %s", "en": "    [warn] %s"},
    "misc.dwi.json_name_mismatch": {"zh_CN": "json 文件名与 nii 不一致（%s），按内容匹配",
                                    "en": "json filename does not match the nii "
                                          "(%s); matched by content"},
    "misc.dwi.json_in_subdir": {"zh_CN": "json 在子目录中找到（%s）",
                                "en": "json found in a subfolder (%s)"},
    "misc.dwi.json_not_dict": {"zh_CN": "json 不是字典: %s",
                               "en": "json is not an object: %s"},
    "misc.dwi.json_unreadable": {"zh_CN": "json 读不出 (%s): %s",
                                 "en": "cannot read the json (%s): %s"},
    "misc.dwi.no_dir": {"zh_CN": "被试目录不存在: %s",
                        "en": "subject folder does not exist: %s"},
    "misc.dwi.no_nii": {"zh_CN": "目录下没有 .nii/.nii.gz: %s",
                        "en": "no .nii/.nii.gz in this folder: %s"},
    "misc.dwi.no_valid": {
        "zh_CN": "找不到带配套 .bval/.bvec 的 DWI（已检查 %d 个 nii）。\n"
                 "      目录中的 nii:\n      %s\n"
                 "      提示：ALPSbox 要求 <name>.nii[.gz] + <name>.bval + "
                 "<name>.bvec 同时存在。",
        "en": "no DWI with matching .bval/.bvec found (%d nii checked).\n"
              "      nii files in this folder:\n      %s\n"
              "      Note: ALPSbox needs <name>.nii[.gz] + <name>.bval + "
              "<name>.bvec to exist together."},
    "misc.dwi.multi_valid": {"zh_CN": "发现 %d 组可用输入，取第一个: %s",
                             "en": "found %d usable input sets; using the first: %s"},
    "misc.dwi.second_file_missing": {"zh_CN": "第二套 DWI 的 %s 文件不存在: %s",
                                     "en": "the second DWI %s file does not "
                                           "exist: %s"},
    "misc.dwi.second_nii_missing": {"zh_CN": "第二套 DWI 的 NIfTI 不存在: %s",
                                    "en": "the second DWI NIfTI does not exist: %s"},
    "misc.dwi.second_incomplete_named": {
        "zh_CN": "第二套 DWI 缺少同名的 .bval/.bvec: %s",
        "en": "the second DWI has no same-name .bval/.bvec: %s"},
    "misc.dwi.topup_on": {"zh_CN": "TOPUP 已启用（%s ↔ %s）",
                          "en": "TOPUP enabled (%s <-> %s)"},
    "misc.dwi.topup_off": {"zh_CN": "TOPUP 未启用：%s",
                           "en": "TOPUP not used: %s"},
    "misc.dwi.pair_bval_mismatch": {
        "zh_CN": "两套数据的 bval 有 %d 个体积不一致，可能不是同一采集/同一被试",
        "en": "%d volumes differ in bval between the two series; they may come "
              "from different acquisitions/subjects"},
    "misc.dwi.pair_bvec_mismatch": {
        "zh_CN": "两套数据的 bvec 数值个数不同（%d vs %d）",
        "en": "the bvec files contain different numbers of values (%d vs %d)"},
    "misc.dwi.pair_meta_mismatch": {
        "zh_CN": "采集元数据 %s 不一致（%s vs %s）",
        "en": "acquisition metadata %s differs (%s vs %s)"},
    "misc.dwi.pair_protocol_mismatch": {
        "zh_CN": "协议名去掉方向标记后不一致（%s vs %s），可能不是同一序列",
        "en": "protocol names differ after removing the direction token "
              "(%s vs %s); they may not be the same series"},
    "misc.dwi.pair_geometry_mismatch": {
        "zh_CN": "图像几何不一致（%s: %s vs %s）",
        "en": "image geometry differs (%s: %s vs %s)"},
    "misc.dwi.pair_inconsistent": {
        "zh_CN": "第二套 DWI 与主数据不一致：%s",
        "en": "the second DWI is inconsistent with the main data: %s"},
    "misc.dwi.pair_inconsistent_where": {
        "zh_CN": "在 %s 中找到反向相位编码数据，但与主数据不一致：%s",
        "en": "found reversed phase-encoding data in %s but it is inconsistent "
              "with the main data: %s"},
    "batch.topup.split_subject": {
        "zh_CN": "被试文件夹“%s”和“%s”看起来是同一被试的 AP/PA 两套数据，"
                 "却被组织成了两个被试；请把两套数据放进同一个被试文件夹后重跑",
        "en": "subject folders \"%s\" and \"%s\" look like the AP/PA series of "
              "one subject but are organized as two subjects; put both series in "
              "one subject folder and rerun"},
    "batch.topup.layout_header": {
        "zh_CN": "TOPUP 批量组织检查发现问题（未开始处理）：",
        "en": "TOPUP batch layout check found problems (nothing was processed):"},
    "batch.report.title": {
        "zh_CN": "ALPSbox 批量预检记录",
        "en": "ALPSbox batch preflight report"},
    "batch.report.summary": {
        "zh_CN": "可用被试 %d，失败 %d，TOPUP 组织错误 %d",
        "en": "usable subjects %d, failed %d, TOPUP layout errors %d"},
    "batch.report.done": {
        "zh_CN": "（本文件在处理开始前写入，作为预检记录）",
        "en": "(written before processing as a preflight record)"},
    "cli.batch.report": {"zh_CN": "预检记录: %s",
                         "en": "preflight report: %s"},
    "cli.batch.blocked": {
        "zh_CN": "已在处理开始前停止。请按上面的提示重新组织被试文件夹后重跑。",
        "en": "Stopped before any processing. Reorganize the subject folders "
              "as described above and rerun."},
    "misc.dwi.sibling_used": {
        "zh_CN": "在相邻文件夹“%s”中找到反向相位编码的第二套 DWI；"
                 "请确认它与主数据来自同一被试",
        "en": "found the reversed phase-encoding DWI in the sibling folder "
              "\"%s\"; confirm that it belongs to the same subject"},
    "misc.dwi.sibling_none": {
        "zh_CN": "所选文件夹内没有第二套反向相位编码数据，也没有可搜索的相邻文件夹；"
                 "可选择包含两套数据的上级目录，或手动选择第二套 DWI",
        "en": "no reversed phase-encoding series inside the selected folder and "
              "no sibling folder to search; select the parent folder that "
              "contains both series, or choose the second DWI manually"},
    "misc.dwi.sibling_too_many": {
        "zh_CN": "上级目录有 %d 个子文件夹，跳过相邻自动检测以避免配错被试；"
                 "请选择包含两套数据的上级目录，或手动选择第二套 DWI",
        "en": "the parent folder has %d subfolders; skipping the sibling search to "
              "avoid pairing data from different subjects. Select the parent "
              "folder containing both series, or choose the second DWI manually"},
    "misc.dwi.sibling_no_match": {
        "zh_CN": "所选文件夹内没有第二套反向相位编码数据，相邻文件夹中也没有"
                 "名称匹配的候选；可手动选择第二套 DWI，或选择包含两套数据的上级目录",
        "en": "no reversed phase-encoding series inside the selected folder and "
              "no name-compatible candidate among its siblings; choose the second "
              "DWI manually, or select the parent folder containing both series"},
    "cli.err.topup_invalid": {"zh_CN": "[错误] TOPUP 设置无效：%s",
                              "en": "[error] invalid TOPUP setup: %s"},
    "cli.err.topup_cfg": {"zh_CN": "[错误] TOPUP 配置文件不存在：%s",
                          "en": "[error] TOPUP configuration file not found: %s"},
    "misc.dwi.no_eddy_meta": {
        "zh_CN": "json 缺 PhaseEncodingDirection 或 TotalReadoutTime，"
                 "将回落 eddy_correct",
        "en": "the json lacks PhaseEncodingDirection or TotalReadoutTime; "
              "falling back to eddy_correct"},
    "misc.dwi.bval_unreadable": {"zh_CN": "bval 读不出: %s",
                                 "en": "cannot read bval: %s"},
    "misc.dwi.bvec_unreadable": {"zh_CN": "bvec 读不出: %s",
                                 "en": "cannot read bvec: %s"},
    "misc.dwi.bval_empty": {"zh_CN": "bval 为空", "en": "bval is empty"},
    "misc.dwi.bvec_empty": {"zh_CN": "bvec 为空", "en": "bvec is empty"},
    "misc.dwi.count_mismatch": {"zh_CN": "bval(%d) 与 bvec 列数(%d) 不一致",
                                "en": "bval (%d values) and bvec (%d columns) "
                                      "disagree"},
    "misc.dwi.bvec_3rows": {"zh_CN": "bvec 应有 3 行，实际 %d 行",
                            "en": "bvec should have 3 rows, found %d"},

    # =================================================================
    # fsl.py -- command runner
    # =================================================================
    "misc.fsl.cmd_failed": {"zh_CN": "命令失败 (exit=%d): %s\n  日志: %s\n  尾部:\n%s",
                            "en": "command failed (exit=%d): %s\n  log: %s\n"
                                  "  tail:\n%s"},
    "misc.fsl.exe_not_found": {"zh_CN": "找不到可执行文件: %s",
                               "en": "executable not found: %s"},
    "misc.fsl.exit_ignored": {"zh_CN": "      ! 返回 %d（已忽略）",
                              "en": "      ! exit %d (ignored)"},
    "misc.fsl.nvol_parse": {"zh_CN": "无法从 fslval 输出解析体积数: %r",
                            "en": "cannot parse the volume count from fslval "
                                  "output: %r"},

    # =================================================================
    # acqp.py -- acqp / index for eddy
    # =================================================================
    "misc.acqp.no_trt": {
        "zh_CN": "json 中既没有 TotalReadoutTime，也无法由 EffectiveEchoSpacing "
                 "× (ReconMatrixPE-1) 推算。 请检查 sidecar 是否完整。",
        "en": "the json has no TotalReadoutTime and it cannot be derived from "
              "EffectiveEchoSpacing × (ReconMatrixPE-1). Check that the sidecar "
              "is complete."},
    "misc.acqp.no_pe": {"zh_CN": "json 中缺 PhaseEncodingDirection",
                        "en": "the json has no PhaseEncodingDirection"},
    "misc.acqp.bad_pe": {"zh_CN": "无法解析的 PhaseEncodingDirection: %r",
                         "en": "unparsable PhaseEncodingDirection: %r"},
    "misc.acqp.rotime_range": {
        "zh_CN": "TotalReadoutTime=%.6f s 超出 FSL eddy 允许范围 [%.2f, %.2f] s。"
                 " 这是 FSL 源码里的硬检查（AcqPara::AcqPara）。"
                 " 常见原因：单位不是秒（例如写成了毫秒）。",
        "en": "TotalReadoutTime=%.6f s is outside the range FSL eddy accepts "
              "[%.2f, %.2f] s. This is a hard check in the FSL source "
              "(AcqPara::AcqPara). The usual cause is a unit other than "
              "seconds (e.g. milliseconds)."},
    "misc.acqp.bad_nvol": {"zh_CN": "体积数非法: %r",
                           "en": "invalid volume count: %r"},

    # =================================================================
    # regqc.py -- registration robustness QC
    # =================================================================
    "misc.regqc.mat_short": {"zh_CN": "矩阵文件不足 16 个数: %s",
                             "en": "the matrix file has fewer than 16 numbers: %s"},
    "misc.regqc.load_fail": {"zh_CN": "读配准矩阵失败: %s",
                             "en": "cannot read the registration matrix: %s"},
    "misc.regqc.base_fail": {"zh_CN": "基准 vecreg/ROI 计算失败",
                             "en": "the baseline vecreg/ROI computation failed"},
    "misc.regqc.too_few": {"zh_CN": "扰动计算成功数过少（%d）",
                           "en": "too few perturbation runs succeeded (%d)"},
    "misc.regqc.level_warn": {"zh_CN": "需注意", "en": "check"},
    "misc.regqc.note_warn": {"zh_CN": "ALPS 对配准高度敏感，建议复核配准",
                             "en": "ALPS is highly sensitive to registration "
                                   "here; re-check the registration"},
    "misc.regqc.level_info": {"zh_CN": "提示", "en": "info"},
    "misc.regqc.note_info": {"zh_CN": "ALPS 对配准较敏感",
                             "en": "ALPS is fairly sensitive to registration"},
    "misc.regqc.level_ok": {"zh_CN": "通过", "en": "pass"},
    "misc.regqc.note_ok": {"zh_CN": "配准稳健", "en": "registration is robust"},
}

register_strings(STRINGS)
