# VoiceDeepfake analysis 目录说明

## 1. 目录定位

analysis 目录是一组围绕人声非线性现象进行研究分析的脚本集合，核心关注对象是 NLPs（nonlinear phenomena），包括：

- Subharmonics
- Sidebands
- Chaos
- Frequency jumps

这些脚本不是训练或推理入口，而是偏研究型的数据分析、可视化、算法验证和声音合成演示代码。主要依赖 R、soundgen、ggplot2、patchwork、randomForest，以及部分 Praat 脚本。

从功能上看，这个目录可以分为四类：

1. 人工标注与一致性分析
2. 声学指标和检测算法验证
3. 真实语音数据的描述统计
4. NLP 合成与可控操作示例

## 2. 目录结构与文件作用

```text
analysis/
├── README.md
├── analysis.zip
├── analysis_HNR.Rmd
├── analysis_amDep.Rmd
├── analysis_any-NLP.Rmd
├── analysis_descriptives.R
├── analysis_freqJump.Rmd
├── analysis_subh.Rmd
├── getHNR.praat
├── manualAnn_specs.R
├── manual_annotation.Rmd
├── phasegrams.Rmd
├── synthesis_AM-FM.Rmd
├── synthesis_biphonation.Rmd
├── synthesis_chaos.Rmd
├── synthesis_freqJumps.Rmd
└── visualization.Rmd
```

### 2.1 核心统计与分析脚本

#### analysis_descriptives.R

这个目录里最接近“总分析脚本”的文件。

主要作用：

- 从 ../data/bs_per_frame.RDS 读取逐帧分析结果
- 将手工标注的 NLP 类型整理成统一类别
- 过滤低能量帧，减少静音和近静音干扰
- 对 Speech、Nonverbal、Singing 三大类声音做对比
- 比较 HNR、entropy、roughness、subDep 等多个声学特征在不同 NLP 类别下的分布
- 用简单线性模型计算每个特征由 NLP 类别解释的方差比例（R²）
- 用随机森林粗略测试这些特征能否区分不同 NLP

脚本前半部分还有两个 if (FALSE) 代码块，用于一次性离线处理：

- 清理人工标注，只保留真实存在的音频文件
- 对 1518 个 beyond_speech 录音做逐帧声学分析，并将人工标注映射到逐帧数据

因此，这个脚本的角色是：
把“真实录音 + 人工标注 + 自动声学分析 + 非线性时间序列特征”整合成最终描述统计结果。

#### analysis_any-NLP.Rmd

这是一个综合性验证脚本，用大量合成声音测试“不同 NLP 类型是否真的会在各类声学指标上表现出可分辨的差异”。

主要作用：

- 生成多类合成声音：Unvoiced、None、Sidebands、Subharmonics、Chaos
- 调用 analyze() 和 phasegram() 提取声学与非线性特征
- 比较不同 NLP 类型在多项指标上的分布差异
- 再把结果和人工标注的真实人声数据放在一起对照

这个脚本相当于连接“模拟数据验证”和“真实数据解释”的桥梁。

#### analysis_HNR.Rmd

用于验证 HNR（harmonics-to-noise ratio）这个指标的稳定性和解释边界。

主要作用：

- 合成带谐波和噪声的声音
- 控制 f0、jitter、rolloff、SNR 等参数
- 分别用 soundgen 和 Praat 测量 HNR
- 对比真实信噪比和估计 HNR 的关系

该脚本回答的问题是：HNR 到底在什么条件下可靠，什么时候会受 jitter、噪声或非平稳性影响而失真。

#### analysis_amDep.Rmd

用于验证幅度调制 AM 的检测与量化。

主要作用：

- 合成具有已知 AM 深度和 AM 频率的声音
- 用 analyze() 的两条路径提取 AM：
  - 从平滑振幅包络提取
  - 从 modulation spectrum 提取
- 比较真实 AM 参数与测量结果的一致性

