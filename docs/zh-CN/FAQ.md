# 常见问题（中文简版）

完整中文说明见 [INSTALL.md](INSTALL.md)；英文 FAQ 见 [../FAQ.md](../FAQ.md)。

## 先跑环境检查

```bash
alpsbox check
```

## 安装与依赖

- **`alpsbox: command not found`**：在仓库目录 `pip install -e .`，然后 `source ~/.bashrc`。
- **未找到 FSL**：`source $FSLDIR/etc/fslconf/fsl.sh`；FSL 装在别处时加 `--fsl-dir`。
- **没有 `mrdegibbs`**：MRtrix3 是可选依赖，去振铃会跳过并给出警告。
- **不要把 MRtrix3 的 `bin` 放在 `PATH` 最前面**：它自带的 `python3` 可能没有 numpy。

## 输入数据

- **找不到 DWI**：每个被试目录需要同名的 `.nii(.gz)` + `.bval` + `.bvec`，文件名必须一致。
- **`TotalReadoutTime out of range`**：json 里的读出时间单位必须是秒（约 0.01–0.2）。
- **bvec 列数与体积数不符**：先跑 `alpsbox dryrun` 检查。
- **没有 json**：无法用完整 eddy，会回落到 `eddy_correct`（已知偏差），质控会标出，
  不要与其他 eddy 处理的被试在下游混用。
- **TOPUP 在哪里开？为什么没生效？** TOPUP 针对相位编码方向相反的第二套 DWI
  （AP + PA）。GUI：处理页 → **高级 → TOPUP**（单被试选自动检测或手动指定第二套；
  批量自动按被试检测）；命令行：`run` 用 `--dwi2/--bval2/--bvec2/--json2`，
  `batch` 用 `--topup-auto`，可用 `--topup-config` 指定 b02b0.cnf。没有反向 PE
  数据、任一 json 缺 `PhaseEncodingDirection`/`TotalReadoutTime`、两套方向相同、
  或找不到 b02b0.cnf 时会跳过；日志和 `alps_summary.csv` / `alps_result.json` 的
  `topup` 列会给出原因。第二套必须是 NIfTI + `.bval` + `.bvec` + `.json`
  （DICOM 先用 dcm2niix 转换）。

## 处理

- **eddy 跑 10–20 分钟**：正常，eddy 占八成时间。
- **中断了**：重新跑同一个队列即可，已有 `alps_result.json` 的被试会跳过。
- **ROI 体素数不是 81**：配准可能失败或数据被重采样；先看 `FA_in_mni.nii.gz`。
- **要不要开 `--regqc`**：研究用途建议开，每例多 1–2 分钟，能量化 ALPS 对配准的敏感度。

## 结果

- **ALPS 多少算正常**：没有公认诊断阈值；报告里的参考区间仅用于判断数值是否合理。
- **能否和文献直接比**：只有采集和处理参数接近时才能比；bet 阈值、配准代价、
  模板、ROI 都会改变 ALPS。
- **能不能做组统计**：不能——本工具只输出每个被试的数值与质控，组统计请用导出的
  CSV/JSON 在下游软件完成。

## 图形界面与启动器

- **双击 `ALPSbox-GUI.bat` 报 "Could not resolve this folder inside WSL" /
  "Could not find an accessible WSL distribution"**：说明 Windows 没能把启动器
  所在目录传给可用的 WSL 发行版。依次检查：
  1. `wsl -l -v`：是否装了发行版、状态不是 `Installing`；没有则用管理员
     PowerShell 执行 `wsl --install -d Ubuntu` 后重启。
  2. 你的发行版是不是默认发行版？不是的话任选一种：`wsl -s <名字>` 设为默认，
     或 `setx ALPSBOX_WSL_DISTRO <名字>` 后重开窗口再双击。名字要完全一致
     （如 `Ubuntu-24.04`，不要加引号）；常见 Ubuntu/Debian 名称会自动尝试。
  3. ALPSbox 文件夹是否在本地盘？网络盘/UNC 路径不一定能转换成 WSL 路径，
     建议放到 `C:\` 或 `D:\` 下。
  4. `run_gui.sh` 是否与 `.bat` 在同一文件夹。
  诊断：先 `set ALPSBOX_DRY_RUN=1` 再双击，启动器只解析路径并退出。
  旧版启动器有一个路径尾部反斜杠 bug（必然报此错），更新到最新
  `ALPSbox-GUI.bat` 即可。

- **怎么换语言**：工具默认英文。在 GUI 首页选 简体中文 即切换本次会话的界面、
  处理日志、质控文字和 HTML 报告。命令行给任意子命令加 `--lang en` 或
  `--lang zh_CN` 即可（默认英文）。
- **窗口不出现（WSL）**：需要 WSLg（Windows 11），`echo $DISPLAY` 应有值。
- **Linux/macOS 上 GUI 打不开**：Linux 需要图形会话，`echo $DISPLAY` 应有值
  （X11 或 Wayland 的 XWayland）；macOS 先确认
  `python3 -c "import tkinter; print(tkinter.TkVersion)"` 能通过（python.org 的
  Python 自带 Tk，Homebrew 版需另装匹配的 `python-tk`）。失败时
  `bash run_gui.sh` 会打印日志路径和探测到的 FSL/Python；完整日志在
  `~/.alpsbox/gui.log`。
- **跑得慢**：66 体积数据每例约 10–15 分钟属正常，受 CPU/GPU 限制。
