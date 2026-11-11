# -*- coding: utf-8 -*-
"""Help-page bodies (Chinese and English). Called from helptext.page()."""
from __future__ import annotations

from . import citations as _C
from . import i18n

_ZH = {
    "quickstart": """三步开始

1. 选输入
   单个被试就选那个被试的文件夹；批量就选队列根目录，程序把每个子文件夹当成一个被试。

2. 选输出目录
   每个被试会在输出目录下有一个同名子文件夹。已经有结果的会自动跳过，可中断续跑。

3. 点开始处理
   底部有两条进度条，上面是整体进度，下面显示当前被试走到第几步。
   处理中随时可以点停止，程序会在当前被试跑完后才停下，不会留下半截文件。

建议先跑一次“先检查输入”

这一步只做文件匹配，不碰图像，几秒钟就能把每个被试的情况列出来：
能不能找到 DWI、bval 和 bvec 配不配套、json 够不够做完整 eddy。
它能在开始处理前把缺文件、不配套的输入列出来。

结果在哪里

界面的结果页会自动保存，关掉再打开还在，不用手动存。
实时日志在日志页，可以另存成 txt。
磁盘上的位置是“输出目录/被试名/”，里面有 alps_result.json 和各类中间文件。
整批跑完还会在输出目录根部生成 alps_summary.csv 和 qc_report.txt。

每个被试要多久

18 个体积的数据大约 9 到 10 分钟，66 个体积的大约 14 到 15 分钟。
时间基本都花在 eddy 上，大约占八成，这是计算量决定的，换参数也压不下来多少。

结果怎么带走

结果页可以导出 CSV 或 JSON。也可以把以前导出的表用“导入结果”合并回来，
同名的被试会被新的覆盖。

想先看看效果

examples/demo_synthetic_cohort 里有一份合成数据，可以直接导入。
里面有十个虚构被试，质控的四种判定都能看到，双击任意一行能看头动曲线。

本工具只管每个被试的 ALPS 与质控

组间比较、前后测等统计分析属于下游工作，不在本工具范围内。
本工具的输出（alps_summary.csv / JSON / HTML 报告）可以直接交给
R、Python、SPSS 等做后续统计。
""",

    "input": """每个被试目录里需要什么

至少一套同名的三件套：四维 DWI（.nii 或 .nii.gz）、同名的 .bval、同名的 .bvec。
名字必须一致，例如：

    sub_001/DTI1/20251213_155452.nii.gz
    sub_001/DTI1/20251213_155452.bval
    sub_001/DTI1/20251213_155452.bvec

程序判断 DWI 的依据就是“同名的 bval 和 bvec 都存在”。这样即使目录里
同时放着 projection.nii.gz、association.nii.gz 这类 ROI 文件也不会选错。
放在子目录里同样能自动找到。

最好再补一个 json

同目录下的 .json 是 dcm2niix 生成的 BIDS sidecar。只有拿到它，
程序才能用完整 eddy，因为 eddy 需要里面的相位编码方向（PhaseEncodingDirection）
和读出时间（TotalReadoutTime）。

没有 json 时会退回 eddy_correct。这个老命令有已知偏差（扩散率与各向异性会被低估），所以能补 json 就补。

怎么补 json

不用重转图像，直接在原始 DICOM 目录上跑下面这条命令，-b o 表示只输出 json：

    dcm2niix -b o -o /tmp/out -f "%f_%p_%s" /path/to/SUBJECT/DTI1

把生成的 .json 拷到 nii 旁边就行。

json 的文件名不需要和 nii 一致

程序按内容匹配，优先选 SeriesDescription 或 ProtocolName 里含 DTI、DWI 的那个。
日志里会写一句“json 文件名与 nii 不一致，按内容匹配”，看到这句不用紧张。

批量模式的目录结构

    队列根目录/
      ├─ sub_001/    一个被试
      ├─ sub_002/    一个被试
      └─ sub_003/    一个被试

每个子文件夹里的要求和单个被试完全相同。子文件夹之外的散文件不会被处理。
""",

    "install": """ALPSbox 需要什么

必需的是 Python 3.9 以上和 FSL 6.0.3 以上。FSL 里必须有 eddy、bet、dtifit、
flirt、vecreg、fslroi、fslmaths、fslstats、fslval 这几个命令。

MRtrix3 用来去 Gibbs 振铃，dcm2niix 用来把 DICOM 转成 NIfTI，这两个是可选的，
缺了不影响主流程，只是少做一步或者少一种输入格式。

为什么 ALPSbox 不带 FSL

FSL 的许可证只允许非商业使用，而且明确禁止再分发。所以 FSL 必须由使用者
自己安装，ALPSbox 只负责调用。这和 DPABI 要求你先装 MATLAB 和 SPM 是一个道理。

在一台新机器上装

第一步，装 WSL。Windows 下用管理员权限打开 PowerShell，执行：

    wsl --install -d Ubuntu

装完重启，设好用户名和密码。用 wsl -l -v 确认能看到 Ubuntu。

第二步，装 FSL。在 WSL 里执行：

    cd ~
    wget https://fsl.fmrib.ox.ac.uk/fsldownloads/fslinstaller.py
    python3 fslinstaller.py

装完把环境变量写进 ~/.bashrc：

    export FSLDIR=$HOME/fsl
    . ${FSLDIR}/etc/fslconf/fsl.sh
    export PATH=${FSLDIR}/bin:$PATH

然后 source ~/.bashrc，用 fsl-config --version 和 which eddy bet dtifit flirt vecreg
确认装好了。

第三步，装 MRtrix3。推荐用 conda，先装 miniforge 再建环境：

    conda create -n mrtrix -c conda-forge -c bioconda --channel-priority flexible mrtrix3=3.0.8 -y
    export PATH=$HOME/miniforge3/envs/mrtrix/bin:$PATH

装完用 which mrdegibbs 确认。

第四步，装 ALPSbox。把 alpsbox 文件夹拷到目标机器，然后：

    cd /path/to/alpsbox
    python3 -m pip install -e . --no-build-isolation

用 --no-build-isolation 可以避免联网下载构建依赖。

第五步，启动。命令行输入 alpsbox gui，或者 Windows 下双击 ALPSbox-GUI.bat。

依赖不满足时怎么办

点界面右上角的环境详情，会逐项列出每个命令找到还是缺失、在哪里，
缺失时给出对应的修复命令。对话框里有复制诊断信息按钮，
可以直接把结果粘给能帮你排查的人。

各项缺失的影响

FSL 或其中任何一个必需命令缺失，程序无法处理。
缺 MRtrix3 只会跳过去振铃，结果仍然有效。
缺 dcm2niix 只影响 DICOM 输入，已经是 NIfTI 的话不需要。
没有 eddy_cuda 也没关系，会回落到 CPU 版 eddy，只是慢五到十倍。
""",

    "trouble": """双击 bat 闪一下就没了

检查是不是用了 ALPSbox-GUI.bat（这个文件是 CRLF 换行，Windows 批处理要求如此）。
另外那个黑色命令行窗口不要关，关掉它 GUI 也就关了。
还不行就看日志 ~/.alpsbox/gui.log，里面有启动时的路径、DISPLAY 和 Python 位置。

提示 command not found

说明 FSL 的 bin 目录不在 PATH 里。先执行 source ~/.bashrc，
或者直接用绝对路径 $FSLDIR/bin/alpsbox gui。

命令行启动但窗口不出现

需要 WSLg，Windows 11 自带。用 echo $DISPLAY 检查，应该有类似 :0 的值。
如果为空，run_gui.sh 里会自动补成 :0，仍然不行就是 WSLg 没启用。

报错未找到 FSL

设置 export FSLDIR=/你的/fsl/路径，并确认 ls $FSLDIR/bin/eddy 这个文件存在。

报错 TotalReadoutTime 超出 0.01 到 0.2

json 里的单位写成毫秒了，应该是秒。这个范围是 FSL eddy 源码里写死的检查。

报错 bvec 列数不等于体积数

bval 和 bvec 跟 nii 不是同一套。用先检查输入能提前发现这种情况。

ROI 体素数不等于 81

配准失败或者图像有问题。看该被试目录下的 FA_in_mni.nii.gz 配准结果，
以及质控页的 r_wm。r_wm 低于 0.9 说明配准质量不好。

所有被试都退回了 eddy_correct

说明没有找到 json。用 dcm2niix -b o 补 json，具体命令见输入数据要求那页。

每次跑出来的数值都不一样

这是 eddy 本身的特性，不是 bug。FSL 文档说明 eddy 不是确定性算法，
同一份数据重跑两次结果会有细微差别；个体层面不要过度解释很小的差异，
跨研究比较时请报告处理参数。

头动数据缺失或想补算

用 alpsbox rescan 可以从已有的 eddy 输出重算，不重跑处理：

    alpsbox rescan /结果目录
    alpsbox rescan /结果目录 --json --tsv 汇总表.tsv

它读每个被试目录下的 eddy_out.eddy_movement_rms 和 eddy_outlier_report，
几秒钟能跑完上百个被试，不占显存。

跑到一半中断了

已完成的被试结果都保存着，重新打开会自动跳过他们。
想重算某个被试，勾上强制重跑，或者删掉输出目录下该被试的子文件夹。
程序判断某被试是否完成的依据就是他的目录里有没有 alps_result.json。
""",

    "method": """ALPS 指数怎么算

公式是 ALPS 等于 Dxx 在两个纤维区的平均值，除以 Dyy 和 Dzz 的平均值。

分子取的是沿血管周围间隙方向的扩散率，方向是左右。
分母取的是垂直于血管周围间隙方向的扩散率，在这里投射区取 Dyy、联络区取 Dzz。
分母的作用是归一化，扣掉个体整体扩散水平的差异，使比值可以跨人比较。

测量位置的解剖

位置在侧脑室体部层面，放射冠区域。选这里是因为两束纤维在这里互相垂直：
投射纤维就是上放射冠，走行上下；联络纤维就是上纵束，走行前后。
血管周围间隙沿脑中动脉和静脉走，在这里垂直于上述两束纤维，也就是左右方向。

在左右方向上，纤维内部的水分子扩散被纤维膜限制，而血管周围间隙里不受限，
所以这个方向的扩散率主要反映血管周围间隙的通畅程度。

文献里的参考值大约 1.3 到 1.7，Taoka 2017 报告的认知正常对照是 1.35 加减 0.20。

处理链和每一步的依据

去 Gibbs 振铃用 mrdegibbs，依据是 Kellner 等 2016 年的方法学论文。
涡流、头动和离群切片替换用 eddy 加 repol，依据是 Andersson 和 Sotiropoulos 2016。
脑提取用 bet，依据是 Smith 2002。
张量拟合用 dtifit 加 save_tensor，依据是 Basser 等 1994。
配准用 flirt 十二自由度，把 FA 配到 JHU-ICBM-FA-1mm，依据是 Jenkinson 等 2002。
张量重定向用 vecreg，这一步不能省，依据是 Alexander 等 2001 和 Tatekawa 等 2023。
取 Dxx、Dyy、Dzz 用 fslroi 取第 0、3、5 个分量。
ROI 内均值用 fslstats，最后按公式算指数。

为什么一定要做张量重定向

扩散张量是二阶张量，把图像配准到模板空间时，张量本身也必须按
T' 等于 R 乘 T 乘 R 的转置 这个规律旋转。直接把 Dxx、Dyy、Dzz 当三个独立
标量搬到模板空间是错的。

Tatekawa 等 2023 在 OASIS-3 数据上验证过：不做重定向时，观察者间与观察者内
组内相关系数只有 0.52 到 0.81；做了重定向之后提高到 0.85 以上。

ROI 定义

随附的四个掩膜来自 gbarisano/alps，MIT 许可。它们在 JHU-ICBM-FA-1mm 模板上
画成 2.5 毫米半径的球，每个 81 个体素。L_SCR 和 R_SCR 分别是左侧和右侧
上放射冠，L_SLF 和 R_SLF 分别是左侧和右侧上纵束。

这个方法目前没有公认的方法学共识指南，所以引用时宜表述为
“沿用 Taoka 原始文献的方法学定义，按 FSL 标准工具实现，
并参照 gbarisano/alps 的 ROI 方案”，这种说法准确也站得住。
""",


}


