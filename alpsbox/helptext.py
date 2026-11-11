# -*- coding: utf-8 -*-
"""Help text and references (bilingual, zh_CN / en).

Public API
----------
    HELP["input_single"]   # widget-level note, resolved lazily per language
    page(key)              # help page (title, body)
    PAGES_ORDER            # order of the help pages
    references_text()      # body of the References page
"""
from __future__ import annotations

from . import citations as _C
from . import i18n

_HELP = {
    "zh_CN": {
        "input_single": (
            "选这个被试的文件夹。\n\n"
            "里面至少要有一套同名的弥散数据：一张四维的 DWI（.nii 或 .nii.gz）、"
            "同名的 .bval 和 .bvec。三者名字必须一致。\n\n"
            "如果还能找到配套的 .json（dcm2niix 生成的 sidecar），程序会用完整 eddy "
            "做涡流校正、头动校正和离群切片替换；找不到 json 就只能退回 eddy_correct，"
            "结果表里会把这个被试的校正方法标出来。\n\n"
            "程序靠“同名的 bval 和 bvec 都存在”来认定 DWI，所以目录里同时放着 "
            "projection.nii.gz、association.nii.gz 这类 ROI 文件也不会选错。"
            "放在子目录（比如 DTI1/）里同样能自动找到。\n\n"
            "如果同一被试还有一套相位编码方向相反的 DWI（AP + PA），可以在下面的"
            "“高级”参数里启用 TOPUP：本模式可自动检测或手动指定第二套；批量模式"
            "会对每个被试自动检测。"
        ),
        "input_batch": (
            "选一个队列根目录。它下面的每个子文件夹会被当成一个被试，"
            "例如某个目录下有 sub_001、sub_002、sub_003 三个子文件夹，"
            "就是三个被试。\n\n"
            "每个子文件夹内部的要求和单个被试一样：一套同名的 DWI、.bval、.bvec，"
            "有 .json 更好。\n\n"
            "开始之前建议先点“先检查输入”。这个操作只做文件匹配，不跑图像处理，"
            "几秒钟就能把每个被试能不能找到 DWI 列出来，省得跑到一半才发现有的人缺文件。"
        ),
        "outdir": (
            "所有结果写在这个目录下。每个被试会有一个同名子文件夹，里面有 "
            "alps_result.json（全部数值）、pipeline.log（完整的命令记录）、"
            "dwi_eddy.nii.gz（校正后的数据）、以及张量、FA、dxx/dyy/dzz 等中间文件。\n\n"
            "整批跑完还会在输出目录根部生成 alps_summary.csv 和 qc_report.txt。\n\n"
            "如果某个被试的子文件夹里已经有 alps_result.json，默认会跳过它，"
            "这样中断后重新开始不会白跑。想强制重算就勾上“强制重跑”。"
        ),
        "threads": (
            "传给 FSL 和 MRtrix3 的线程数（OMP_NUM_THREADS 与 MRTRIX_NTHREADS）。"
            "一般填 CPU 核数就行。\n\n"
            "这个参数只对多线程的步骤有用，主要是去振铃（mrdegibbs）和张量拟合（dtifit）。"
            "真正占时间最多的 eddy 在 GPU 上算，加线程没用；"
            "bet、flirt、vecreg 本身是单线程，也不受影响。\n\n"
            "所以超过核数再往上调不会更快，反而因为线程抢 CPU 变慢，也更容易吃满内存。"
        ),
        "unring": (
            "用 MRtrix3 的 mrdegibbs 去掉 Gibbs 振铃伪影。建议开着，"
            "每个被试多花半分钟左右。\n\n"
            "如果本机没装 MRtrix3，这一步会自动跳过并在日志里写一句，不影响后面的处理。"
        ),
        "force": (
            "默认情况下，输出目录里已经有 alps_result.json 的被试会被跳过，"
            "可中断续跑。勾上这个选项就忽略已有结果，全部重算。\n\n"
            "需要注意 eddy 本身不是确定性算法（FSL 文档说明），"
            "同一份数据重跑两次结果会有细微差别。"
        ),
        "workers": (
            "同时处理几个被试。建议 1 到 2。\n\n"
            "每个 eddy 进程大约占 1 GB 显存，并行太多会互相抢资源，"
            "单个被试反而变慢。显存不到 4 GB 的机器保持 1 就好。"
        ),
        "roi_bundled": (
            "用随附的参考 ROI。这套掩膜复制自开源参考实现 gbarisano/alps"
            "（MIT License，Copyright (c) 2023 Giuseppe Barisano），"
            "在 JHU-ICBM-FA-1mm 模板上画的 2.5 毫米半径球（= 5 mm 直径，"
            "与 Taoka 2017 原文一致），每个 81 个体素：\n"
            "L_SCR、R_SCR 是上放射冠（投射纤维），L_SLF、R_SLF 是上纵束（联络纤维）。\n\n"
            "这是文献里用得最多的定义，结果便于和已发表数据比较；"
            "来源与文件校验值见仓库 alpsbox/data/ROIs_JHU_ALPS/PROVENANCE.md。"
        ),
        "roi_sphere": (
            "按固定 MNI 坐标现画球形 ROI，坐标是投射区正负 26、负 16、正 27，"
            "联络区正负 38、负 16、正 27。\n\n"
            "半径取 2.5 毫米时，画出来的掩膜和随包参考 ROI 逐体素完全相同。"
            "改半径可以用来做敏感性分析。"
        ),
        "roi_custom": (
            "自己提供四个 NIfTI 掩膜，顺序固定为：左上放射冠、右上放射冠、"
            "左上纵束、右上纵束。掩膜要在 JHU-ICBM-FA-1mm 模板空间，1 毫米分辨率。\n\n"
            "顺序搞错会直接算出错误的 ALPS，建议确认后再用。"
        ),
        "go": (
            "点下去会开一个后台线程逐个处理，界面不会卡住。"
            "底部有两条进度条，上面一条是整体进度，下面一条是当前被试走到第几步。\n\n"
            "处理过程中可以点停止，程序会在当前被试跑完之后才停，"
            "不会留下跑到一半的文件。"
        ),
        "preflight": (
            "只做输入检查，不跑任何图像处理。程序会逐个被试确认能否找到 DWI、"
            "bval 和 bvec 是否配套、json 里有没有做完整 eddy 所需的相位编码方向和读出时间。\n\n"
            "跑处理之前先点一下，可以提前发现缺文件或不配套的问题。"
        ),
        "results": (
            "结果表会自动保存到 ~/.alpsbox/session.json，下次打开还在，不需要手动存。\n\n"
            "另外 ~/.alpsbox/history.jsonl 是只追加的历史记录，清空结果不会动它，"
            "以后要追溯某次跑的数据可以从这里找。\n\n"
            "可以把以前导出的 CSV 或 JSON 用“导入结果”合并回来，"
            "同名的被试会被新的覆盖。"
        ),
        "env": (
            "必需的是 FSL 6.0.3 或更高版本，具体要 eddy、bet、dtifit、flirt、"
            "vecreg、fslroi、fslmaths、fslstats 这八个命令都在。\n"
            "MRtrix3 用来去振铃，dcm2niix 用来转 DICOM，两个都是可选的。\n\n"
            "点右边的环境详情可以看到逐项检查结果和对应的修复命令。"
        ),
        "roi_viewer": (
            "这张图是 JHU-ICBM-FA-1mm 模板在侧脑室体部层面的切片，"
            "四个彩色块就是 ALPS 用到的四个 ROI。\n\n"
            "投射纤维（上放射冠）走上下，联络纤维（上纵束）走前后，"
            "两者在这里互相垂直；血管周围间隙垂直于这两束纤维，也就是沿左右方向。"
            "ALPS 指数取的就是左右方向扩散率与垂直方向扩散率之比。\n\n"
            "鼠标移到色块上可以高亮，点击看解剖详情，滚轮缩放，中键拖动平移。"
            "图像按放射学惯例显示，图像左侧是右脑。"
        ),
        "regqc": (
            "对配准矩阵做 12 次微小扰动（绕三轴各 ±0.5 度、沿三轴各 ±0.5 毫米），"
            "每次重新把张量变换到模板空间并重算 ALPS，报告 ALPS 的变化范围。\n\n"
            "为什么要做：ALPS 依赖张量从个体空间到模板空间的重定向，配准矩阵的"
            "小误差会直接进入结果（重定向方法对可重复性的影响见 Tatekawa 2023）；"
            "这个指标把“该被试的结果对配准有多敏感”单独量化出来，而 r_wm 这类"
            "整体相关系数并不直接反映这一点。\n\n"
            "判定：极差 < 6% 通过；6–10% 提示；> 10% 需注意（该被试结果对配准"
            "过于敏感，建议复核配准后再用）。分档是可改的实践性阈值，不是公认标准。\n\n"
            "代价：每个被试多花约 1 到 2 分钟。默认关闭，需要时勾选。"
        ),
        "topup": (
            "TOPUP 用两套相位编码方向相反（例如 AP 与 PA）的 DWI 估计磁化率"
            "畸变场，再交给 FSL eddy 做畸变校正。\n\n"
            "启用条件：同一被试有两套 DWI，各自 .bval/.bvec 齐全；两套 .json 都要有 "
            "PhaseEncodingDirection（同一轴、方向相反，如 j 与 j-）和 "
            "TotalReadoutTime；每套的第一个 volume 都应是 b0。输入格式与主数据"
            "相同：NIfTI（.nii/.nii.gz）+ 同名 .bval + .bvec + BIDS .json；"
            "DICOM 需先用 dcm2niix 转换成这四件套。\n\n"
            "单被试有两种用法：自动检测（在单被试目录内寻找反向 PE 的第二套），"
            "或手动选择第二套 DWI 的 NIfTI（同目录同名 .bval/.bvec/.json 自动匹配）。\n"
            "批量：每个被试文件夹自动检测；有反向 PE 数据就自动启用，没有就按"
            "单相位编码处理，不会中断队列。\n\n"
            "参数：默认自动查找 FSL 的 b02b0.cnf，也可手动指定其它 TOPUP 配置文件。"
            "结果文件（alps_result.json / alps_summary.csv / HTML 报告）会记录 "
            "TOPUP 是否启用及使用的配置名，便于跨研究比较。\n\n"
            "注意：两套数据必须来自同一被试、同一协议，仅相位编码方向相反；"
            "相位编码方向相同的两套数据不会被当作 TOPUP 输入，程序会给出提示。\n\n"
            "方法文献：Andersson JLR, Skare S, Ashburner J. How to correct "
            "susceptibility distortions in spin-echo echo-planar images: "
            "application to diffusion tensor imaging. NeuroImage. "
            "2003;20(2):870-888. doi:10.1016/S1053-8119(03)00336-7"
        ),
        "qc": (
            "质控覆盖八类指标（界面上按明细逐项展开，另含处理状态），每项判通过、提示、需注意或不合格，"
            "只要有一项不合格，该被试总体就判不合格。\n\n"
            "头动分成两个指标，因为 eddy 输出的两列物理含义不同。\n"
            "“抖动”是相对前一个体积的位移，相当于 fMRI 里的 frame-wise "
            "displacement，不随扫描时长累积，组间可比。\n"
            "“漂移”是相对第 1 个体积的位移，反映整段扫描漂了多远，"
            "会随扫描时长累积，序列越长数值越大，所以只作参考，不宜跨协议比较。\n\n"
            "双击某一行可以看到该被试每一项的具体数值，以及头动随体积变化的曲线。"
            "曲线里上半是漂移、下半是抖动，红带标出被判为离群的体积。\n\n"
            "详情窗口中间有一条可拖动的分隔条，往左拖图会更大。"
            "图本身可以滚轮缩放、按住拖动平移，缩放时是按新尺寸重画的，"
            "不是把图片拉大，所以文字不会糊。\n\n"
            "想先看看效果，可以导入 examples/demo_synthetic_cohort 里的示例 CSV，"
            "那是合成数据，不涉及任何真实被试。"
        ),
        "scatter": (
            "任选两个变量画散点，自动给出相关系数 r、p 值和样本量。\n\n"
            "分组口径由你定，工具不预设任何队列结构：\n"
            "按 ID 前缀，就是取第一个下划线、横线或点之前的那一段，"
            "siteA_01 归到 siteA；\n"
            "用 group 列，是读数据里自带的分组字段；\n"
            "不分组就全部画成一组。\n\n"
            "同组同色，颜色按组顺序循环取用，不绑定任何具体研究。"
        ),
        "qc_thresholds": (
            "这些阈值没有公认标准，是按方法学常识与常见实践定的，所以做成可改的。\n\n"
            "配准相关系数 0.95 是通过线：同模板同空间时接近 1.000，"
            "跨被试正常也多在 0.95 以上，掉到 0.90 以下通常提示配准失败。\n\n"
            "抖动（相对位移）是主要判据，不随扫描时长累积，适合跨协议比较；"
            "0.25 的警告线只是实践性的参考值。\n"
            "漂移（绝对位移）阈值放得宽，因为它随扫描时长累积，不同体积数的"
            "序列不可直接比较；拿漂移做组间比较会得出虚假结论。\n\n"
            "ALPS 区间取得比较宽（0.60 到 2.50），目的是抓明显异常，不是筛正常值。\n\n"
            "改完点保存，当前所有结果立即按新标准重判。配置存在 "
            "~/.alpsbox/qc_config.json，删掉这个文件就回到默认值。"
        ),
    },

    "en": {
        "input_single": (
            "Pick this subject's folder.\n\n"
            "It must contain at least one matched diffusion set: a 4D DWI "
            "(.nii or .nii.gz) plus a .bval and a .bvec sharing the same base name. "
            "All three names must match.\n\n"
            "If a matching .json sidecar (from dcm2niix) is present, ALPSbox uses "
            "full eddy for eddy-current, motion and outlier-slice correction. "
            "Without it the pipeline falls back to eddy_correct, and the results "
            "table records which correction each subject received.\n\n"
            "A file is treated as the DWI only when a same-named .bval and .bvec "
            "both exist, so stray ROI files such as projection.nii.gz or "
            "association.nii.gz are never picked by mistake. Subfolders "
            "(e.g. DTI1/) are searched too.\n\n"
            "If the subject also has a second DWI with the opposite phase-encoding "
            "direction (AP + PA), enable TOPUP under Advanced; single-subject mode "
            "can auto-detect a reversed series or take a manually chosen second DWI."
        ),
        "input_batch": (
            "Pick a cohort root folder. Every subfolder is treated as one subject: "
            "a folder holding sub_001, sub_002 and sub_003 yields three subjects.\n\n"
            "Each subfolder has the same requirements as a single subject: one "
            "matched DWI/.bval/.bvec set, ideally with a .json.\n\n"
            "If a subject also has a second DWI with the opposite phase-encoding "
            "direction (AP + PA), enable TOPUP under Advanced; each subject folder "
            "is then checked for a reversed series automatically.\n\n"
            "Click “Check inputs” before starting. It only matches files, runs no "
            "image processing, and reports within seconds which subjects are usable."
        ),
        "outdir": (
            "All results go here. Each subject gets a subfolder of the same name "
            "holding alps_result.json (all values), pipeline.log (full command "
            "record), dwi_eddy.nii.gz (corrected data), plus tensor, FA, "
            "dxx/dyy/dzz and other intermediates.\n\n"
            "A finished batch also writes alps_summary.csv and qc_report.txt at the "
            "root of the output folder.\n\n"
            "If a subject subfolder already contains alps_result.json it is skipped, "
            "so an interrupted run can resume. Tick “Force re-run” to recompute."
        ),
        "threads": (
            "Thread count passed to FSL and MRtrix3 (OMP_NUM_THREADS and "
            "MRTRIX_NTHREADS). Setting it to the CPU core count is usually right.\n\n"
            "This only affects multithreaded steps, mainly unringing (mrdegibbs) and "
            "tensor fitting (dtifit). eddy dominates the runtime and runs on the GPU, "
            "so extra threads do not help it; bet, flirt and vecreg are single-threaded.\n\n"
            "Going above the core count is slower, not faster, and uses more memory."
        ),
        "unring": (
            "Removes Gibbs ringing with MRtrix3's mrdegibbs. Recommended; costs about "
            "half a minute per subject.\n\n"
            "If MRtrix3 is not installed this step is skipped with a note in the log "
            "and the rest of the pipeline continues unaffected."
        ),
        "force": (
            "By default, subjects whose output folder already contains "
            "alps_result.json are skipped so an interrupted run can resume. Ticking "
            "this recomputes everything.\n\n"
            "Note that eddy is not deterministic (FSL documents this), so re-running "
            "the same data gives slightly different numbers."
        ),
        "workers": (
            "How many subjects to process at once. 1–2 is recommended.\n\n"
            "Each eddy process uses roughly 1 GB of GPU memory; too many in parallel "
            "contend for resources and slow each other down. Keep it at 1 on GPUs "
            "with less than 4 GB."
        ),
        "roi_bundled": (
            "Uses the bundled reference ROIs, reproduced from the open-source "
            "reference implementation gbarisano/alps (MIT License, Copyright "
            "(c) 2023 Giuseppe Barisano): 2.5 mm radius spheres (= 5 mm "
            "diameter, matching Taoka 2017) on the JHU-ICBM-FA-1mm template, "
            "81 voxels each. L_SCR and R_SCR are the superior corona radiata "
            "(projection fibres); L_SLF and R_SLF are the superior longitudinal "
            "fasciculus (association fibres).\n\n"
            "This is the most widely used definition, so results compare "
            "directly with published work; provenance and file checksums are "
            "in alpsbox/data/ROIs_JHU_ALPS/PROVENANCE.md."
        ),
        "roi_sphere": (
            "Generates spherical ROIs from fixed MNI coordinates: projection at "
            "(±26, −16, 27), association at (±38, −16, 27).\n\n"
            "At a radius of 2.5 mm the masks match the bundled reference ROIs "
            "voxel for voxel. Changing the radius is useful for sensitivity "
            "analysis."
        ),
        "roi_custom": (
            "Supply your own four NIfTI masks, in this exact order: left projection, "
            "right projection, left association, right association. Masks must be in "
            "JHU-ICBM-FA-1mm space at 1 mm resolution.\n\n"
            "Getting the order wrong produces a wrong ALPS value, so double-check."
        ),
        "go": (
            "Starts a background thread that processes subjects one by one, so the "
            "interface stays responsive. Two progress bars sit at the bottom: overall "
            "progress above, current step below.\n\n"
            "You can stop at any time; the current subject finishes first, so no "
            "half-written files are left behind."
        ),
        "preflight": (
            "Checks inputs only and runs no image processing. For every subject it "
            "reports whether the DWI is found, whether bval and bvec match, and "
            "whether the JSON carries the phase-encoding direction and readout time "
            "that full eddy needs.\n\n"
            "Run it before processing to catch missing or mismatched files early."
        ),
        "results": (
            "The results table is saved automatically to ~/.alpsbox/session.json and "
            "restored on the next start; no manual save needed.\n\n"
            "~/.alpsbox/history.jsonl is an append-only journal that clearing the "
            "table does not touch, useful for tracing earlier runs.\n\n"
            "Previously exported CSV or JSON can be merged back with “Import”; "
            "records sharing a subject ID are replaced by the newer one."
        ),
        "env": (
            "FSL 6.0.3 or newer is required, specifically with eddy, bet, dtifit, "
            "flirt, vecreg, fslroi, fslmaths and fslstats all present.\n"
            "MRtrix3 provides unringing and dcm2niix handles DICOM input; both are "
            "optional.\n\n"
            "Click “Environment” for a per-item check and the matching fix commands."
        ),
        "roi_viewer": (
            "This is a slice of the JHU-ICBM-FA-1mm template at the level of the "
            "body of the lateral ventricles. The four coloured patches are the ROIs "
            "used for ALPS.\n\n"
            "Projection fibres (superior corona radiata) run head–foot and "
            "association fibres (superior longitudinal fasciculus) run "
            "anterior–posterior; the two are perpendicular here. Perivascular spaces "
            "run perpendicular to both, i.e. left–right, which is the direction ALPS "
            "measures.\n\n"
            "Hover a patch to highlight it, click for anatomical detail, scroll to "
            "zoom, drag with the middle button to pan. Images follow the radiological "
            "convention: the left side of the image is the right hemisphere."
        ),
        "regqc": (
            "Applies 12 small perturbations to the registration matrix "
            "(±0.5 degrees about each axis, ±0.5 mm along each axis), re-orients the "
            "tensor to template space each time and recomputes ALPS, then reports how "
            "much ALPS varies.\n\n"
            "Why this matters: ALPS depends on re-orienting the tensor from subject "
            "to template space, so small registration errors propagate directly into "
            "the result (see Tatekawa 2023 for the effect of reorientation on "
            "reproducibility); this metric isolates how sensitive one subject's "
            "result is to registration, which an overall correlation such as r_wm "
            "does not show directly.\n\n"
            "Grading: range < 6% pass; 6–10% info; > 10% check (the result is too "
            "sensitive to registration; review the registration before using it). "
            "The cut-offs are practical, editable defaults, not a consensus "
            "standard.\n\n"
            "Cost: about 1–2 minutes per subject. Off by default."
        ),
        "topup": (
            "TOPUP estimates a susceptibility-distortion field from two DWI "
            "series with opposite phase-encoding directions (for example AP and "
            "PA) and hands that field to FSL eddy.\n\n"
            "Requirements: both series must belong to the same subject, each "
            "with its own complete .bval/.bvec set; both .json files must carry "
            "PhaseEncodingDirection (same axis, opposite sign, e.g. j and j-) and "
            "TotalReadoutTime; the first volume of each series must be b0. Input "
            "format is the same as the main data: NIfTI (.nii/.nii.gz) + same-name "
            ".bval + .bvec + BIDS .json; convert DICOM with dcm2niix first.\n\n"
            "Single subject: auto-detect (search the subject folder for a "
            "reversed-PE series) or choose the second DWI NIfTI manually "
            "(same-name .bval/.bvec/.json are matched automatically).\n"
            "Batch: every subject folder is checked automatically; TOPUP is "
            "enabled where a reversed-PE series exists, otherwise single-PE eddy "
            "runs and the cohort is never interrupted.\n\n"
            "Parameters: FSL's b02b0.cnf is located automatically by default; a "
            "different TOPUP configuration file can be specified. Result files "
            "(alps_result.json / alps_summary.csv / HTML report) record whether "
            "TOPUP was used and which config, for cross-study comparison.\n\n"
            "Note: both series must come from the same subject and protocol, with "
            "only the phase-encoding direction differing; two series with the same "
            "phase-encoding direction are rejected with a message.\n\n"
            "References:\n\n"
            "Andersson JLR, Skare S, Ashburner J. How to correct "
            "susceptibility distortions in spin-echo echo-planar images: "
            "application to diffusion tensor imaging. NeuroImage. "
            "2003;20(2):870-888. doi:10.1016/S1053-8119(03)00336-7"
        ),
        "qc": (
            "QC covers eight categories of checks (the table expands them into items, "
            "plus the processing status); "
            "each item is graded pass, info, check or fail. "
            "Any failing item fails the subject overall.\n\n"
            "Motion is split into two metrics because the two columns of eddy's "
            "output mean different things.\n"
            "“Jitter” is displacement relative to the previous volume, analogous to "
            "frame-wise displacement in fMRI; it does not accumulate with scan length "
            "and is comparable across groups.\n"
            "“Drift” is displacement relative to the first volume; it does accumulate "
            "with scan length, so longer series are naturally larger. It is reported "
            "for reference only and should not be compared across protocols.\n\n"
            "Double-click a row to see every value for that subject together with the "
            "motion time course. The upper panel is drift, the lower is jitter, and "
            "red bands mark outlier volumes.\n\n"
            "The divider in the detail window can be dragged to enlarge the plot. The "
            "plot zooms with the wheel and pans by dragging, and is re-rendered at the "
            "new size rather than upscaled, so text stays sharp.\n\n"
            "To see it working, import the sample CSV in "
            "examples/demo_synthetic_cohort; that data is synthetic and involves no "
            "real subject."
        ),
        "scatter": (
            "Plot any two variables against each other; the correlation r, its p value "
            "and the sample size are computed automatically.\n\n"
            "Grouping is your choice; the tool assumes no cohort structure:\n"
            "by ID prefix — the text before the first underscore, hyphen or dot, so "
            "siteA_01 belongs to siteA;\n"
            "by a group column in the data;\n"
            "or not grouped at all.\n\n"
            "Colours come from a generic cyclic palette, not tied to any study."
        ),
        "qc_thresholds": (
            "There is no consensus on these cut-offs; they follow methodological "
            "common sense and common practice, which is why they are editable.\n\n"
            "A registration correlation of 0.95 is the passing line: the same "
            "template in the same space gives close to 1.000, and cross-subject "
            "values normally stay above 0.95; below 0.90 registration is likely "
            "broken.\n\n"
            "Jitter is the primary criterion because it does not accumulate with "
            "scan length and can be compared across protocols; the 0.25 warning "
            "line is a practical reference value.\n"
            "Drift thresholds are deliberately loose because drift accumulates "
            "with scan length: series with different numbers of volumes cannot be "
            "compared directly, and comparing drift across groups would produce a "
            "spurious result.\n\n"
            "The plausible ALPS window is wide (0.60–2.50) on purpose: it catches "
            "obvious errors rather than screening normal values.\n\n"
            "Saving re-evaluates every subject immediately. Settings live in "
            "~/.alpsbox/qc_config.json; deleting that file restores the defaults."
        ),
    },
}