该脚本主要验证 amEnvDep、amEnvFreq、amMsPurity、amMsFreq 这些指标。

#### analysis_subh.Rmd

用于验证 subharmonics 的检测算法。

主要作用：

- 合成包含已知 subDep 和 subRatio 的声音
- 用 analyze() 检测 subharmonics 的强度和比例
- 检查当 f0 或 g0 检测错误时，subharmonics 指标会怎样退化

它的核心研究点是：subharmonics 的测量高度依赖 pitch tracking 是否正确。

#### analysis_freqJump.Rmd

用于优化频率跳变 frequency jumps 的自动检测。

主要作用：

- 读取人工标注的 pitch jump 时间点
- 基于 f0 轨迹调用 soundgen 内部的 findJumps() 检测候选跳变
- 通过 jumpThres 和 jumpWindow 网格搜索优化参数
- 用 precision、recall、F1 评估检测效果

它关注的是“快速频率变化”能否从逐帧 pitch 轨迹中稳定自动恢复出来。

### 2.2 标注与可视化说明脚本

#### manual_annotation.Rmd

用于评估人工 NLP 标注的一致性。

主要作用：

- 读取多位专家对同一批录音的标注结果
- 绘制不同标注者在时间轴上的 NLP 标记
- 计算帧级的一致性指标
- 分别统计“是否存在 NLP”“NLP 类型是否一致”“frequency jump 是否一致”

这个脚本为后续所有真实数据分析提供标注可靠性基础。

#### manualAnn_specs.R

用于说明“可视化参数会影响人对 NLP 的判断”。

主要作用：

- 演示动态范围过小会让 subharmonics 不明显
- 演示分析窗长不同会改变 AM 的可见性
- 演示普通谱图和 reassigned spectrogram 对快速 FM 的区别
- 演示看起来像 smudge 的现象不一定真的是 chaos

它更像一个“标注和看图注意事项”脚本，而不是正式统计分析脚本。

#### visualization.Rmd

这是一个通用的声音可视化说明文档。

主要作用：

- 展示 spectrogram 的不同画法
- 解释时间分辨率和频率分辨率之间的权衡
- 演示 auditory spectrogram 和 reassigned spectrogram
- 演示 modulation spectrum 的解读方法

它是整个目录里最偏“方法说明”的文档之一。

#### phasegrams.Rmd

用于解释相空间与非线性时间序列分析的直觉。

主要作用：

- 用延迟坐标和 Hilbert transform 构造 phase space
- 展示纯音、AM、FM、subharmonics、biphonation、chaos 在相空间中的差异
- 帮助理解 phasegram() 这类非线性特征的来源

这个脚本是理解 shannon、ed、d2、sur 等 phase-space 特征的重要背景材料。

### 2.3 合成与操控示例脚本

#### synthesis_AM-FM.Rmd

演示如何在合成声音或真实录音上加入 AM、FM 和 subharmonics。

主要作用：

- 合成带 AM 的声音
- 比较正弦 AM 和非正弦 AM 的频谱效果
- 在已有录音上添加 AM
- 演示 FM 和其与 sidebands 的关系

#### synthesis_biphonation.Rmd

演示双声源发声和双发声 biphonation 的两类模型。

主要作用：

- 说明两个声源相加与相乘的差异
- 展示并联和串联声源的声学结果
- 合成 whistle + tone 等双发声示例

#### synthesis_chaos.Rmd

演示如何近似合成 chaos，或者把 chaos 加到已有录音中。

主要作用：

- 用 jitter 和 shimmer 合成类似 chaos 的效果
- 用快速 pitch 跳变制造类似 chaos 的片段
- 对真实录音做 source-filter 风格的重合成与 envelope transplant

#### synthesis_freqJumps.Rmd

演示如何从录音中移除频率跳变，或给合成声音加上频率跳变。

主要作用：

- 对已有录音做 shiftPitch 处理，平滑掉某个 pitch jump
- 基于合成 source 再叠加 formant 和 envelope，做带 jump 的版本

