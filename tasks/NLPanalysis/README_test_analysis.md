# test_analysis.py 输出说明

这个文档解释 [tasks/NLPanalysis/test_analysis.py](/home/xsl/VoiceDeepfake/tasks/NLPanalysis/test_analysis.py) 会生成哪些结果文件，以及这些 CSV 中每个音频特征的含义。

脚本本质上分两层：

1. 先调用 R 的 soundgen::analyze()，得到逐帧声学特征。
2. 再在 Python 里把这些逐帧特征整理成逐帧 CSV、分段 CSV，以及批量汇总 CSV。

这里的 NLP 指的是 nonlinear phenomena，也就是发声中的非线性现象候选，如亚谐波、边带、混沌、频率跳变。它不是自然语言处理。

## 结果文件

脚本可能产生三类文件：

### 1. 逐帧文件

文件名形如：

- [results/.../*_nlp_frames.csv](/home/xsl/VoiceDeepfake/results)

每一行代表一个分析帧，保留了 soundgen 返回的原始逐帧指标，以及脚本根据阈值得到的候选标签。

### 2. 分段文件

文件名形如：

- [results/.../*_nlp_segments.csv](/home/xsl/VoiceDeepfake/results)

脚本把相邻且标签相同的帧合并成一个 segment，用于看连续的声学事件。

### 3. 批量汇总文件

文件名通常是：

- [results/NLPanalysis/.../audio_stats.csv](/home/xsl/VoiceDeepfake/results)
- [results/NLPanalysis/.../batch_summary.md](/home/xsl/VoiceDeepfake/results)

其中 audio_stats.csv 是最重要的批处理结果。每一行对应一个音频文件，内容是把逐帧结果做计数、占比、均值、中位数之后得到的摘要。

## 分析流程

脚本的核心流程如下：

1. 用短时傅里叶分析逐帧提取特征。
2. 对每一帧读取这些字段：voiced、ampl、pitch、amEnvDep、amMsPurity、HNR、roughness、entropy、subDep。
3. 基于阈值生成四类候选布尔变量：
   - subharmonics_candidate
   - sidebands_candidate
   - chaos_candidate
   - frequency_jump_candidate
4. 再给每一帧分配 heuristic_label。
5. 最后把逐帧标签合并为 segment，并按文件统计 audio_stats.csv。

## 逐帧 CSV 字段含义

逐帧文件对应 [tasks/NLPanalysis/test_analysis.py](/home/xsl/VoiceDeepfake/tasks/NLPanalysis/test_analysis.py) 里 R_ANALYSIS_SCRIPT 输出的字段。

### 时间与索引

- frame_index：帧编号，从 1 开始。
- time_start_ms：该帧起始时间，单位毫秒。它不是 soundgen 直接给出的原始边界，而是脚本用当前帧时间减去步长近似得到。
- time_end_ms：该帧结束时间，单位毫秒。脚本直接用 soundgen 返回的当前帧时间戳作为结束位置。

### 基础发声状态

- voiced：这一帧是否被认为是有声帧。
  含义：TRUE 通常表示这一帧存在可追踪的周期性发声，FALSE 表示无声、噪声段或难以建立稳定基频的片段。

### 原始声学特征

- ampl：RMS 幅度。
  含义：短时帧内信号能量的均方根幅度，反映这一帧“有多响/多强”，但它是物理幅度，不等于主观响度。

- pitch：基频或其后处理后的音高轮廓，单位 Hz。
  含义：这一帧的主导周期性频率估计。对明显无声或无法可靠跟踪基频的帧，可能是空值。

- amEnvDep：基于平滑振幅包络估计的振幅调制深度，范围大致是 0 到 1。
  含义：如果把音频包络看成“音量在起伏”，这个量表示起伏有多明显。数值越大，说明包络调制越强。

- amMsPurity：基于 modulation spectrum 估计的振幅调制纯度。
  含义：表示某个主导振幅调制频率有多突出。它反映调制是否集中、是否像清晰的周期性抖动，而不是分散的随机起伏。

- HNR：harmonics-to-noise ratio，谐波噪声比，单位 dB。
  含义：衡量这一帧有多“谐波化”。值越高，通常表示更接近规则的周期性发声；值越低，说明噪声成分越重、周期性越差。HNR = 0 dB 近似表示谐波能量与噪声能量相当。

- roughness：粗糙度。
  含义：衡量处于 roughness 频带内的时频调制强度。直观上可以理解为声音是否带有明显的粗糙、刺耳、颤动、摩擦式的纹理。

- entropy：Wiener entropy，也可近似理解为谱平坦度，范围通常接近 0 到 1。
  含义：越接近 0，谱越像纯音或谐波结构明显的声音；越接近 1，越像宽带噪声。

- subDep：subharmonic depth，亚谐波深度。
  含义：衡量亚谐波成分有多强。0 表示几乎没有，1 表示亚谐波强度可以接近主基频成分。这个量依赖 pitch 跟踪质量，因此 pitch 不稳定时它也会受影响。

### 候选布尔标签

这些字段不是 soundgen 原始输出，而是脚本基于阈值二次判断出来的候选标记。

- subharmonics_candidate：是否疑似亚谐波。
  判定：subDep >= subdep_thres。

- sidebands_candidate：是否疑似边带。
  判定：amEnvDep >= amenv_thres，或者 amMsPurity >= amms_thres。
  直观理解：如果振幅调制明显，频谱上常会出现围绕主频的侧带结构，所以脚本把强 AM 当作边带候选信号。

- chaos_candidate：是否疑似混沌发声。
  判定：HNR <= hnr_thres，并且 roughness >= roughness_thres 或 entropy >= entropy_thres。
  直观理解：谐波性低，同时粗糙度高或频谱更像噪声时，更接近混沌或强非周期发声。

- frequency_jump_candidate：是否疑似频率跳变。
  判定：由 soundgen 内部的 findJumps() 根据 pitch 轮廓、jump_thres、jump_window 检测。
  直观理解：如果基频在短时间内发生突变，而不是平滑过渡，就会被标成这一类候选。

### 最终逐帧标签

- heuristic_label：脚本给这一帧的启发式最终标签。

可选值有：

- None：该帧是有声帧，但没有满足任何非线性候选规则。
- Unvoiced：该帧被视为无声或非稳定发声帧。
- Chaos：满足混沌候选规则。
- Sidebands：满足边带候选规则。
- Frequency jump：满足频率跳变候选规则。
- Subharmonics：满足亚谐波候选规则。

注意，这些标签有覆盖优先级，不是并列投票。脚本的覆盖顺序是：

1. 先把无声帧标成 Unvoiced
2. 再标 Chaos
3. 再标 Sidebands
4. 再标 Frequency jump
5. 最后标 Subharmonics

因此同一帧如果同时满足多个条件，最终优先级是：

- Subharmonics
- Frequency jump
- Sidebands
- Chaos
- Unvoiced
- None

这意味着 heuristic_label 只是一个单标签摘要；如果你想保留一帧同时具备多个现象的信息，应该直接看各个 *_candidate 列，而不是只看 heuristic_label。

## 分段 CSV 字段含义

分段文件是把连续且标签相同的帧合并后的结果。

- label：这个 segment 的标签，来自逐帧的 heuristic_label。
- start_ms：segment 起始时间，毫秒。
- end_ms：segment 结束时间，毫秒。
- duration_ms：segment 持续时长，毫秒。
- frame_count：这个 segment 包含多少个连续帧。

segment 的用途是把逐帧抖动压缩成更容易读的连续事件，比如“这一段连续 180 ms 都是 Subharmonics”。

## audio_stats.csv 字段含义

audio_stats.csv 是批处理时最核心的汇总表。每一行对应一个音频文件。

### 文件与任务状态字段

- source_audio：音频文件的绝对路径。
- relative_audio：相对于输入目录的相对路径。
- status：处理状态。
  常见值：
  - ok：本次成功分析。
  - skipped：复用了已有详细结果。
  - failed：处理失败。
- error：错误信息。只有 failed 时通常非空。

### 时长与帧级规模

- duration_ms：该音频在逐帧结果中的近似总时长，毫秒。
- frame_count：总帧数。
- segment_count：总分段数。
- voiced_frame_count：被判定为 voiced 的帧数。
- voiced_frame_ratio：voiced_frame_count / frame_count。
  含义：整个音频里，有多少比例的帧是可追踪发声状态。

### 主导标签

- dominant_frame_label：逐帧标签里出现次数最多的标签。
- dominant_segment_label：分段标签里出现次数最多的标签。

二者区别：

- dominant_frame_label 更偏向“总时长占比最大的是哪类现象”。
- dominant_segment_label 更偏向“事件个数上最常出现的是哪类现象”。

### 候选现象计数

- subharmonics_candidate_count：满足亚谐波候选条件的帧数。
- sidebands_candidate_count：满足边带候选条件的帧数。
- chaos_candidate_count：满足混沌候选条件的帧数。
- frequency_jump_candidate_count：满足频率跳变候选条件的帧数。

这些列统计的是候选布尔量为 TRUE 的帧数，不受 heuristic_label 单标签覆盖机制限制。所以它们比最终标签统计更能反映“现象是否同时出现”。

### 原始声学特征的均值与中位数

这些字段都是由逐帧特征聚合得到。

- mean_ampl / median_ampl：逐帧 RMS 幅度的均值 / 中位数。
- mean_pitch_voiced / median_pitch_voiced：仅在 voiced 帧上统计的 pitch 均值 / 中位数，单位 Hz。
- mean_amEnvDep / median_amEnvDep：振幅包络调制深度的均值 / 中位数。
- mean_amMsPurity / median_amMsPurity：调制谱 AM 纯度的均值 / 中位数。
- mean_HNR / median_HNR：谐波噪声比的均值 / 中位数。
- mean_roughness / median_roughness：粗糙度的均值 / 中位数。
- mean_entropy / median_entropy：谱熵的均值 / 中位数。
- mean_subDep / median_subDep：亚谐波深度的均值 / 中位数。

如何理解这些统计量：

- mean 更容易受到少量极端帧影响。
- median 更稳健，适合描述“典型帧”。
- pitch 只在 voiced 帧上统计，因此它不会被大量无声帧直接拉低。

### 按标签统计的计数与占比

脚本会为每个标签生成三列，共六组标签。

标签集合是：

- None
- Unvoiced
- Subharmonics
- Sidebands
- Chaos
- Frequency jump

每个标签都有以下三种统计：

- frame_<label>_count：该标签的帧数。
- frame_<label>_ratio：该标签帧数 / 总帧数。
- segment_<label>_count：该标签 segment 数。

具体列名如下：

- frame_none_count
- frame_none_ratio
- segment_none_count
- frame_unvoiced_count
- frame_unvoiced_ratio
- segment_unvoiced_count
- frame_subharmonics_count
- frame_subharmonics_ratio
- segment_subharmonics_count
- frame_sidebands_count
- frame_sidebands_ratio
- segment_sidebands_count
- frame_chaos_count
- frame_chaos_ratio
- segment_chaos_count
- frame_frequency_jump_count
- frame_frequency_jump_ratio
- segment_frequency_jump_count

这些字段的解释方式完全一致：

- frame_*_count 看总时长占比对应的帧数规模。
- frame_*_ratio 看该类现象在整段音频里占多大比例。
- segment_*_count 看该类现象被切成了多少个离散事件。

举例：

- frame_subharmonics_ratio 高：说明整段音频里很多时间都被标为亚谐波。
- segment_subharmonics_count 高但 frame_subharmonics_ratio 不高：说明亚谐波出现得很频繁，但每次持续时间不长。

## 阈值参数和它们控制的意义

脚本里用到的关键阈值如下：

- subdep_thres：亚谐波候选阈值。越低越容易把帧判为 subharmonics_candidate。
- amenv_thres：基于包络 AM 深度的边带候选阈值。
- amms_thres：基于调制谱纯度的边带候选阈值。
- hnr_thres：混沌候选的 HNR 上限。越高越宽松。
- roughness_thres：混沌候选的粗糙度下限。越低越宽松。
- entropy_thres：混沌候选的谱熵下限。越低越宽松。
- jump_thres：频率跳变检测阈值。
- jump_window：频率跳变检测所看的时间窗口。

这些阈值改变的不是底层原始特征本身，而是候选标签和最终 heuristic_label 的分布。

## 该脚本里的几个容易混淆点

### 1. heuristic_label 不是人工真值

它只是规则标签，不是人工标注，也不是训练后的分类器输出。更准确地说，它是“候选声学现象的启发式单标签摘要”。

### 2. sidebands 不是直接看频谱侧带图像

这里脚本没有直接检测某两个离散侧带峰，而是把较强的振幅调制当作边带候选的代理信号。因此它更适合快速筛查，不等于严格的频谱结构鉴定。

### 3. chaos 的定义是工程化近似

这里的 chaos 不是严格动力系统意义上的混沌证明，而是“低谐波性 + 高粗糙度或高噪声样谱”的启发式近似。

### 4. subDep 依赖 pitch 质量

如果基频跟踪本身不稳，subDep 的解释要更谨慎，因为亚谐波估计依赖于对 f0 的参照。

### 5. segment 不是声学真边界

它只是把相邻同标签帧做合并，适合摘要和可视化，不代表精确声门事件边界或人工注释边界。

## 如何读这些结果

如果你的目标是快速筛选音频，可以优先看：

- frame_subharmonics_ratio
- frame_sidebands_ratio
- frame_chaos_ratio
- frame_frequency_jump_ratio
- dominant_frame_label

如果你的目标是分析事件是否零散出现，可以看：

- segment_subharmonics_count
- segment_sidebands_count
- segment_chaos_count
- segment_frequency_jump_count

如果你的目标是理解声学底层变化，可以回到逐帧文件看：

- pitch
- HNR
- entropy
- roughness
- subDep
- 各类 *_candidate

## 与可视化脚本的关系

[tasks/NLPanalysis/visulization.py](/home/xsl/VoiceDeepfake/tasks/NLPanalysis/visulization.py) 会基于 audio_stats.csv 做说话人层面的小提琴图可视化。默认重点可视化的是：

- frame_subharmonics_ratio
- frame_sidebands_ratio

也就是说，它主要拿 audio_stats.csv 里的按文件汇总统计做说话人层面的分布图，而不是直接读取逐帧 CSV。

### visulization.py 当前支持的功能

- 默认绘制 frame_subharmonics_ratio 和 frame_sidebands_ratio。
- 可以通过 --columns 指定任意一个或多个数值列。
- 可以通过 --all-columns 自动绘制 CSV 中所有可用数值列。
- 每个特征单独输出一张小提琴图。
- 每个特征会额外输出一张按说话人均值排序的版本。
- 每张图左上角会自动标注当前特征的 overall 样本数、speaker 数、均值和中位数。

### 常用命令

默认绘制两列：

```bash
python tasks/NLPanalysis/visulization.py results/NLPanalysis/LibriSeVoc_diffwave/audio_stats.csv
```

只绘制指定列：

```bash
python tasks/NLPanalysis/visulization.py results/NLPanalysis/LibriSeVoc_diffwave/audio_stats.csv \
  --columns frame_subharmonics_ratio mean_HNR mean_entropy
```

绘制所有可用数值列：

```bash
python tasks/NLPanalysis/visulization.py results/NLPanalysis/LibriSeVoc_diffwave/audio_stats.csv \
  --all-columns
```

指定输出名前缀：

```bash
python tasks/NLPanalysis/visulization.py results/NLPanalysis/LibriSeVoc_diffwave/audio_stats.csv \
  --columns mean_HNR \
  --output /tmp/viz.png
```

### 输出文件命名规则

如果不传 --output，脚本会默认生成类似下面的文件：

- audio_stats_speaker_ratio_distribution_frame_subharmonics_ratio.png
- audio_stats_speaker_ratio_distribution_frame_subharmonics_ratio_sorted_by_mean.png

如果传入：

- --output /tmp/viz.png

则指定列 mean_HNR 会生成：

- /tmp/viz_mean_HNR.png
- /tmp/viz_mean_HNR_sorted_by_mean.png

### 图上的统计摘要怎么理解

每张图左上角的文本框默认统计当前特征在当前 CSV 中全部有效样本的：

- overall n：有效音频条目数
- speakers：有有效值的 speaker 数
- mean：该特征的全局均值
- median：该特征的全局中位数

这些统计是帮助你快速判断这个特征整体分布位置的摘要，不会替代小提琴图本身展示的分布形状。

## 参考依据

这个 README 的字段解释来自两部分：

1. [tasks/NLPanalysis/test_analysis.py](/home/xsl/VoiceDeepfake/tasks/NLPanalysis/test_analysis.py) 自身的实现逻辑。
2. soundgen::analyze() 文档对这些声学量的定义，包括 ampl、pitch、amEnvDep、amMsPurity、HNR、roughness、entropy、subDep 等。

如果你后续想把这些结果写进论文，建议把 heuristic_label 描述为：

“a rule-based candidate label derived from frame-level acoustic descriptors extracted with soundgen”

而不要直接把它表述为严格的人工确认标签。