# =====================================================================
# Citation format:
#   authors  —  may be shortened to "first author et al." (both authors are
#               listed when there are exactly two)
#   after the authors  —  full title + journal + year;volume(issue):pages +
#               DOI, never abbreviated
# Full author lists are in REFERENCES at the end of this file (References page)
# =====================================================================
_CITE_CORE = {
    "taoka17": (
        "Taoka T, et al. Evaluation of glymphatic system activity with "
        "the diffusion MR technique: diffusion tensor image analysis "
        "along the perivascular space (DTI-ALPS) in Alzheimer's disease "
        "cases. Jpn J Radiol. 2017;35(4):172-178. "
        "doi:10.1007/s11604-017-0617-z"
    ),
    # ---- Formal citation for the reference implementation (gbarisano/alps);
    # ---- single source in citations.py ----
    "ref_software": _C.CITATION_REF_SOFTWARE,
    "ref_paper": _C.CITATION_REF_PAPER,
    "ref_roi": _C.CITATION_ROI_MASKS,
    "taoka22": (
        "Taoka T, et al. Reproducibility of diffusion tensor image "
        "analysis along the perivascular space (DTI-ALPS) for evaluating "
        "interstitial fluid diffusivity and glymphatic function: CHanges "
        "in Alps index on Multiple conditiON acquIsition eXperiment "
        "(CHAMONIX) study. Jpn J Radiol. 2022;40(2):147-158. "
        "doi:10.1007/s11604-021-01187-5"
    ),
    "tatekawa23": (
        "Tatekawa H, et al. Improved reproducibility of diffusion tensor "
        "image analysis along the perivascular space (DTI-ALPS) index: an "
        "analysis of reorientation technique of the OASIS-3 dataset. Jpn "
        "J Radiol. 2023;41(4):393-400. doi:10.1007/s11604-022-01370-2"
    ),
    "kellner16": (
        "Kellner E, et al. Gibbs-ringing artifact removal based on local "
        "subvoxel-shifts. Magn Reson Med. 2016;76(5):1574-1581. "
        "doi:10.1002/mrm.26054"
    ),
    "andersson16": (
        "Andersson JLR, Sotiropoulos SN. An integrated approach to "
        "correction for off-resonance effects and subject movement in "
        "diffusion MR imaging. NeuroImage. 2016;125:1063-1078. "
        "doi:10.1016/j.neuroimage.2015.10.019"
    ),
    "alexander01": (
        "Alexander DC, et al. Spatial transformations of diffusion tensor "
        "magnetic resonance images. IEEE Trans Med Imaging. "
        "2001;20(11):1131-1139. doi:10.1109/42.963816"
    ),
    "basser94": (
        "Basser PJ, et al. MR diffusion tensor spectroscopy and imaging. "
        "Biophys J. 1994;66(1):259-267. doi:10.1016/S0006-3495(94)80775-1"
    ),
    "smith02": (
        "Smith SM. Fast robust automated brain extraction. Hum Brain "
        "Mapp. 2002;17(3):143-155. doi:10.1002/hbm.10062"
    ),
    "jenkinson02": (
        "Jenkinson M, et al. Improved optimization for the robust and "
        "accurate linear registration and motion correction of brain "
        "images. NeuroImage. 2002;17(2):825-841. "
        "doi:10.1006/nimg.2002.1132"
    ),
    "jenkinson12": (
        "Jenkinson M, et al. FSL. NeuroImage. 2012;62(2):782-790. "
        "doi:10.1016/j.neuroimage.2011.09.015"
    ),
    "tournier19": (
        "Tournier JD, et al. MRtrix3: A fast, flexible and open software "
        "framework for medical image processing and visualisation. "
        "NeuroImage. 2019;202:116137. "
        "doi:10.1016/j.neuroimage.2019.116137"
    ),
    "power12": (
        "Power JD, et al. Spurious but systematic correlations in "
        "functional connectivity MRI networks arise from subject motion. "
        "NeuroImage. 2012;59(3):2142-2154. "
        "doi:10.1016/j.neuroimage.2011.10.018"
    ),
    "ajouz26": (
        "Ajouz A, et al. Automatic determination of glymphatic flow with "
        "the DTI-ALPS-index along the principal axis system in native "
        "imaging space corrects for head and fiber orientation. Magn "
        "Reson Med. 2026;95(2):1110-1122. doi:10.1002/mrm.70082"
    ),
    "schilling25": (
        "Schilling KG, et al. White matter geometry confounds diffusion "
        "tensor imaging along perivascular space (DTI-ALPS) measures. Hum "
        "Brain Mapp. 2025;46(10):e70282. doi:10.1002/hbm.70282"
    ),
    "qiu25": (
        "Qiu E, et al. Reliability and spatial consistency of MR diffusion "
        "tensor imaging measures along the cerebral perivascular space. J "
        "Neuroimaging. 2025;35(5):e70086. doi:10.1111/jon.70086"
    ),
    "andersson03": (
        "Andersson JLR, Skare S, Ashburner J. How to correct susceptibility "
        "distortions in spin-echo echo-planar images: application to "
        "diffusion tensor imaging. NeuroImage. 2003;20(2):870-888. "
        "doi:10.1016/S1053-8119(03)00336-7"
    ),
    "liu24": (
        "Liu X, Barisano G, et al. Cross-vendor test-retest validation of "
        "diffusion tensor image analysis along the perivascular space "
        "(DTI-ALPS) for evaluating glymphatic system function. Aging Dis. "
        "2024;15(4):1885-1898. doi:10.14336/AD.2023.0321-2"
    ),
}