### 2.4 辅助文件

#### getHNR.praat

这是供 analysis_HNR.Rmd 调用的 Praat 脚本。

主要作用：

- 从临时导出的 wav 中计算 Praat 版本的 HNR
- 作为与 soundgen 结果对照的外部基线

#### analysis.zip

看起来是 analysis 目录相关内容的压缩归档文件，通常不是主分析流程的一部分，更像打包或备份产物。

## 3. 典型数据流

这个目录的整体数据流大致如下：

### 3.1 真实数据分析路径

1. 从 ../sounds/beyond_speech 读取真实录音
2. 从 ../data/nlp_manual.csv 读取人工 NLP 标注
3. 用 analyze() 和 phasegram() 逐帧提取声学特征与非线性特征
4. 把标注映射到逐帧特征表中
5. 保存为 ../data/bs_per_frame.RDS
6. 在 analysis_descriptives.R 中做描述统计、可视化和简单分类

### 3.2 合成数据验证路径

1. 用 soundgen 合成带已知真值的 AM、subharmonics、chaos、frequency jumps 等声音
2. 用 analyze()、phasegram() 或其他函数提取特征
3. 将估计结果与合成时设定的真实参数比较
4. 得到各检测算法的误差边界、适用条件和失效模式

### 3.3 可视化与教学路径

1. 用 visualization.Rmd、phasegrams.Rmd 解释图怎么看
2. 用 manualAnn_specs.R 说明谱图参数对观测结果的影响
3. 用 synthesis_*.Rmd 演示各种 NLP 可以如何被生成、增强、替换或移除

## 4. 这个目录回答的核心问题

综合来看，analysis 目录主要回答以下问题：

1. 人类专家能否稳定一致地标注 NLP？
2. 现有自动声学指标能否准确测到这些 NLP？
3. 不同 NLP 会在 HNR、entropy、roughness、AM、subharmonics 等指标上留下什么统计痕迹？
4. 这些现象在真实人声中如何表现，在合成人声中能否被复现？
5. 哪些现象是“真的非线性”，哪些可能只是可视化或 pitch tracking 造成的假象？

## 5. 建议阅读顺序

如果是第一次看这个目录，建议按下面顺序阅读：

1. visualization.Rmd
2. phasegrams.Rmd
3. manual_annotation.Rmd
4. analysis_amDep.Rmd
5. analysis_subh.Rmd
6. analysis_freqJump.Rmd
7. analysis_HNR.Rmd
8. analysis_any-NLP.Rmd
9. analysis_descriptives.R
10. synthesis_AM-FM.Rmd、synthesis_biphonation.Rmd、synthesis_chaos.Rmd、synthesis_freqJumps.Rmd

这样读的好处是：

- 先理解图和现象
- 再理解标注是否可靠
- 再理解自动指标是否可信
- 最后再看真实数据上的总分析与声音操控示例

## 6. 与当前工作最相关的文件

如果你的目标是理解“这个目录最后产出了什么结论”，最关键的是以下三个文件：

1. analysis_descriptives.R
2. analysis_any-NLP.Rmd
3. manual_annotation.Rmd

如果你的目标是修改或复现实验，则通常还需要同时查看：

1. analysis_amDep.Rmd
2. analysis_subh.Rmd
3. analysis_freqJump.Rmd
4. analysis_HNR.Rmd
5. getHNR.praat

## 7. 总结

analysis 目录并不是一个单一程序，而是一套研究型分析工具箱。

它围绕“人声中的非线性发声现象”展开，覆盖了：

- 人工标注
- 自动检测验证
- 可视化解释
- 真实数据描述统计
- 合成声音操控与复现实验

如果把整个目录浓缩成一句话，它的作用是：

通过手工标注、声学分析、非线性时间序列分析和可控声音合成，系统研究人声中各种 NLP 的表现、可检测性和统计特征。