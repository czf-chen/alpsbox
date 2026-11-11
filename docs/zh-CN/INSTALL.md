# ALPSbox 安装指南

> 面向"另一台机器上从零开始"的场景。按顺序做即可。

> **引用与第三方来源**：本工具不打包 FSL / MRtrix3（请按下面步骤自行安装），
> 随包 ROI 掩膜复制自开源参考实现 **gbarisano/alps**（MIT License）。
> 完整的软件/方法/第三方引用见仓库根目录 `CITATION.cff` 与
> [`docs/zh-CN/CITATIONS.md`](CITATIONS.md)（英文版 [`docs/CITATIONS.md`](../CITATIONS.md)）；
> ROI 来源与校验值见
> [`alpsbox/data/ROIs_JHU_ALPS/PROVENANCE.md`](../../alpsbox/data/ROIs_JHU_ALPS/PROVENANCE.md)。
> 注意：ALPS 没有「官方标准实现」；本仓库所称「参考实现」专指上述仓库。

---

## 平台说明

ALPSbox 的代码是纯 Python，跨平台。限制来自 FSL。

| 平台 | 能否直接用 | 说明 |
|---|---|---|
| Linux | 可以 | 首选 |
| WSL2（Windows） | 可以 | 需要 WSLg 显示 GUI |
| macOS | 可以 | 原生运行，Intel 与 Apple Silicon 都支持；没有 CUDA，eddy 只能 CPU（慢 5–10 倍） |
| Windows 原生 | 不行 | FSL 没有 Windows 版本，必须走 WSL |

所以下面的步骤在 Windows 上是"先装 WSL，再在 WSL 里装 FSL"；
Linux 和 macOS 跳过第 1 步，直接装 FSL（macOS 见第 2 步里的 macOS 小节）。

---

## 0. 先看你的情况

| 你的情况 | 从哪开始 |
|---|---|
| 全新机器，什么都没有 | 从第 1 步开始 |
| 已有 Ubuntu / WSL | 跳到第 2 步（装 FSL） |
| 已有 macOS 机器 | 看第 2 步的 macOS 小节（跳过 WSL） |
| 已有 FSL 6.0.3+ | 跳到第 4 步（装 ALPSbox） |

**ALPSbox 需要什么**

| 组件 | 必需 | 用途 |
|---|---|---|
| Python 3.10+ | ✅ 必需 | 运行 ALPSbox；Python 依赖（NumPy、nibabel、Pillow、matplotlib）由 `pip install -e .` 安装 |
| **FSL 6.0.3+** | ✅ **必需** | eddy / bet / dtifit / flirt / vecreg / fslroi / fslmaths / fslstats / fslval |
| mrdegibbs（MRtrix3） | 推荐 | 去 Gibbs 振铃。没有会自动跳过 |
| dcm2niix | 可选 | DICOM → NIfTI。只处理现成 NIfTI 时不需要 |
| fslcc | 建议 | 质控里的配准相关系数 r_wm。缺了该项显示「未测」，不影响 ALPS 数值 |
| tkinter | GUI 需要 | Windows/macOS 的 Python 自带；Linux `sudo apt install python3-tk` |
| pillow / matplotlib | 自动安装 | `pip install -e .` 会装（ROI 图解页、质控绘图用） |

> ⚠️ **ALPSbox 不随附 FSL。**
> FSL 的许可证只允许**非商业**使用，且**禁止再分发**。
> 所以 FSL 必须由使用者自行安装，ALPSbox 只负责调用它。
> （这和 DPABI 要求你先装 MATLAB + SPM 是一回事。）

---

## 1. 装 WSL（Windows 用户）

以**管理员**身份打开 PowerShell：

```powershell
wsl --install -d Ubuntu
```

装完重启，设置 UNIX 用户名和密码。

验证：

```powershell
wsl -l -v
```

应该看到 `Ubuntu  Running  2`。

> **GUI 显示需要 WSLg**（Windows 11 自带；Windows 10 需 21H2+ 且手动启用）。
> 验证方法：进 WSL 后 `echo $DISPLAY`，应该有值（如 `:0`）。

---

## 2. 装 FSL

在 WSL / Linux 终端里：

```bash
# 下载FSL 提供的安装脚本
cd ~
wget https://fsl.fmrib.ox.ac.uk/fsldownloads/fslinstaller.py

# 运行（默认装到 ~/fsl）
python3 fslinstaller.py
```

装完后把环境写进 `~/.bashrc`：

```bash
cat >> ~/.bashrc <<'EOF'

# FSL
export FSLDIR=$HOME/fsl
. ${FSLDIR}/etc/fslconf/fsl.sh
export PATH=${FSLDIR}/bin:$PATH
EOF

source ~/.bashrc
```

**验证**：

```bash
fsl-config --version          # 应 >= 6.0.3
which eddy bet dtifit flirt vecreg fslroi fslmaths fslstats fslval
```

