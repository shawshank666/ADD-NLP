# Batch NLP Analysis Report

## Batch Info

- Input directory: /mnt/home/xiaoshilin/Data/LibriSeVoc/wavernn
- Stats CSV: /mnt/home/xiaoshilin/ADD-NLP/results/NLPanalysis/LibriSeVoc_wavernn/audio_stats.csv
- Audio suffixes: .wav
- Files discovered: 13201
- Successful or reused: 13158
- Failed: 43
- Approximate analyzed duration: 2032m 21.05s

## Aggregate Frame Labels

- None: 1178777
- Unvoiced: 1761208
- Subharmonics: 538118
- Sidebands: 1371422
- Chaos: 0
- Frequency jump: 28117

## Aggregate Segment Labels

- None: 237371
- Unvoiced: 296123
- Subharmonics: 301827
- Sidebands: 408165
- Chaos: 0
- Frequency jump: 28117

## Failures

- 1088_129236_000018_000004_gen.wav: [Errno 2] No such file or directory: '/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/bin/Rscript'
- 1116_132847_000023_000002_gen.wav: R analysis failed: /bin/sh: 0: cannot open /mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/bin/R: No such file
- 1116_132847_000024_000001_gen.wav: R analysis failed: Warning in gzfile(file, "rb") :
  cannot open compressed file '/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/jsonlite/R/jsonlite.rdx', probable reason 'No such file or directory'
Error in gzfile(file, "rb") : cannot open the connection
Error: package or namespace load failed for ‘soundgen’:
 unable to load R code in package ‘jsonlite’
Execution halted
- 1246_135815_000010_000003_gen.wav: R analysis failed: Error in gzfile(file, "rb") : cannot open the connection
In addition: Warning message:
In gzfile(file, "rb") :
  cannot open compressed file '/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/compiler/R/compiler.rdx', probable reason 'No such file or directory'
Error: unable to load R code in package ‘compiler’
Execution halted
- 1263_138246_000031_000001_gen.wav: R analysis failed: Warning in gzfile(file, "rb") :
  cannot open compressed file '/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/tools/R/sysdata.rdx', probable reason 'No such file or directory'
Error: package or namespace load failed for ‘soundgen’ in gzfile(file, "rb"):
 cannot open the connection
Execution halted
- 1355_39947_000021_000003_gen.wav: R analysis failed: Error in gzfile(file, "rb") : cannot open the connection
In addition: Warning message:
In gzfile(file, "rb") :
  cannot open compressed file '/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/compiler/R/compiler.rdx', probable reason 'No such file or directory'
Error: unable to load R code in package ‘compiler’
Execution halted
- 1355_39947_000025_000000_gen.wav: R analysis failed: Error: package or namespace load failed for ‘soundgen’:
 .onLoad failed in loadNamespace() for 'rlang', details:
  call: gzfile(file, "rb")
  error: cannot open the connection
Execution halted
- 1502_122615_000008_000002_gen.wav: R analysis failed: Warning in gzfile(file, "rb") :
  cannot open compressed file '/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/jsonlite/Meta/features.rds', probable reason 'No such file or directory'
Error: package or namespace load failed for ‘soundgen’ in gzfile(file, "rb"):
 cannot open the connection
Execution halted
- 1553_140047_000006_000002_gen.wav: R analysis failed: During startup - Warning messages:
1: In gzfile(file, "rb") :
  cannot open compressed file '/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/utils/Meta/package.rds', probable reason 'No such file or directory'
2: package ‘utils’ in options("defaultPackages") was not found 
Warning in HzToSemitones(ps[infl]) : NaNs produced
Error in write.csv(out, frames_csv, row.names = FALSE) : 
  could not find function "write.csv"
Execution halted
- 1841_179183_000018_000004_gen.wav: R analysis failed: Warning in gzfile(file, "rb") :
  cannot open compressed file '/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/rlang/Meta/package.rds', probable reason 'No such file or directory'
Error: package or namespace load failed for ‘soundgen’ in gzfile(file, "rb"):
 cannot open the connection
Execution halted
- 1926_147979_000005_000000_gen.wav: R analysis failed: Warning in gzfile(file, "rb") :
  cannot open compressed file '/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/jsonlite/Meta/package.rds', probable reason 'No such file or directory'
Error: package or namespace load failed for ‘soundgen’ in gzfile(file, "rb"):
 cannot open the connection
Execution halted
- 2002_139469_000013_000000_gen.wav: R analysis failed: Error: package or namespace load failed for ‘soundgen’:
 .onLoad failed in loadNamespace() for 'rlang', details:
  call: gzfile(file, "rb")
  error: cannot open the connection
Execution halted
- 2136_5147_000050_000003_gen.wav: R analysis failed: Warning in gzfile(file, "rb") :
  cannot open compressed file '/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/jsonlite/Meta/package.rds', probable reason 'No such file or directory'
Error: package or namespace load failed for ‘soundgen’ in loadNamespace(j <- i[[1L]], c(lib.loc, .libPaths()), versionCheck = vI[[j]]):
 there is no package called ‘jsonlite’
Execution halted
- 250_142276_000015_000016_gen.wav: R analysis failed: Warning in gzfile(file, "rb") :
  cannot open compressed file '/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/fastmap/Meta/package.rds', probable reason 'No such file or directory'
Error: package or namespace load failed for ‘soundgen’ in find.package(package, lib.loc, verbose = verbose):
 there is no package called ‘fastmap’
Execution halted
- 3240_131231_000031_000001_gen.wav: R analysis failed: Warning in file(filename, "r") :
  cannot open file '/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/jsonlite/R/jsonlite': No such file or directory
Error in file(filename, "r") : cannot open the connection
Error: package or namespace load failed for ‘soundgen’:
 unable to load R code in package ‘jsonlite’
Execution halted
- 3240_131232_000051_000000_gen.wav: R analysis failed: Error in file(filename, "r") : cannot open the connection
In addition: Warning message:
In file(filename, "r") :
  cannot open file '/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/compiler/R/compiler': No such file or directory
Error: unable to load R code in package ‘compiler’
Execution halted
- 3242_67153_000018_000001_gen.wav: R analysis failed: Error: package or namespace load failed for ‘soundgen’:
 .onLoad failed in loadNamespace() for 'rlang', details:
  call: gzfile(file, "rb")
  error: cannot open the connection
Execution halted
- 32_4137_000005_000002_gen.wav: R analysis failed: Error in file(filename, "r") : cannot open the connection
In addition: Warning message:
In file(filename, "r") :
  cannot open file '/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/compiler/R/compiler': No such file or directory
Error: unable to load R code in package ‘compiler’
Execution halted
- 3436_172162_000015_000001_gen.wav: R analysis failed: Warning in gzfile(file, "rb") :
  cannot open compressed file '/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/jsonlite/Meta/package.rds', probable reason 'No such file or directory'
Error: package or namespace load failed for ‘soundgen’ in find.package(package, lib.loc, verbose = verbose):
 there is no package called ‘jsonlite’
Execution halted
- 3526_176653_000002_000006_gen.wav: R analysis failed: Warning in gzfile(file, "rb") :
  cannot open compressed file '/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/jsonlite/Meta/package.rds', probable reason 'No such file or directory'
Error: package or namespace load failed for ‘soundgen’ in find.package(package, lib.loc, verbose = verbose):
 there is no package called ‘jsonlite’
Execution halted
- Additional failures omitted: 23
