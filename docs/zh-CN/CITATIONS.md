# 引用与第三方来源（Citations & Provenance）

本页是 ALPSbox 发布版的**正式引用信息**。若你只想知道"发表时该引什么"，
看 §1 即可；想知道"工具里的『参考实现 / 随包参考 ROI』到底指什么"，看 §2。

---

## 1. 引用本工具（软件引用）

尚未发表论文时的软件引用格式（GitHub 发布后建议用 Zenodo DOI 替换）：

> ALPSbox contributors. *ALPSbox: one-click DTI-ALPS processing with quality
> control and HTML reports*. Version 1.0.0. GitHub; 2026.
> https://github.com/czf-chen/alpsbox

归档版本：ALPSbox v1.0.0。*Zenodo*。doi:10.5281/zenodo.24137518（https://doi.org/10.5281/zenodo.24137518）

仓库内提供了机器可读的 `CITATION.cff`（GitHub 会显示 "Cite this repository"）。
**正式发表后请以论文引用为准。**

---

## 2. 术语：什么是"参考实现"（旧文档中的"官方 alps.sh"）

**ALPS 指数没有官方标准或认证实现。** 本仓库中所有
「参考实现」（旧文档中的「官方 alps.sh」「参考实现（gbarisano/alps）」「参考实现流程」）**一律专指**：

> Barisano G. *alps: Bash script to compute DTI-ALPS (alps.sh)*.
> GitHub repository. <https://github.com/gbarisano/alps>.
> Commit `e6f58e7c1b882a799b613e91fe15bab940dc4cd3`（2025-09-12）.
> Accessed 2026-11-11. **MIT License**.

该仓库 README 要求使用其脚本时同时引用配套论文：