**8 个命令都要能找到路径**，缺任何一个 ALPSbox 都会报错。

### 常见问题

| 现象 | 原因 | 解决 |
|---|---|---|
| `fsl-config: command not found` | PATH 没设 | `source ~/.bashrc`，检查 `echo $FSLDIR` |
| 缺 `vecreg` | FSL 版本太老 | 重装 6.0.3+ |
| 缺 atlas | 只装了核心 | `$FSLDIR/bin/fsl_install_atlases` |
| 提示缺 libtiff 等 | 系统依赖缺失 | `sudo apt install -y libtiff5 libquadmath0 dc` |

### macOS（原生安装，Intel / Apple Silicon）

macOS 不需要 WSL。FSL 项目提供的安装脚本支持 Intel 与 Apple Silicon：

```bash
curl -Ls https://fsl.fmrib.ox.ac.uk/fsldownloads/fslconda/releases/getfsl.sh | sh -s
# 看到 "FSL successfully installed" 后关闭 Terminal 再重新打开
fsl-config --version        # 应 >= 6.0.3
```

若重开后仍提示找不到 `fsl-config`，把下面一行加到 `~/.zshrc`（FSLDIR 默认
是 `~/fsl`），再开一个新终端：

```bash
. $FSLDIR/etc/fslconf/fsl.sh
```

macOS 的 GUI 依赖 tkinter：python.org 的 Python 自带；Homebrew 的 Python
不带，需要安装与其版本匹配的 `python-tk`。可以先检查：

```bash
python3 -c "import tkinter; print(tkinter.TkVersion)"
```

---

## 3. 装 MRtrix3（强烈推荐）

没有它 ALPSbox 会跳过去振铃（不致命，但少一步预处理）。

推荐用 conda：

```bash
# 如果没装 conda，先装 miniforge（Linux；macOS 用 Miniforge3-MacOSX-arm64.sh）
wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
bash Miniforge3-Linux-x86_64.sh -b -p ~/miniforge3
~/miniforge3/bin/conda init bash && source ~/.bashrc

# 装 MRtrix3（注意用 flexible channel priority，否则依赖冲突）
conda create -n mrtrix -c conda-forge -c bioconda --channel-priority flexible mrtrix3=3.0.8 -y
echo 'export PATH=$HOME/miniforge3/envs/mrtrix/bin:$PATH' >> ~/.bashrc
echo 'export MRTRIX_NTHREADS=4' >> ~/.bashrc
source ~/.bashrc
```

**验证**：

```bash
which mrdegibbs
```

macOS 补充：以上 conda 包只有 linux-64 / linux-aarch64 版本，macOS 上请用
<https://www.mrtrix.org/download/> 的 macOS 预编译包（或从源码编译）。MRtrix3
是可选项，装不上会自动跳过 Gibbs 去振铃，不影响 ALPS 数值。

---

## 4. 装 ALPSbox

把整个 `alpsbox` 文件夹拷到目标机器（或 git clone），然后：

```bash
cd /path/to/alpsbox
python3 -m pip install -e . --no-build-isolation
# 也可以只装 Python 依赖：python3 -m pip install -r requirements.txt
```

> 用 `--no-build-isolation` 可以避免联网下载构建依赖。
> 若提示缺 setuptools：`python3 -m pip install setuptools wheel`

**验证**：

```bash
alpsbox --version      # alpsbox 1.0.0
alpsbox check          # 逐项检查 FSL / MRtrix3 / dcm2niix
```

`alpsbox check` 的输出长这样：

```
 ALPSbox 环境检测
====================================================================
  FSLDIR      : /home/user/fsl
  MRtrix3     : /home/user/mrtrix3
  dcm2niix    : /home/user/fsl/bin/dcm2niix
  eddy 将使用 : /home/user/fsl/bin/eddy_cuda11.0

  FSL 必需命令：
    OK  eddy      /home/user/fsl/bin/eddy
    OK  bet       ...
    ...
====================================================================
环境可用。
```

**若 `alpsbox` 命令找不到**：说明 `$FSLDIR/bin` 不在 PATH，或者用绝对路径：

```bash
/home/user/fsl/bin/alpsbox check
```

---

## 5. 启动

### Linux / macOS（原生终端）

在仓库目录运行（会自动找 FSL；macOS 自动跳过 DISPLAY 设置）：

```bash
bash run_gui.sh
# 或
alpsbox gui
```

### Windows 双击

```
alpsbox/ALPSbox-GUI.bat
```

> 会弹一个黑色命令行窗口，**别关它** —— 关它就关了 GUI。
> 新版启动器会自动查找 WSL 发行版，不再写死 `Ubuntu`。若你的发行版不是默认
> 发行版，任选一种方式（只需做一次）：
>
> ```bat
> wsl -s Ubuntu-24.04                    :: 设为默认发行版
> setx ALPSBOX_WSL_DISTRO Ubuntu-24.04   :: 只告诉本启动器（需重开窗口）
> wsl -l -v                              :: 查看准确的发行版名
> ```
>
> 启动器与 `run_gui.sh` 必须放在同一文件夹；也可以在 WSL 里直接运行
> `bash run_gui.sh` 或 `alpsbox gui`。

