# Batch NLP Analysis Report

## Batch Info

- Input directory: /mnt/home/xiaoshilin/Data/LibriSeVoc/wavenet
- Stats CSV: /mnt/home/xiaoshilin/ADD-NLP/results/NLPanalysis/LibriSeVoc_wavenet/audio_stats.csv
- Audio suffixes: .wav
- Files discovered: 13201
- Successful or reused: 13150
- Failed: 51
- Approximate analyzed duration: 2069m 59.40s

## Aggregate Frame Labels

- None: 1109106
- Unvoiced: 2315937
- Subharmonics: 538808
- Sidebands: 986471
- Chaos: 0
- Frequency jump: 17654

## Aggregate Segment Labels

- None: 246591
- Unvoiced: 336139
- Subharmonics: 348471
- Sidebands: 409330
- Chaos: 0
- Frequency jump: 17654

## Failures

- 1116_132851_000005_000001_gen.wav: R analysis failed: Error in gzfile(file, "rb") : cannot open the connection
Calls: getNamespace -> loadNamespace -> readRDS -> gzfile
In addition: Warning message:
In gzfile(file, "rb") :
  cannot open compressed file '/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/compiler/Meta/nsInfo.rds', probable reason 'No such file or directory'
Execution halted
- 1355_39947_000019_000009_gen.wav: R analysis failed: Warning in gzfile(file, "rb") :
  cannot open compressed file '/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/R6/Meta/nsInfo.rds', probable reason 'No such file or directory'
Error: package or namespace load failed for ‘soundgen’ in gzfile(file, "rb"):
 cannot open the connection
Execution halted
- 1502_122615_000048_000001_gen.wav: R analysis failed: Warning in gzfile(file, "rb") :
  cannot open compressed file '/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/lifecycle/Meta/nsInfo.rds', probable reason 'No such file or directory'
Error: package or namespace load failed for ‘soundgen’ in gzfile(file, "rb"):
 cannot open the connection
Execution halted
- 1553_140047_000013_000000_gen.wav: R analysis failed: Warning in gzfile(file, "rb") :
  cannot open compressed file '/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/fastmap/Meta/package.rds', probable reason 'No such file or directory'
Error: package or namespace load failed for ‘soundgen’ in gzfile(file, "rb"):
 cannot open the connection
Execution halted
- 1624_168623_000003_000004_gen.wav: R analysis failed: Warning in gzfile(file, "rb") :
  cannot open compressed file '/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/rlang/Meta/package.rds', probable reason 'No such file or directory'
Error: package or namespace load failed for ‘soundgen’ in gzfile(file, "rb"):
 cannot open the connection
Execution halted
- 1926_143879_000007_000012_gen.wav: R analysis failed: Warning in gzfile(file, "rb") :
  cannot open compressed file '/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/rlang/Meta/package.rds', probable reason 'No such file or directory'
Error: package or namespace load failed for ‘soundgen’ in gzfile(file, "rb"):
 cannot open the connection
Execution halted
- 196_122150_000013_000000_gen.wav: R analysis failed: Error in file(filename, "r") : cannot open the connection
In addition: Warning message:
In file(filename, "r") :
  cannot open file '/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/compiler/R/compiler': No such file or directory
Error: unable to load R code in package ‘compiler’
Execution halted
- 2007_132570_000021_000000_gen.wav: R analysis failed: /bin/sh: 0: cannot open /mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/bin/R: No such file
- 2092_145706_000012_000003_gen.wav: R analysis failed: Warning in gzfile(file, "rb") :
  cannot open compressed file '/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/R6/R/R6.rdx', probable reason 'No such file or directory'
Error in gzfile(file, "rb") : cannot open the connection
Error: package or namespace load failed for ‘soundgen’:
 unable to load R code in package ‘R6’
Execution halted
- 2136_5140_000011_000001_gen.wav: R analysis failed: Error: package or namespace load failed for ‘soundgen’:
 .onLoad failed in loadNamespace() for 'rlang', details:
  call: gzfile(file, "rb")
  error: cannot open the connection
Execution halted
- 2182_181183_000027_000000_gen.wav: R analysis failed: /bin/sh: 0: cannot open /mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/bin/R: No such file
- 2196_170379_000006_000001_gen.wav: R analysis failed: Error: package or namespace load failed for ‘soundgen’:
 .onLoad failed in loadNamespace() for 'rlang', details:
  call: gzfile(file, "rb")
  error: cannot open the connection
Execution halted
- 2289_152258_000011_000001_gen.wav: R analysis failed: Warning in gzfile(file, "rb") :
  cannot open compressed file '/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/jsonlite/R/jsonlite.rdx', probable reason 'No such file or directory'
Error in gzfile(file, "rb") : cannot open the connection
Error: package or namespace load failed for ‘soundgen’:
 unable to load R code in package ‘jsonlite’
Execution halted
- 2416_152139_000063_000002_gen.wav: R analysis failed: Warning in gzfile(file, "rb") :
  cannot open compressed file '/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/jsonlite/Meta/nsInfo.rds', probable reason 'No such file or directory'
Error: package or namespace load failed for ‘soundgen’ in gzfile(file, "rb"):
 cannot open the connection
Execution halted
- 2436_2481_000040_000003_gen.wav: R analysis failed: Warning in gzfile(file, "rb") :
  cannot open compressed file '/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/jsonlite/Meta/package.rds', probable reason 'No such file or directory'
Error: package or namespace load failed for ‘soundgen’ in find.package(package, lib.loc, verbose = verbose):
 there is no package called ‘jsonlite’
Execution halted
- 254_12312_000004_000011_gen.wav: R analysis failed: Error: package or namespace load failed for ‘soundgen’:
 .onLoad failed in loadNamespace() for 'rlang', details:
  call: gzfile(file, "rb")
  error: cannot open the connection
Execution halted
- 2836_5354_000072_000000_gen.wav: R analysis failed: Warning in gzfile(file, "rb") :
  cannot open compressed file '/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/rlang/Meta/package.rds', probable reason 'No such file or directory'
Error: package or namespace load failed for ‘soundgen’ in find.package(package, lib.loc, verbose = verbose):
 there is no package called ‘rlang’
Execution halted
- 2893_139310_000037_000001_gen.wav: R analysis failed: /bin/sh: 0: cannot open /mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/bin/R: No such file
- 298_126791_000078_000001_gen.wav: R analysis failed: Error: package or namespace load failed for ‘soundgen’:
 .onLoad failed in loadNamespace() for 'rlang', details:
  call: gzfile(file, "rb")
  error: cannot open the connection
Execution halted
- 302_123523_000020_000001_gen.wav: R analysis failed: Warning in gzfile(file, "rb") :
  cannot open compressed file '/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/tools/R/sysdata.rdx', probable reason 'No such file or directory'
Error: package or namespace load failed for ‘soundgen’ in gzfile(file, "rb"):
 cannot open the connection
Execution halted
- Additional failures omitted: 31