> Liu X, Barisano G, et al. Cross-vendor test-retest validation of diffusion
> tensor image analysis along the perivascular space (DTI-ALPS) for evaluating
> glymphatic system function. *Aging and Disease*. 2024;15(4):1885-1898.
> doi:[10.14336/AD.2023.0321-2](https://doi.org/10.14336/AD.2023.0321-2)

ALPS 方法本身出自：

> Taoka T, Masutani Y, Kawai H, Nakane T, Matsuoka K, Yasuno F, Kishimoto T,
> Naganawa S. Evaluation of glymphatic system activity with the diffusion MR
> technique: diffusion tensor image analysis along the perivascular space
> (DTI-ALPS) in Alzheimer's disease cases. *Japanese Journal of Radiology*.
> 2017;35(4):172-178.
> doi:[10.1007/s11604-017-0617-z](https://doi.org/10.1007/s11604-017-0617-z)

### 2.1 参考实现的默认设置 ≠ 本工具默认设置

| 项目 | 参考实现默认 | 本工具默认 |
|---|---|---|
| 张量变换 | `-f 1`：flirt/applywarp 直接变换（**不重定向张量**） | `vecreg`（等价参考的 `-f 2`） |
| 预处理 | `-d 1`：去噪 + 去振铃 | 只去振铃（等价 `-d 3`），去噪可选 |
| eddy 程序 | `-e 1`：eddy_cpu | GPU eddy（自动探测） |
| 配准代价 | flirt 默认 `corratio` | `normmi`（`--reg-cost` 可切） |
| ROI | 2.5 mm 半径球（2025-05-28 起） | 同一套随包掩膜 |

因此，"与参考实现差多少"必须说明**两边实际运行参数**，否则数值不可比。
本工具的跨实现验证是把参考脚本做参数对齐补丁后运行的
（`-d 3 -e eddy_cuda11.0 -r 2.5 -t 1 -f 2`，配准代价 patch 为 normmi），
详见 [docs/zh-CN/VALIDATION.md](VALIDATION.md)。

---

## 3. 随包 ROI 掩膜的来源与许可

`alpsbox/data/ROIs_JHU_ALPS/` 下的 4 个掩膜复制自参考实现仓库的
`ROIs_JHU_ALPS/` 目录（**MIT License**, Copyright (c) 2023 Giuseppe Barisano；
全文见 `LICENSE_Barisano_alps.txt`）：

- 2.5 mm 半径球（= 5 mm 直径，与 Taoka 2017 一致），位于
  `JHU-ICBM-FA-1mm.nii.gz` 模板空间，每个 ROI 81 体素；
- 该默认值由参考实现仓库 2025-05-28 更新说明确立（此前为 5 mm 半径球）；
- 文件 sha256、逐文件说明与核验方法见
  `alpsbox/data/ROIs_JHU_ALPS/PROVENANCE.md`。

---

## 4. 方法学引用（按处理步骤）

| 步骤 | 文献 |
|---|---|
| 去 Gibbs 振铃（mrdegibbs） | Kellner E, Dhital B, Kiselev VG, Reisert M. Gibbs-ringing artifact removal based on local subvoxel-shifts. *Magnetic Resonance in Medicine*. 2016;76(5):1574-1581. doi:10.1002/mrm.26054 |
| 涡流/头动/离群切片校正（eddy, --repol） | Andersson JLR, Sotiropoulos SN. An integrated approach to correction for off-resonance effects and subject movement in diffusion MR imaging. *NeuroImage*. 2016;125:1063-1078. doi:10.1016/j.neuroimage.2015.10.019 |
| 脑提取（bet） | Smith SM. Fast robust automated brain extraction. *Human Brain Mapping*. 2002;17(3):143-155. doi:10.1002/hbm.10062 |
| 张量拟合（dtifit） | Basser PJ, Mattiello J, LeBihan D. MR diffusion tensor spectroscopy and imaging. *Biophysical Journal*. 1994;66(1):259-267. doi:10.1016/S0006-3495(94)80775-1 |
| 线性配准（flirt） | Jenkinson M, Bannister P, Brady M, Smith S. Improved optimization for the robust and accurate linear registration and motion correction of brain images. *NeuroImage*. 2002;17(2):825-841. doi:10.1006/nimg.2002.1132 |
| 张量重定向（vecreg / T'=R·T·Rᵀ） | Alexander DC, Pierpaoli C, Basser PJ, Gee JC. Spatial transformations of diffusion tensor magnetic resonance images. *IEEE Transactions on Medical Imaging*. 2001;20(11):1131-1139. doi:10.1109/42.963816；Tatekawa H, et al. Improved reproducibility of DTI-ALPS index: an analysis of reorientation technique of the OASIS-3 dataset. *Japanese Journal of Radiology*. 2023;41(4):393-400. doi:10.1007/s11604-022-01370-2 |
| 配准稳健性 / 几何混杂（`--regqc` 依据） | Ajouz A, et al. Automatic determination of glymphatic flow with the DTI-ALPS-index along the principal axis system in native imaging space corrects for head and fiber orientation. *Magnetic Resonance in Medicine*. 2026;95(2):1110-1122. doi:10.1002/mrm.70082；Schilling KG, et al. White matter geometry confounds diffusion tensor imaging along perivascular space (DTI-ALPS) measures. *Human Brain Mapping*. 2025;46(10):e70282. doi:10.1002/hbm.70282 |
| DTI-ALPS 的可靠性与空间一致性（质控语境） | Qiu E, et al. Reliability and spatial consistency of MR diffusion tensor imaging measures along the cerebral perivascular space. *Journal of Neuroimaging*. 2025;35(5):e70086. doi:10.1111/jon.70086 |
| 头动质控（framewise displacement） | Power JD, Barnes KA, Snyder AZ, Schlaggar BL, Petersen SE. Spurious but systematic correlations in functional connectivity MRI networks arise from subject motion. *NeuroImage*. 2012;59(3):2142-2154. doi:10.1016/j.neuroimage.2011.10.018 |
| ALPS 指数定义 | Taoka T, et al. 2017（见 §2） |
| TOPUP 畸变校正 | Andersson JLR, Skare S, Ashburner J. How to correct susceptibility distortions in spin-echo echo-planar images: application to diffusion tensor imaging. *NeuroImage*. 2003;20(2):870-888. doi:10.1016/S1053-8119(03)00336-7 |

---

## 5. 第三方软件

本工具**不打包** FSL 与 MRtrix3，只调用用户自行安装的程序：

- **FSL**（FMRIB Software Library）：Jenkinson M, Beckmann CF, Behrens TEJ,
  Woolrich MW, Smith SM. FSL. *NeuroImage*. 2012;62(2):782-790.
  doi:10.1016/j.neuroimage.2011.09.015。许可证限制为非商业用途、禁止再分发。
- **MRtrix3**：Tournier JD, et al. MRtrix3: A fast, flexible and open software
  framework for medical image processing and visualisation. *NeuroImage*.
  2019;202:116137. doi:10.1016/j.neuroimage.2019.116137。
- **dcm2niix**（可选）：Li X, Morgan PS, Ashburner J, Smith J, Rorden C.
  The first step for neuroimaging data analysis: DICOM to NIfTI conversion.
  *Journal of Neuroscience Methods*. 2016;264:47-56.
  doi:10.1016/j.jneumeth.2016.03.001。

---

## 6. 我们做了什么、没做什么（避免误引）

- **没做**：我们没有提出新的 ALPS 定义，也没有修改参考实现的发布内容；
  参考实现的所有权与许可归 Giuseppe Barisano（MIT）。
- **做了**：独立的 Python 实现（FSL 编排 + GUI + 质控 + 报告），
  并用参数对齐后的参考实现做了跨实现一致性验证（30 例外部数据
  r = 0.994，见 [docs/zh-CN/VALIDATION.md](VALIDATION.md)）。
- 若你的论文只引用"参考实现"而漏掉 Taoka 2017，方法学出处是不完整的；
  反之若只引 Taoka 2017 而不提 gbarisano/alps，读者无法复现我们的实现细节。
  建议两者都引。

---

## 7. 验证用数据集

外部队列为公开的 UCLA Consortium for Neuropsychiatric Phenomics LA5c Study，
以 OpenNeuro `ds000030` 数据集形式发布（CC0 许可；访问日期 2026-11-11）：

- Poldrack RA, Congdon E, Triplett W, Gorgolewski KJ, Karlsgodt KH, Mumford JA,
  Sabb FW, Freimer NB, London ED, Cannon TD, Bilder RM. A phenome-wide
  examination of neural and cognitive function. *Scientific Data*.
  2016;3:160110. doi:10.1038/sdata.2016.110
- UCLA Consortium for Neuropsychiatric Phenomics LA5c Study. *OpenNeuro*.
  数据集 `ds000030`，版本 1.0.0。
  doi:10.18112/openneuro.ds000030.v1.0.0
  （https://openneuro.org/datasets/ds000030）

内部验证队列不再分发（被试隐私）；[VALIDATION.md](VALIDATION.md) 只报告汇总结果。
每个被试的 ALPS 处理参数由工具记录在各自的 `alps_result.json` 中；
完整实验记录可向作者索取。