### 命令行

任何系统都可以运行 `alpsbox gui`；处理命令（`alpsbox check` / `run` / `batch`
等）在三个系统上完全相同。

工具默认英文；首页可切换为简体中文（作用于本次会话的界面、处理日志、质控文字
和 HTML 报告）。命令行给任意子命令加 `--lang en` 或 `--lang zh_CN` 可切换
本次运行的语言。

**这两个启动器都不写死路径**：

- `run_gui.sh` 按自身位置定位包，依次检查 `$FSLDIR`、`~/fsl`、
  `/usr/local/fsl`、`/opt/fsl` 等常见位置来自动找 FSL，
  macOS 上自动跳过 `DISPLAY`。
- `ALPSbox-GUI.bat` 用 `wslpath` 把所在目录转成 WSL 路径并自动查找 WSL
  发行版（默认发行版优先，找不到再尝试 Ubuntu/Debian 常见名称；也可用
  `ALPSBOX_WSL_DISTRO` 指定）。整个 `alpsbox` 文件夹放哪个本地盘、哪个
  目录都行；建议不要放在网络盘/UNC 路径上。

启动日志写到 `~/.alpsbox/gui.log`，里面有 `whoami`、包路径、`uname`、
探测到的 FSLDIR / MRtrix3 / DISPLAY / Python。起不来先看这个。

---

## 6. 依赖不满足时怎么办

点界面右上角 **「环境详情」**，会列出：

- 每一项检查结果（找到的路径 / 缺失）
- 具体的修复命令字符串
- **「复制诊断信息」** 按钮 —— 可直接粘给能帮你排查的人

### 各缺失项的影响

| 缺失 | 严重性 | 影响 |
|---|---|---|
| FSL / eddy / vecreg / dtifit / flirt | **致命** | 完全无法处理 |
| `fslstats` / `fslroi` | **致命** | 无法算 ROI 均值 |
| MRtrix3 / mrdegibbs | 轻微 | 跳过去振铃，结果仍有效 |
| dcm2niix | 轻微 | 只影响 DICOM 输入；已有 NIfTI 时不需要 |
| eddy_cuda | 可接受 | 回落 CPU eddy（慢 5–10 倍） |
| `fslcc` | 轻微 | 质控的配准指标显示「未测」，ALPS 数值不受影响 |
| `pillow` | 轻微 | 「ROI 图解」页空白，处理与质控不受影响 |

---

## 7. 最小可用组合（如果只想跑起来）

```bash
# 只要这三样就能跑
sudo apt install -y python3 python3-pip
# + FSL（见第 2 步）
cd alpsbox && python3 -m pip install -e .
alpsbox run /path/to/sub_001 --out ./results```

没有 MRtrix3 也行（会提示跳过去振铃）。
没有 dcm2niix 也行（只要你已经是 NIfTI + bval + bvec + json）。

---

## 8. 检查清单

装完逐项打勾：

- [ ] `echo $FSLDIR` 有输出
- [ ] `fsl-config --version` ≥ 6.0.3
- [ ] `which eddy bet dtifit flirt vecreg fslroi fslmaths fslstats` 全部有路径
- [ ] `which mrdegibbs`（可选的）
- [ ] `which fslcc`（质控用，建议有）
- [ ] `alpsbox --version` 输出 1.0.0
- [ ] `alpsbox check` 最后显示"环境可用"
- [ ] `echo $DISPLAY` 有值（要 GUI 的话）
- [ ] 双击 `ALPSbox-GUI.bat`（Windows）或运行 `bash run_gui.sh`（Linux/macOS）能出窗口
- [ ] GUI 里「质控」页能打开、「ROI 图解」页能看到脑图

全部打勾就可以开始跑了。

---

## 附：卸载

```bash
python3 -m pip uninstall alpsbox
rm -rf ~/.alpsbox          # 删除会话记录（结果历史）
```

FSL / MRtrix3 按各自安装文档卸载。

---

## ⚠️ 注意：不要把 MRtrix3 的 `bin` 放到 `PATH` 最前面

MRtrix3 自带一个 `python3`（通常 3.14，且**没有 numpy**）。如果你把
`~/mrtrix3/bin` 放在 `PATH` 最前面，`python3` 就会被它抢占，导致：

* `python3 -m alpsbox gui` 起不来（缺 tkinter）
* `python3 -m alpsbox batch` 里 HTML 报告生成失败

**推荐配置**：把 MRtrix3 放在 `PATH` **末尾**，或者启动 ALPSbox 时显式指定解释器：

```bash
/usr/bin/python3 -m alpsbox batch ...
```

（v0.6.5 起 `--regqc` 已不依赖 numpy，即使解释器没有 numpy 也能工作。）
