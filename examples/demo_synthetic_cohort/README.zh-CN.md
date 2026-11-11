# 示例队列（合成数据，仅供试用）

[**English**](README.md) | [**简体中文**](README.zh-CN.md)

这个文件夹是用来试「导入结果」按钮的，**里面没有任何真实被试的数据**。

所有数值都是 `examples/make_demo_cohort.py` 用固定随机种子生成的，
被试 ID（`demoA_01`、`demoB_02` …）也是编的。用它熟悉界面可以，
**不要拿它做任何分析，也不要当成真实结果的参考**。

---

## 怎么用

1. 打开 ALPSbox，进「质控」页
2. 点「导入结果」，选本文件夹里的 `demo_synthetic_summary.csv`
3. 若当前结果表里已有内容，会按被试 ID 合并；ID 不冲突就不会覆盖
4. 质控统计和明细表会立刻按新数据重算
5. **双击任意一行**，右侧会画出该被试的头动曲线

第 5 步能出图，是因为本文件夹里除了 CSV，还有每个被试的子目录：

```
demo_synthetic_cohort/
  demo_synthetic_summary.csv      <- 导入这个
  demoA_01/
    eddy_out.eddy_movement_rms    <- 曲线数据（每卷两列）
    eddy_out.eddy_outlier_report  <- 红色竖带的位置
  demoA_02/
  ...
```

导入时程序会记住 CSV 所在目录，之后按「目录/被试ID」去找这两个文件。
换成你自己的数据时，把 CSV 放在各被试子目录的上一级即可。

---

## 这批示例想演示什么

十个被试，两种分组（`groupA` / `groupB`），故意做出四种不同的质控结果：

| 被试 | 情况 | 实际判定 |
|---|---|---|
| `demoA_01/02/04`、`demoB_01/03/05` | 正常 | 通过（6 个） |
| `demoA_03` | 第 9–12、26–28 卷有几次明显抖动（抖动 0.156 / 0.847 mm），漂移也大 | 需注意 |
| `demoA_05` | 缓慢累积漂移（1.13 / 2.13 mm），抖动正常 | 提示（漂移偏大） |
| `demoB_02` | 配准失败（r_wm 0.875），ALPS 随之偏低 | 不合格 |
| `demoB_04` | 离群切片多（23 条 / 40 卷） | 需注意 |

合计：通过 6，提示 1，需注意 2，不合格 1。

导入后可以点「通过 / 需注意 / 不合格」筛选，看分档是否正确。
`demoA_03` 是看头动曲线最典型的一个，抖动尖峰在图上很明显。

---

## 关于分组

工具本身**不预设任何队列结构**。散点图的分组口径在散点窗口里选：

| 选项 | 含义 |
|---|---|
| 按 ID 前缀（默认） | 取下划线、横线或点之前的第一段，`demoA_01` → `demoA` |
| 用 group 列 | 读数据里的 `group` 字段；示例 CSV 里是 `groupA` / `groupB` |
| 不分组 | 当成一个整体画 |

这份 CSV 同时带 `group` 列，所以三种口径都能试。你自己的数据用什么命名都行，
只要 ID 里带一段能代表组别的前缀，或者干脆加一列 `group`。

> 注意：本工具只负责**每个被试的 ALPS 与质控**；组间统计属于下游分析，
> 不在本工具范围内（`group` 列只用于界面散点图的分组显示）。

---

## 重新生成

想换一批数值：

```bash
python3 examples/make_demo_cohort.py
```

随机种子写死在脚本里（`20261023`），同样的种子每次生成一样的结果。
改种子或改 `SUBJECTS` 列表就能得到不同组合。

---

## 文件格式

CSV 的列（顺序无所谓，缺列会留空）：

```
subject, status, group,
ALPS_L, ALPS_R, ALPS_mean,
r_wm, n_L_proj, n_R_proj, n_L_asso, n_R_asso,
rms_abs_mean, rms_abs_max, rms_rel_mean, rms_rel_max,
n_outlier, n_vol, method, seconds, finished_at
```

大小写不敏感，`ALPS_L` 和 `alps_L` 都能识别。
`subject` 也可以用 `id`。

`eddy_out.eddy_movement_rms` 是 FSL eddy 的原始输出格式：
每行一个体积，第一列是相对第 1 卷的绝对位移，第二列是相对前一卷的位移，单位毫米。
直接把这些文件换成真实的一定能读。