_EN = {
    "quickstart": """Three steps

1. Choose the input
   For one subject pick that subject's folder. For a batch pick the cohort root;
   every subfolder becomes one subject.

2. Choose the output folder
   Each subject gets a subfolder of the same name. Completed subjects are skipped
   automatically so an interrupted run can resume.

3. Click Start
   Two progress bars sit at the bottom: overall progress above, current step below.
   You can stop at any time; the current subject finishes first, so nothing is left
   half-written.

Run "Check inputs" first

It only matches files and never touches image data, so within seconds it reports
whether each subject has a DWI, whether bval and bvec match, and whether the JSON
carries enough for full eddy. It lists missing or mismatched inputs before processing starts.

Where the results are

The results page saves automatically and survives a restart; no manual save needed.
The live log is on the Log page and can be exported as text.
On disk look in <output folder>/<subject>/ for alps_result.json and the
intermediates. A finished batch also writes alps_summary.csv and qc_report.txt at
the output root.

How long each subject takes

About 9-10 minutes for 18 volumes and 14-15 minutes for 66 volumes. Roughly 80% of
that is eddy and is dictated by the computation, not by the settings.

Taking the results with you

Export CSV or JSON from the results page. Earlier exports can be merged back with
"Import"; records sharing a subject ID are replaced by the newer one.

Want to see it working first

examples/demo_synthetic_cohort contains synthetic data you can import directly.
It has ten fictional subjects covering all four QC grades, and double-clicking any
row shows the motion time course.

What this tool does and does not do

ALPSbox computes per-subject ALPS values and quality-control metrics.
Group comparisons and statistical analysis are downstream tasks outside the
scope of this tool. Its outputs (alps_summary.csv / JSON / HTML reports) are
ready to be imported into R, Python, SPSS or similar for that analysis.
""",

    "input": """What each subject folder needs

At least one matched triple: a 4D DWI (.nii or .nii.gz), a same-named .bval and a
same-named .bvec. The names must match, for example:

    sub_001/DTI1/20251213_155452.nii.gz
    sub_001/DTI1/20251213_155452.bval
    sub_001/DTI1/20251213_155452.bvec

A file is treated as the DWI only when a same-named .bval and .bvec both exist.
That way stray ROI files such as projection.nii.gz or association.nii.gz in the same
folder are never chosen by mistake. Subfolders are searched as well.

A JSON sidecar is strongly recommended

The .json written by dcm2niix is a BIDS sidecar. Only with it can ALPSbox run full
eddy, because eddy needs PhaseEncodingDirection and TotalReadoutTime from it.

Without a JSON the pipeline falls back to eddy_correct, which has known biases (diffusivity and anisotropy are underestimated). So supply the JSON when you can.

How to produce one

You do not need to re-export the images. Run this on the original DICOM folder;
-b o means JSON only:

    dcm2niix -b o -o /tmp/out -f "%f_%p_%s" /path/to/SUBJECT/DTI1

Then copy the resulting .json next to the NIfTI.

The JSON file name need not match the NIfTI

Matching is by content, preferring a SeriesDescription or ProtocolName containing
DTI or DWI. The log notes "json file name differs from nii, matched by content";
that message is expected and harmless.

Folder layout for batch mode

    cohort root/
      +- sub_001/    one subject
      +- sub_002/    one subject
      +- sub_003/    one subject

Requirements inside each subfolder are identical to the single-subject case. Loose
files outside the subfolders are ignored.
""",

    "install": """What ALPSbox needs

Python 3.9+ and FSL 6.0.3+. FSL must provide eddy, bet, dtifit, flirt, vecreg,
fslroi, fslmaths, fslstats and fslval.

MRtrix3 supplies Gibbs unringing and dcm2niix handles DICOM input. Both are
optional: without them you lose one preprocessing step or one input format.

Why FSL is not bundled

FSL's licence permits non-commercial use only and explicitly forbids redistribution,
so it must be installed by the user; ALPSbox only calls it. This is the same
arrangement DPABI has with MATLAB and SPM.

Installing on a new machine

Step 1, install WSL. In an administrator PowerShell on Windows:

    wsl --install -d Ubuntu

Reboot, set a username and password, and confirm with wsl -l -v.

Step 2, install FSL. Inside WSL:

    cd ~
    wget https://fsl.fmrib.ox.ac.uk/fsldownloads/fslinstaller.py
    python3 fslinstaller.py

Then add the environment to ~/.bashrc:

    export FSLDIR=$HOME/fsl
    . ${FSLDIR}/etc/fslconf/fsl.sh
    export PATH=${FSLDIR}/bin:$PATH

Run source ~/.bashrc and verify with fsl-config --version and
which eddy bet dtifit flirt vecreg.

Step 3, install MRtrix3. conda is the easiest route:

    conda create -n mrtrix -c conda-forge -c bioconda --channel-priority flexible mrtrix3=3.0.8 -y
    export PATH=$HOME/miniforge3/envs/mrtrix/bin:$PATH

Verify with which mrdegibbs.

Step 4, install ALPSbox. Copy the alpsbox folder over, then:

    cd /path/to/alpsbox
    python3 -m pip install -e . --no-build-isolation

--no-build-isolation avoids downloading build dependencies.

Step 5, launch. Run alpsbox gui on the command line, or double-click
ALPSbox-GUI.bat on Windows.

When dependencies are missing

Click "Environment" in the top right for a per-command report showing what was
found, where, and the matching fix command. The dialog has a "Copy diagnostics"
button you can paste into a message for whoever is helping.

What each missing item costs

Any missing FSL requirement blocks processing entirely.
Missing MRtrix3 only skips unringing; results remain valid.
Missing dcm2niix only affects DICOM input; existing NIfTI files are unaffected.
No eddy_cuda is fine: the pipeline falls back to CPU eddy, five to ten times slower.
""",

    "trouble": """Double-clicking the .bat does nothing

Check that you are using ALPSbox-GUI.bat, which has CRLF line endings as Windows
batch files require. Do not close the black console window; closing it closes the
GUI too. If it still fails, read ~/.alpsbox/gui.log, which records the paths,
DISPLAY and Python interpreter used at launch.

"command not found"

FSL's bin directory is not on PATH. Run source ~/.bashrc, or call the absolute path
$FSLDIR/bin/alpsbox gui.

The window never appears from the command line

WSLg is required; Windows 11 ships it. Check echo $DISPLAY, which should show
something like :0. If it is empty, run_gui.sh sets it to :0 automatically; if that
still fails, WSLg is not enabled.

"FSL not found"

Set export FSLDIR=/your/fsl/path and verify that $FSLDIR/bin/eddy exists.

"TotalReadoutTime outside 0.01 to 0.2"

The JSON gives the value in milliseconds; it must be seconds. That range is a hard
check in the FSL eddy source.

"bvec columns do not match the number of volumes"

bval and bvec belong to a different acquisition than the NIfTI. "Check inputs"
catches this before any processing.

"ROI voxel count is not 81"

Registration failed or the image is unusual. Inspect FA_in_mni.nii.gz for that
subject and the r_wm value on the QC page; r_wm below 0.9 indicates poor
registration.

Every subject fell back to eddy_correct

No JSON was found. Add them with dcm2niix -b o; the command is on the Input
requirements page.

Numbers differ between runs

That is eddy's nature, not a bug: FSL documents that eddy is not deterministic,
so re-running the same data gives slightly different results. Avoid over-interpreting
very small differences at the individual level, and report the processing
parameters when comparing studies.

Missing motion data, or wanting to recompute it

alpsbox rescan recomputes from existing eddy output without re-running anything:

    alpsbox rescan /results
    alpsbox rescan /results --json --tsv summary.tsv

It reads eddy_out.eddy_movement_rms and eddy_outlier_report from each subject
folder, finishes hundreds of subjects in seconds, and needs no GPU memory.

An interrupted run

Completed subjects are already saved and are skipped when you restart. To recompute
one, tick "Force re-run" or delete that subject's output subfolder. Completion is
determined solely by the presence of alps_result.json.
""",

    "method": """How the ALPS index is computed

ALPS is the mean Dxx across two fibre regions divided by the mean of Dyy and Dzz.

The numerator is diffusivity along the perivascular space, which lies left-right.
The denominator is diffusivity perpendicular to it: Dyy in the projection region and
Dzz in the association region. The denominator normalises out each subject's overall
diffusivity level so the ratio is comparable across people.

Anatomy of the measurement site

The site is the corona radiata at the level of the lateral ventricle bodys.
It is chosen because the two fibre bundles are perpendicular there: projection
fibres (superior corona radiata) run head-foot and association fibres (superior
longitudinal fasciculus) run anterior-posterior. Perivascular spaces follow the
cerebral arteries and veins, which at this level are perpendicular to both bundles,
i.e. left-right.

Along left-right, water inside fibres is constrained by membranes while water in the
perivascular space is not, so diffusivity in this direction mainly reflects how
freely the perivascular space conducts.

Published values are roughly 1.3 to 1.7; Taoka 2017 reported 1.35 +/- 0.20 in
cognitively normal controls.

Pipeline and the reference behind each step

Gibbs unringing uses mrdegibbs, following Kellner, Dhital, Kiselev and Reisert
(2016).
Eddy-current, motion and outlier-slice correction uses eddy with repol, following
Andersson and Sotiropoulos (2016).
Brain extraction uses bet, following Smith (2002).
Tensor fitting uses dtifit with save_tensor, following Basser, Mattiello and
LeBihan (1994).
Registration uses flirt with 12 DOF to warp FA into JHU-ICBM-FA-1mm, following
Jenkinson, Bannister, Brady and Smith (2002).
Tensor reorientation uses vecreg, which is not optional, following Alexander,
Pierpaoli, Basser and Gee (2001) and Tatekawa, Matsushita, Ueda, Takita, Horiuchi,
Atsukawa, Morishita, Tsukamoto, Shimono and Miki (2023).
Dxx, Dyy and Dzz are taken with fslroi from components 0, 3 and 5.
ROI means come from fslstats, and the index follows the formula above.

Why tensor reorientation is mandatory

The diffusion tensor is a second-order tensor. When an image is registered to
template space the tensor itself must be rotated as T' = R * T * R^T. Copying Dxx,
Dyy and Dzz into template space as three independent scalars is wrong.

Tatekawa, Matsushita, Ueda, Takita, Horiuchi, Atsukawa, Morishita, Tsukamoto,
Shimono and Miki (2023) demonstrated this on OASIS-3: without reorientation the
intra- and inter-rater intraclass correlation was only 0.52-0.81; with
reorientation it rose above 0.85.

ROI definition

The four bundled masks come from gbarisano/alps under the MIT licence. They are
2.5 mm radius spheres on the JHU-ICBM-FA-1mm template, 81 voxels each. L_SCR and
R_SCR are the left and right superior corona radiata; L_SLF and R_SLF are the left
and right superior longitudinal fasciculus.

No methodological consensus guideline exists for this index yet, so the accurate way
to describe it is: "following the methodological definition of the original Taoka
paper, implemented with standard FSL tools, using the ROI scheme of gbarisano/alps".
""",


}