_CITATIONS = {
    "zh_CN": {
        "input_single":
            _CITE_CORE["andersson16"] + "（eddy 需要 PhaseEncodingDirection 与 "
            "TotalReadoutTime，所以推荐补 json）",
        "input_batch":
            _CITE_CORE["andersson16"] + "（有 json 才能做完整 eddy）",
        "unring":
            _CITE_CORE["kellner16"] + "（mrdegibbs 的方法来源）",
        "force":
            _CITE_CORE["andersson16"] + "（FSL 说明 eddy 非确定性，"
            "同一数据重复运行结果会有细微差异）",
        "roi_bundled":
            _CITE_CORE["taoka17"] + "（ROI 定义与 5 mm 直径球）\n\n"
            + _CITE_CORE["ref_software"] + "（随附掩膜的来源，MIT License）"
            + "\n\n" + _CITE_CORE["ref_paper"] + "（该仓库要求的配套论文）"
            + "\n\n" + _CITE_CORE["ref_roi"],
        "roi_sphere":
            _CITE_CORE["taoka17"] + "（原文为 5 mm 直径球，即 2.5 mm 半径）",
        "roi_custom":
            _CITE_CORE["taoka17"] + "（四区的定义与顺序依据）",
        "env":
            _CITE_CORE["jenkinson12"] + "\n\n" + _CITE_CORE["tournier19"],
        "roi_viewer":
            _CITE_CORE["taoka17"] + "（投射纤维、联络纤维与髓静脉的解剖关系）",
        "regqc":
            _CITE_CORE["ajouz26"] + "\n\n" + _CITE_CORE["schilling25"]
            + "\n\n" + _CITE_CORE["taoka22"] + "\n\n"
            + _CITE_CORE["tatekawa23"],
        "qc":
            _CITE_CORE["power12"] + "（帧间位移 / framewise displacement 的定义）；"
            + _CITE_CORE["qiu25"] + "（DTI-ALPS 指标的可靠性与空间一致性）；"
            + _CITE_CORE["tatekawa23"],
        "qc_thresholds":
            _CITE_CORE["taoka22"] + "（ROI 与采集参数变化对 ALPS 的影响幅度）；"
            + _CITE_CORE["qiu25"] + "（可靠性与空间一致性）；"
            + _CITE_CORE["power12"] + "（头动阈值惯例）",
    },
    "en": {
        "input_single":
            _CITE_CORE["andersson16"] + " (eddy needs PhaseEncodingDirection "
            "and TotalReadoutTime, hence the JSON)",
        "input_batch":
            _CITE_CORE["andersson16"] + " (full eddy needs the JSON)",
        "unring":
            _CITE_CORE["kellner16"] + " (source of mrdegibbs)",
        "force":
            _CITE_CORE["andersson16"] + " (FSL documents that eddy is not "
            "deterministic)",
        "roi_bundled":
            _CITE_CORE["taoka17"] + " (ROI definition, 5 mm diameter spheres)"
            + "\n\n" + _CITE_CORE["ref_software"] + " (source of the bundled "
            "masks, MIT License)" + "\n\n" + _CITE_CORE["ref_paper"]
            + " (accompanying paper required by that repository)"
            + "\n\n" + _CITE_CORE["ref_roi"],
        "roi_sphere":
            _CITE_CORE["taoka17"] + " (5 mm diameter = 2.5 mm radius)",
        "roi_custom":
            _CITE_CORE["taoka17"] + " (definition and order of the four areas)",
        "env":
            _CITE_CORE["jenkinson12"] + "\n\n" + _CITE_CORE["tournier19"],
        "roi_viewer":
            _CITE_CORE["taoka17"] + " (projection/association fibres and the "
            "medullary veins)",
        "regqc":
            _CITE_CORE["ajouz26"] + "\n\n" + _CITE_CORE["schilling25"]
            + "\n\n" + _CITE_CORE["taoka22"] + "; "
            + _CITE_CORE["tatekawa23"],
        "qc":
            _CITE_CORE["power12"] + " (framewise displacement); "
            + _CITE_CORE["qiu25"] + " (reliability and spatial consistency "
            "of DTI-ALPS measures); " + _CITE_CORE["tatekawa23"],
        "qc_thresholds":
            _CITE_CORE["taoka22"] + " (magnitude of ALPS change from "
            "ROI/parameter variation); " + _CITE_CORE["qiu25"]
            + " (reliability and spatial consistency); "
            + _CITE_CORE["power12"] + " (conventional motion cut-offs)",
    },
}

