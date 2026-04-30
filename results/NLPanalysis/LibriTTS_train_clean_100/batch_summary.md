# Batch NLP Analysis Report

## Batch Info

- Input directory: /mnt/data/xiaoshilin/Data/LibriTTS/LibriTTS/train-clean-100
- Stats CSV: /mnt/home/xiaoshilin/ADD-NLP/results/NLPanalysis/LibriTTS_train_clean_100/audio_stats.csv
- Audio suffixes: .wav
- Files discovered: 33236
- Successful or reused: 33172
- Failed: 64
- Approximate analyzed duration: 3198m 31.42s

## Aggregate Frame Labels

- None: 1725973
- Unvoiced: 3119771
- Subharmonics: 730100
- Sidebands: 2074128
- Chaos: 0
- Frequency jump: 26485

## Aggregate Segment Labels

- None: 344551
- Unvoiced: 492586
- Subharmonics: 419254
- Sidebands: 595226
- Chaos: 0
- Frequency jump: 26485

## Failures

- 1578/6379/1578_6379_000019_000002.wav: R analysis failed: Error: package or namespace load failed for ‘soundgen’:
 .onLoad failed in loadNamespace() for 'rlang', details:
  call: gzfile(file, "rb")
  error: cannot open the connection
Execution halted
- 3982/178459/3982_178459_000044_000005.wav: R analysis failed: During startup - Warning messages:
1: package ‘utils’ in options("defaultPackages") was not found 
2: package ‘stats’ in options("defaultPackages") was not found 
Error: package or namespace load failed for ‘soundgen’:
 .onLoad failed in loadNamespace() for 'utils', details:
  call: options(op.utils[toset])
  error: invalid value for 'editor'
Execution halted
- 40/222/40_222_000011_000004.wav: R analysis failed: Error: package or namespace load failed for ‘soundgen’:
 .onLoad failed in loadNamespace() for 'rlang', details:
  call: gzfile(file, "rb")
  error: cannot open the connection
Execution halted
- 40/222/40_222_000023_000002.wav: R analysis failed: Error in runHook(".onLoad", env, package.lib, package) : 
  cannot open file '/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/compiler/R/compiler.rdb': No such file or directory
Calls: getNamespace -> loadNamespace -> runHook
Execution halted
- 4014/186175/4014_186175_000013_000000.wav: R analysis failed: Warning in gzfile(file, "rb") :
  cannot open compressed file '/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/rlang/Meta/package.rds', probable reason 'No such file or directory'
Error: package or namespace load failed for ‘soundgen’ in loadNamespace(i, c(lib.loc, .libPaths()), versionCheck = vI[[i]]):
 there is no package called ‘rlang’
Execution halted
- 4018/103416/4018_103416_000009_000000.wav: R analysis failed: Warning in gzfile(file, "rb") :
  cannot open compressed file '/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/jsonlite/Meta/package.rds', probable reason 'No such file or directory'
Error: package or namespace load failed for ‘soundgen’ in find.package(package, lib.loc, verbose = verbose):
 there is no package called ‘jsonlite’
Execution halted
- 4018/103416/4018_103416_000012_000000.wav: R analysis failed: Error in gzfile(file, "rb") : cannot open the connection
Calls: getNamespace -> loadNamespace -> readRDS -> gzfile
In addition: Warning message:
In gzfile(file, "rb") :
  cannot open compressed file '/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/compiler/Meta/nsInfo.rds', probable reason 'No such file or directory'
Execution halted
- 405/130894/405_130894_000006_000001.wav: R analysis failed: Warning in gzfile(file, "rb") :
  cannot open compressed file '/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/fastmap/Meta/nsInfo.rds', probable reason 'No such file or directory'
Error: package or namespace load failed for ‘soundgen’ in gzfile(file, "rb"):
 cannot open the connection
Execution halted
- 405/130894/405_130894_000084_000000.wav: R analysis failed: Warning in file(filename, "r") :
  cannot open file '/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/lifecycle/R/lifecycle': No such file or directory
Error in file(filename, "r") : cannot open the connection
Error: package or namespace load failed for ‘soundgen’:
 unable to load R code in package ‘lifecycle’
Execution halted
- 412/126975/412_126975_000004_000001.wav: R analysis failed: Warning in gzfile(file, "rb") :
  cannot open compressed file '/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/jsonlite/Meta/package.rds', probable reason 'No such file or directory'
Error: package or namespace load failed for ‘soundgen’ in gzfile(file, "rb"):
 cannot open the connection
Execution halted
- 412/126975/412_126975_000005_000002.wav: R analysis failed: Error: package or namespace load failed for ‘soundgen’:
 .onLoad failed in loadNamespace() for 'rlang', details:
  call: gzfile(file, "rb")
  error: cannot open the connection
Execution halted
- 412/126975/412_126975_000021_000000.wav: R analysis failed: Error: package or namespace load failed for ‘soundgen’:
 .onLoad failed in loadNamespace() for 'rlang', details:
  call: gzfile(file, "rb")
  error: cannot open the connection
Execution halted
- 4160/11549/4160_11549_000006_000000.wav: R analysis failed: Error in runHook(".onLoad", env, package.lib, package) : 
  cannot open file '/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/compiler/R/compiler.rdb': No such file or directory
Calls: getNamespace -> loadNamespace -> runHook
Execution halted
- 4160/14187/4160_14187_000023_000000.wav: [Errno 2] No such file or directory: '/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/bin/Rscript'
- 4195/17507/4195_17507_000012_000000.wav: R analysis failed: Error: package or namespace load failed for ‘soundgen’:
 .onLoad failed in loadNamespace() for 'rlang', details:
  call: gzfile(file, "rb")
  error: cannot open the connection
Execution halted
- 4195/186237/4195_186237_000055_000000.wav: R analysis failed: Warning in gzfile(file, "rb") :
  cannot open compressed file '/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/jsonlite/Meta/features.rds', probable reason 'No such file or directory'
Error: package or namespace load failed for ‘soundgen’ in gzfile(file, "rb"):
 cannot open the connection
Execution halted
- 4214/7146/4214_7146_000007_000002.wav: R analysis failed: Rscript execution error: No such file or directory
- 4214/7146/4214_7146_000011_000001.wav: R analysis failed: Warning in gzfile(file, "rb") :
  cannot open compressed file '/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/fastmap/Meta/package.rds', probable reason 'No such file or directory'
Error: package or namespace load failed for ‘soundgen’ in find.package(package, lib.loc, verbose = verbose):
 there is no package called ‘fastmap’
Execution halted
- 4340/15220/4340_15220_000050_000000.wav: R analysis failed: Error: package or namespace load failed for ‘soundgen’ in get0(".packageName", env, inherits = FALSE):
 cannot open file '/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/jsonlite/R/jsonlite.rdb': No such file or directory
Execution halted
- 4340/15220/4340_15220_000063_000002.wav: R analysis failed: Warning in gzfile(file, "rb") :
  cannot open compressed file '/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/tools/Meta/package.rds', probable reason 'No such file or directory'
Error: package or namespace load failed for ‘soundgen’ in gzfile(file, "rb"):
 cannot open the connection
Execution halted
- Additional failures omitted: 44
