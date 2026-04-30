# Batch NLP Analysis Report

## Batch Info

- Input directory: /mnt/home/xiaoshilin/Data/LibriSeVoc/gt
- Stats CSV: /mnt/home/xiaoshilin/ADD-NLP/results/NLPanalysis/LibriSeVoc_gt/audio_stats.csv
- Audio suffixes: .wav
- Files discovered: 13201
- Successful or reused: 13157
- Failed: 44
- Approximate analyzed duration: 2079m 49.62s

## Aggregate Frame Labels

- None: 1098450
- Unvoiced: 2028539
- Subharmonics: 467674
- Sidebands: 1379237
- Chaos: 0
- Frequency jump: 17685

## Aggregate Segment Labels

- None: 220506
- Unvoiced: 309613
- Subharmonics: 269606
- Sidebands: 389307
- Chaos: 0
- Frequency jump: 17685

## Failures

- 3259_158083_000024_000004.wav: R analysis failed: Error in file(filename, "r") : 无法打开链结
此外: Warning message:
In file(filename, "r") :
  无法打开文件'/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/compiler/R/compiler': 没有那个文件或目录
错误: 程辑包‘compiler’里的R写碼载入失败
停止执行
- 3259_158083_000068_000000.wav: R analysis failed: Warning in gzfile(file, "rb") :
  无法打开压缩文件'/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/rlang/Meta/nsInfo.rds'，可能是因为'没有那个文件或目录'
错误: package or namespace load failed for ‘soundgen’ in gzfile(file, "rb"):
 无法打开链结
停止执行
- 3436_172171_000010_000001.wav: R analysis failed: Error in gzfile(file, "rb") : 无法打开链结
此外: Warning message:
In gzfile(file, "rb") :
  无法打开压缩文件'/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/compiler/R/compiler.rdx'，可能是因为'没有那个文件或目录'
错误: 程辑包‘compiler’里的R写碼载入失败
停止执行
- 3607_29116_000042_000001.wav: R analysis failed: 错误: package or namespace load failed for ‘soundgen’:
 loadNamespace()里算'rlang'时.onLoad失败了，详细内容：
  调用: gzfile(file, "rb")
  错误: 无法打开链结
停止执行
- 3699_47246_000010_000000.wav: R analysis failed: Warning in gzfile(file, "rb") :
  无法打开压缩文件'/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/rlang/Meta/package.rds'，可能是因为'没有那个文件或目录'
错误: package or namespace load failed for ‘soundgen’ in find.package(package, lib.loc, verbose = verbose):
 不存在叫‘rlang’这个名字的程辑包
停止执行
- 3830_12529_000014_000000.wav: R analysis failed: Warning in gzfile(file, "rb") :
  无法打开压缩文件'/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/jsonlite/Meta/package.rds'，可能是因为'没有那个文件或目录'
错误: package or namespace load failed for ‘soundgen’ in gzfile(file, "rb"):
 无法打开链结
停止执行
- 3830_12530_000012_000002.wav: R analysis failed: Warning in gzfile(file, "rb") :
  无法打开压缩文件'/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/jsonlite/R/jsonlite.rdx'，可能是因为'没有那个文件或目录'
Error in gzfile(file, "rb") : 无法打开链结
错误: package or namespace load failed for ‘soundgen’:
 程辑包‘jsonlite’里的R写碼载入失败
停止执行
- 3830_12531_000010_000000.wav: R analysis failed: Warning in gzfile(file, "rb") :
  无法打开压缩文件'/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/jsonlite/Meta/package.rds'，可能是因为'没有那个文件或目录'
错误: package or namespace load failed for ‘soundgen’ in find.package(package, lib.loc, verbose = verbose):
 不存在叫‘jsonlite’这个名字的程辑包
停止执行
- 3830_12535_000017_000000.wav: R analysis failed: Warning in gzfile(file, "rb") :
  无法打开压缩文件'/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/jsonlite/Meta/package.rds'，可能是因为'没有那个文件或目录'
错误: package or namespace load failed for ‘soundgen’ in gzfile(file, "rb"):
 无法打开链结