# Citation for each pipeline step (used by the "pipeline" help entry)
_STEP_CITES = {
    "zh_CN": [
        ("mrdegibbs 去 Gibbs 振铃", _CITE_CORE["kellner16"]),
        ("eddy --repol 涡流 / 头动 / 离群切片校正", _CITE_CORE["andersson16"]),
        ("bet 脑提取", _CITE_CORE["smith02"]),
        ("dtifit 张量拟合", _CITE_CORE["basser94"]),
        ("flirt 把 FA 配准到模板", _CITE_CORE["jenkinson02"]),
        ("vecreg 张量重定向（T' = R·T·Rᵀ）",
         _CITE_CORE["alexander01"] + "\n\n" + _CITE_CORE["tatekawa23"]),
        ("fslroi / fslstats 取分量与 ROI 均值", _CITE_CORE["jenkinson12"]),
        ("ALPS 指数公式", _CITE_CORE["taoka17"]),
        ("TOPUP 磁化率畸变校正（可选）", _CITE_CORE["andersson03"]),
    ],
    "en": [
        ("mrdegibbs Gibbs-ringing removal", _CITE_CORE["kellner16"]),
        ("eddy --repol (eddy current / motion / outlier slices)",
         _CITE_CORE["andersson16"]),
        ("bet brain extraction", _CITE_CORE["smith02"]),
        ("dtifit tensor fitting", _CITE_CORE["basser94"]),
        ("flirt FA-to-template registration", _CITE_CORE["jenkinson02"]),
        ("vecreg tensor reorientation (T' = R T R^T)",
         _CITE_CORE["alexander01"] + "\n\n" + _CITE_CORE["tatekawa23"]),
        ("fslroi / fslstats component extraction and ROI means",
         _CITE_CORE["jenkinson12"]),
        ("ALPS index formula", _CITE_CORE["taoka17"]),
        ("TOPUP susceptibility distortion correction (optional)",
         _CITE_CORE["andersson03"]),
    ],
}


