# Batch NLP Analysis Report

## Batch Info

- Input directory: /mnt/home/xiaoshilin/Data/LibriSeVoc/parallel_wave_gan
- Stats CSV: /mnt/home/xiaoshilin/ADD-NLP/results/NLPanalysis/LibriSeVoc_parallel_wave_gan/audio_stats.csv
- Audio suffixes: .wav
- Files discovered: 13201
- Successful or reused: 13199
- Failed: 2
- Approximate analyzed duration: 2067m 6.93s

## Aggregate Frame Labels

- None: 1187869
- Unvoiced: 1836307
- Subharmonics: 534659
- Sidebands: 1374049
- Chaos: 0
- Frequency jump: 28193

## Aggregate Segment Labels

- None: 256689
- Unvoiced: 302125
- Subharmonics: 312327
- Sidebands: 390898
- Chaos: 0
- Frequency jump: 28193

## Failures

- 2691_156755_000010_000002_gen.wav: R analysis failed: Warning in gzfile(file, "rb") :
  cannot open compressed file '/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/jsonlite/Meta/package.rds', probable reason 'No such file or directory'
Error: package or namespace load failed for ‘soundgen’ in gzfile(file, "rb"):
 cannot open the connection
Execution halted
- 6476_96661_000007_000001_gen.wav: R analysis failed: Warning in gzfile(file, "rb") :
  cannot open compressed file '/mnt/home/xiaoshilin/.conda/envs/voicedeepfake/lib/R/library/lifecycle/Meta/package.rds', probable reason 'No such file or directory'
Error: package or namespace load failed for ‘soundgen’ in loadNamespace(j <- i[[1L]], c(lib.loc, .libPaths()), versionCheck = vI[[j]]):
 there is no package called ‘lifecycle’
Execution halted