def _reference_block(lang: str) -> str:
    """Reference-implementation and formal-citation block appended to the
    methodology page."""
    if lang == "en":
        return (
            "\n\nReference implementation and formal citations\n\n"
            "ALPS has no official or standard-certified implementation. In this "
            "repository, \"reference implementation\" (also called \"official\" "
            "in older documentation) always means:\n\n"
            + _C.CITATION_REF_SOFTWARE + "\n\n"
            "Accompanying paper required by that repository:\n\n"
            + _C.CITATION_REF_PAPER + "\n\n"
            "Original ALPS method:\n\n"
            + _C.CITATION_ALPS_METHOD + "\n\n"
            "The four bundled ROI masks are reproduced from the "
            "ROIs_JHU_ALPS/ directory of that repository (MIT License, "
            "Copyright (c) 2023 Giuseppe Barisano). Provenance and sha256 "
            "checksums: alpsbox/data/ROIs_JHU_ALPS/PROVENANCE.md. A machine "
            "readable citation file is at the repository root (CITATION.cff); "
            "see also docs/CITATIONS.md."
        )
    return (
        "\n\n参考实现与正式引用\n\n"
        "ALPS 指数没有官方或标准认证实现。本仓库中的「参考实现」"
        "（旧文档中也叫「官方实现 / 官方 alps.sh」）一律专指：\n\n"
        + _C.CITATION_REF_SOFTWARE + "\n\n"
        "该仓库要求的配套论文：\n\n"
        + _C.CITATION_REF_PAPER + "\n\n"
        "ALPS 方法原始文献：\n\n"
        + _C.CITATION_ALPS_METHOD + "\n\n"
        "随包四个 ROI 掩膜复制自该仓库的 ROIs_JHU_ALPS/ 目录"
        "（MIT License, Copyright (c) 2023 Giuseppe Barisano），"
        "来源与 sha256 校验值见 alpsbox/data/ROIs_JHU_ALPS/PROVENANCE.md。"
        "机器可读引用文件见仓库根目录 CITATION.cff，另见 docs/CITATIONS.md。"
    )


def body(key: str) -> str:
    lang = i18n.get_lang()
    table = _EN if lang == "en" else _ZH
    text = table.get(key) or _ZH.get(key, "")
    if key == "method":
        text += _reference_block(lang)
    return text