def pipeline_text() -> str:
    """Pipeline steps and their citations."""
    lang = i18n.get_lang()
    rows = _STEP_CITES.get(lang) or _STEP_CITES["zh_CN"]
    head = ("本工具的完整处理链与每一步的方法学出处：\n"
            if lang != "en" else
            "Full processing chain and the methodological source of each step:\n")
    lines = [head]
    for i, (step, cite) in enumerate(rows, 1):
        lines.append("%d. %s" % (i, step))
        lines.append("   -> %s" % cite)
    tail = ("\n\n所有步骤均按引用文献的原始方法执行，未引入未经文献支持的自定义步骤。\n"
            "ALPS 方法出自 Taoka 2017；本仓库所称「参考实现」专指 "
            "gbarisano/alps（MIT License）——本工具不打包、也不修改它，"
            "引用格式见「参考文献」页。"
            if lang != "en" else
            "\n\nAll steps follow the cited original methods; no unsupported "
            "custom step is introduced.\nThe ALPS method is from Taoka 2017; "
            "'reference implementation' in this repository means "
            "gbarisano/alps (MIT License) - ALPSbox neither bundles nor "
            "modifies it. Full citations are on the References page.")
    lines.append(tail)
    return "\n".join(lines)


class _LangDict:
    """Dict-like wrapper that resolves lazily for the current language."""

    def __init__(self, table):
        self._table = table

    def _d(self):
        return self._table.get(i18n.get_lang()) or self._table["zh_CN"]

    def __getitem__(self, key):
        d = self._d()
        body = d[key] if key in d else self._table["zh_CN"].get(key, "")
        # Special page: "pipeline" is generated by a function
        if key == "pipeline":
            return pipeline_text()
        # Append the step's citation to the end of every "?" help block
        if body:
            lang = i18n.get_lang()
            cite = (_CITATIONS.get(lang) or _CITATIONS["zh_CN"]).get(key)
            if cite:
                sep = "\n\n" + "-" * 30 + "\n"
                label = "文献：" if lang != "en" else "Reference: "
                body = body + sep + label + "\n\n" + cite
        return body

    def get(self, key, default=None):
        try:
            return self[key]
        except Exception:
            return default

    def keys(self):
        return list(self._d().keys()) + ["pipeline"]

    def items(self):
        return self._d().items()

    def __contains__(self, key):
        return key in self._d()

    def __len__(self):
        return len(self._d())