停止执行
- 3857_180923_000006_000000.wav: R analysis failed: Warning in gzfile(file, "rb") :
  无法打开压缩文件'/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/R6/Meta/package.rds'，可能是因为'没有那个文件或目录'
错误: package or namespace load failed for ‘soundgen’ in loadNamespace(j <- i[[1L]], c(lib.loc, .libPaths()), versionCheck = vI[[j]]):
 不存在叫‘R6’这个名字的程辑包
停止执行
- 3879_174923_000033_000008.wav: R analysis failed: 错误: package or namespace load failed for ‘soundgen’:
 loadNamespace()里算'rlang'时.onLoad失败了，详细内容：
  调用: gzfile(file, "rb")
  错误: 无法打开链结
停止执行
- 40_121026_000009_000000.wav: R analysis failed: 错误: package or namespace load failed for ‘soundgen’:
 loadNamespace()里算'rlang'时.onLoad失败了，详细内容：
  调用: gzfile(file, "rb")
  错误: 无法打开链结
停止执行
- 40_121026_000059_000001.wav: R analysis failed: Error in gzfile(file, "rb") : 无法打开链结
此外: Warning message:
In gzfile(file, "rb") :
  无法打开压缩文件'/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/compiler/R/compiler.rdx'，可能是因为'没有那个文件或目录'
错误: 程辑包‘compiler’里的R写碼载入失败
停止执行
- 412_126975_000087_000009.wav: R analysis failed: Warning in gzfile(file, "rb") :
  无法打开压缩文件'/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/jsonlite/Meta/package.rds'，可能是因为'没有那个文件或目录'
错误: package or namespace load failed for ‘soundgen’ in gzfile(file, "rb"):
 无法打开链结
停止执行
- 4160_11550_000009_000000.wav: R analysis failed: Warning in gzfile(file, "rb") :
  无法打开压缩文件'/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/jsonlite/Meta/package.rds'，可能是因为'没有那个文件或目录'
错误: package or namespace load failed for ‘soundgen’ in loadNamespace(j <- i[[1L]], c(lib.loc, .libPaths()), versionCheck = vI[[j]]):
 不存在叫‘jsonlite’这个名字的程辑包
停止执行
- 4195_17507_000064_000000.wav: R analysis failed: Warning in gzfile(file, "rb") :
  无法打开压缩文件'/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/jsonlite/Meta/nsInfo.rds'，可能是因为'没有那个文件或目录'
错误: package or namespace load failed for ‘soundgen’ in gzfile(file, "rb"):
 无法打开链结
停止执行
- 4195_186237_000007_000001.wav: R analysis failed: Warning in gzfile(file, "rb") :
  无法打开压缩文件'/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/jsonlite/Meta/package.rds'，可能是因为'没有那个文件或目录'
错误: package or namespace load failed for ‘soundgen’ in loadNamespace(j <- i[[1L]], c(lib.loc, .libPaths()), versionCheck = vI[[j]]):
 不存在叫‘jsonlite’这个名字的程辑包
停止执行
- 4397_15668_000007_000003.wav: R analysis failed: 错误: package or namespace load failed for ‘soundgen’:
 loadNamespace()里算'rlang'时.onLoad失败了，详细内容：
  调用: gzfile(file, "rb")
  错误: 无法打开链结
停止执行
- 4406_16883_000025_000002.wav: R analysis failed: Warning in file(filename, "r") :
  无法打开文件'/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/jsonlite/R/jsonlite': 没有那个文件或目录
Error in file(filename, "r") : 无法打开链结
错误: package or namespace load failed for ‘soundgen’:
 程辑包‘jsonlite’里的R写碼载入失败
停止执行
- 446_123501_000012_000001.wav: R analysis failed: Warning in file(filename, "r") :
  无法打开文件'/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/lifecycle/R/lifecycle': 没有那个文件或目录
Error in file(filename, "r") : 无法打开链结
错误: package or namespace load failed for ‘soundgen’:
 程辑包‘lifecycle’里的R写碼载入失败
停止执行
- Additional failures omitted: 24