HELP = _LangDict(_HELP)

# Exposed so that the two languages can be checked for alignment
def missing_keys():
    """Return the keys each language is missing relative to zh_CN.

    Exists for self-checks that keep the two language tables aligned.
    """
    base = set(_HELP["zh_CN"])
    out = {}
    for lang, d in _HELP.items():
        miss = base - set(d)
        if miss:
            out[lang] = sorted(miss)
    return out


PAGES_ORDER = ["quickstart", "input", "install", "trouble", "method",
               "refs"]

_PAGE_TITLES = {
    "zh_CN": {"quickstart": "快速上手", "input": "输入数据要求",
              "install": "安装与依赖", "trouble": "故障排查",
              "method": "方法学依据", "refs": "参考文献"},
    "en": {"quickstart": "Quick start", "input": "Input requirements",
           "install": "Installation", "trouble": "Troubleshooting",
           "method": "Methods", "refs": "References"},
}


def page_title(key: str) -> str:
    lang = i18n.get_lang()
    return (_PAGE_TITLES.get(lang) or _PAGE_TITLES["zh_CN"]).get(key, key)


def page(key: str):
    """Return (title, body) for one help page.

    The References page body comes from references_text().
    """
    from . import help_pages
    body = references_text() if key == "refs" else help_pages.body(key)
    return page_title(key), body


# =====================================================================
# References (full format, identical in both languages)
# =====================================================================
REFERENCES = [
    "Taoka T, Masutani Y, Kawai H, Nakane T, Matsuoka K, Yasuno F, Kishimoto T, "
    "Naganawa S. Evaluation of glymphatic system activity with the diffusion MR "
    "technique: diffusion tensor image analysis along the perivascular space "
    "(DTI-ALPS) in Alzheimer's disease cases. Japanese Journal of Radiology. "
    "2017;35(4):172-178. doi:10.1007/s11604-017-0617-z",

    "Taoka T, Ito R, Nakamichi R, Kamagata K, Sakai M, Kawai H, Nakane T, Abe T, "
    "Ichikawa K, Kikuta J, Aoki S, Naganawa S. Reproducibility of diffusion tensor "
    "image analysis along the perivascular space (DTI-ALPS) for evaluating "
    "interstitial fluid diffusivity and glymphatic function: CHanges in Alps index "
    "on Multiple conditiON acquIsition eXperiment (CHAMONIX) study. Japanese "
    "Journal of Radiology. 2022;40(2):147-158. doi:10.1007/s11604-021-01187-5",

    "Tatekawa H, Matsushita S, Ueda D, Takita H, Horiuchi D, Atsukawa N, "
    "Morishita Y, Tsukamoto T, Shimono T, Miki Y. Improved reproducibility of "
    "diffusion tensor image analysis along the perivascular space (DTI-ALPS) index: "
    "an analysis of reorientation technique of the OASIS-3 dataset. Japanese "
    "Journal of Radiology. 2023;41(4):393-400. doi:10.1007/s11604-022-01370-2",

    "Alexander DC, Pierpaoli C, Basser PJ, Gee JC. Spatial transformations of "
    "diffusion tensor magnetic resonance images. IEEE Transactions on Medical "
    "Imaging. 2001;20(11):1131-1139. doi:10.1109/42.963816",

    "Ajouz A, Jansen O, Frohwein LJ, Seehafer S, Larsen N, Hövener JB. Automatic "
    "determination of glymphatic flow with the DTI-ALPS-index along the principal "
    "axis system in native imaging space corrects for head and fiber orientation. "
    "Magnetic Resonance in Medicine. 2026;95(2):1110-1122. doi:10.1002/mrm.70082",

    "Schilling KG, Newton A, Tax C, Nilsson M, Chamberland M, Anderson A, "
    "Landman B, Descoteaux M. White matter geometry confounds diffusion tensor "
    "imaging along perivascular space (DTI-ALPS) measures. Human Brain Mapping. "
    "2025;46(10):e70282. doi:10.1002/hbm.70282",

    "Qiu E, Chaganti J, Phan P, Alizadeh M, Middleton D, Talekar K, Mondel PK, "
    "Faro SH, Mohamed FB, Yuan H. Reliability and spatial consistency of MR "
    "diffusion tensor imaging measures along the cerebral perivascular space. "
    "Journal of Neuroimaging. 2025;35(5):e70086. doi:10.1111/jon.70086",

    "Power JD, Barnes KA, Snyder AZ, Schlaggar BL, Petersen SE. Spurious but "
    "systematic correlations in functional connectivity MRI networks arise from "
    "subject motion. NeuroImage. 2012;59(3):2142-2154. "
    "doi:10.1016/j.neuroimage.2011.10.018",

    "Andersson JLR, Sotiropoulos SN. An integrated approach to correction for "
    "off-resonance effects and subject movement in diffusion MR imaging. "
    "NeuroImage. 2016;125:1063-1078. doi:10.1016/j.neuroimage.2015.10.019",

    "Andersson JLR, Skare S, Ashburner J. How to correct susceptibility "
    "distortions in spin-echo echo-planar images: application to diffusion tensor "
    "imaging. NeuroImage. 2003;20(2):870-888. "
    "doi:10.1016/S1053-8119(03)00336-7",

    "Kellner E, Dhital B, Kiselev VG, Reisert M. Gibbs-ringing artifact removal "
    "based on local subvoxel-shifts. Magnetic Resonance in Medicine. "
    "2016;76(5):1574-1581. doi:10.1002/mrm.26054",

    "Smith SM. Fast robust automated brain extraction. Human Brain Mapping. "
    "2002;17(3):143-155. doi:10.1002/hbm.10062",

    "Basser PJ, Mattiello J, LeBihan D. MR diffusion tensor spectroscopy and "
    "imaging. Biophysical Journal. 1994;66(1):259-267. "
    "doi:10.1016/S0006-3495(94)80775-1",

    "Jenkinson M, Bannister P, Brady M, Smith S. Improved optimization for the "
    "robust and accurate linear registration and motion correction of brain "
    "images. NeuroImage. 2002;17(2):825-841. doi:10.1006/nimg.2002.1132",

    "Jenkinson M, Beckmann CF, Behrens TEJ, Woolrich MW, Smith SM. FSL. "
    "NeuroImage. 2012;62(2):782-790. doi:10.1016/j.neuroimage.2011.09.015",

    "Tournier JD, Smith R, Raffelt D, Tabbara R, Dhollander T, Pietsch M, "
    "Christiaens D, Jeurissen B, Yeh CH, Connelly A. MRtrix3: A fast, flexible "
    "and open software framework for medical image processing and visualisation. "
    "NeuroImage. 2019;202:116137. doi:10.1016/j.neuroimage.2019.116137",

    "Li X, Morgan PS, Ashburner J, Smith J, Rorden C. The first step for "
    "neuroimaging data analysis: DICOM to NIfTI conversion. Journal of "
    "Neuroscience Methods. 2016;264:47-56. doi:10.1016/j.jneumeth.2016.03.001",

    "Liu X, Barisano G, Shao X, Jann K, Ringman JM, Lu H, Arfanakis K, Caprihan A, "
    "DeCarli C, Gold BT, Maillard P, Satizabal CL, Fadaee E, Habes M, Stables L, "
    "Singh H, Fischl B, van der Kouwe A, Schwab K, Helmer KG, Greenberg SM, "
    "Wang DJJ; MarkVCID Consortium. Cross-vendor test-retest validation of "
    "diffusion tensor image analysis along the perivascular space (DTI-ALPS) for "
    "evaluating glymphatic system function. Aging and Disease. "
    "2024;15(4):1885-1898. doi:10.14336/AD.2023.0321-2",

    # ---- Reference implementation: the authoritative source for what this
    # ---- repository calls the "reference implementation" (see citations.py)
    _C.CITATION_REF_SOFTWARE,
]


def references_text() -> str:
    """Body of the References page."""
    if i18n.get_lang() == "en":
        head = ("References for the methods and tools used by ALPSbox. If you use "
                "ALPSbox, please cite (1) the original ALPS method paper "
                "(Taoka 2017), (2) the reference-implementation software "
                "citation and its accompanying paper (Liu & Barisano 2024), and "
                "(3) the tool papers listed below, in addition to ALPSbox itself.")
        tail = ("Terminology: ALPS has no official/standard certified "
                "implementation. Throughout this repository, 'reference "
                "implementation' means gbarisano/alps on GitHub (MIT License); "
                "the four bundled ROI masks are reproduced from that repository. "
                "ALPSbox does not redistribute FSL or MRtrix3.")
    else:
        head = ("本页列出 ALPSbox 所用方法与工具的原始文献。引用 ALPSbox 时，"
                "除本工具本身外，建议至少引用：（1）ALPS 方法原始文献 Taoka 2017；"
                "（2）参考实现 gbarisano/alps 的软件引用及其配套论文 "
                "Liu & Barisano 2024；（3）本页所列的各工具文献。")
        tail = ("术语说明：ALPS 没有官方/标准认证实现。本仓库中的「参考实现」"
                "一律专指 GitHub 上的 gbarisano/alps（MIT License）；"
                "随包四个 ROI 掩膜复制自该仓库。本工具不打包 FSL / MRtrix3，"
                "也不包含其代码。")
    lines = [head, ""]
    for i, ref in enumerate(REFERENCES, 1):
        lines.append("[%d] %s" % (i, ref))
        lines.append("")
    lines.append(tail)
    return "\n".join(lines)
