# illustrations of common problems with visualizing NLP

setwd(dirname(rstudioapi::getActiveDocumentContext()$path)) 

library(soundgen)

## low dynamic range - disappearing subharmonics
sh = soundgen(
  sylLen = 800,
  pitch = c(280, 320, 310, 290, 220) * 2.5,
  rolloff = -3,
  subDep = c(0, 0, 20, 20, 0, 0),
  formants = c(700, 1600, 3200, 4300),
  temperature = .01
)
playme(sh)  # subh clearly audible

png('../pix/specs/dynamicRange_60.png', width = 12, height = 10, units = 'cm', res = 600)
spectrogram(sh, 16000, ylim = c(0, 2.5), dynamicRange = 60, osc = FALSE)
dev.off()

png('../pix/specs/dynamicRange_35.png', width = 12, height = 10, units = 'cm', res = 600)
spectrogram(sh, 16000, ylim = c(0, 2.5), dynamicRange = 35, osc = FALSE)
dev.off()


## alligator bellow requires a very long analysis window
# estimateVTL(c(180, 400))
al = soundgen(
  sylLen = 2000,
  ampl = c(-10, 0, -10, -20),
  pitch = c(70, 80, 70, 50),
  rolloff = -19,
  jitterDep = .1, 
  noise = -55,
  formants = NA, vocalTract = 40,
  amFreq = 15, amDep = c(20, 55, 50, 0), amShape = .15
)
playme(al)
spectrogram(al, 16000, ylim = c(0, .5), windowLength = 100)
spectrogram(al, 16000, ylim = c(0, .5), windowLength = 400)

png('../pix/specs/alligator_AM_wl100.png', width = 12, height = 10, units = 'cm', res = 600)
spectrogram(al, 16000, ylim = c(0, .5), windowLength = 100, heights = c(2, 1))
dev.off()

png('../pix/specs/alligator_AM_wl400.png', width = 12, height = 10, units = 'cm', res = 600)
spectrogram(al, 16000, ylim = c(0, .5), windowLength = 400, heights = c(2, 1))
dev.off()



## How rapid can FM become before we can no longer resolve it with a conventional spectrogram?
fmFreq = 50
pitch = 150
vibratoDep = 5  
semitonesToHz(HzToSemitones(150) + c(vibratoDep, -vibratoDep))
# 200.226 112.373   # pitch range with vibrato
s = suppressWarnings(soundgen(pitch = pitch, vibratoFreq = fmFreq, vibratoDep = vibratoDep, invalidArgAction = 'ignore', temperature = 0, formants = NULL, rolloffExact = 1, addSilence = 10))
spectrogram(s, 16000, ylim = c(0, .4), windowLength = 10)
playme(s)
playme(soundgen(sylLen = 2000, pitch = pitch*4, vibratoFreq = fmFreq*4, vibratoDep = vibratoDep, invalidArgAction = 'ignore', temperature = 0, formants = NULL, rolloffExact = 1, addSilence = 10))  # we perceive fmFreq as the pitch!

png('../pix/specs/FM_conventional_spectrogram.png', width = 12, height = 10, units = 'cm', res = 600)
spectrogram(s, 16000, ylim = c(0, .4), windowLength = 100, heights = c(3, 2))
dev.off()

png('../pix/specs/FM_reassigned_spectrogram.png', width = 12, height = 10, units = 'cm', res = 600)
spectrogram(s, 16000, specType = 'reassigned', ylim = c(0, .4), windowLength = 10, step = 1, heights = c(3, 2))
dev.off()



## Is every smudge chaos?
sm = soundgen(attackLen = c(0, 15), pitch = rnorm(16, 400, 2), 
              sylLen = 100, addSilence = 15, rolloff = c(-4, -8))
sm[1700:1701] = c(1, -1)
spectrogram(sm, 16000, windowLength = 20, osc = FALSE)
spectrogram(sm, 16000, windowLength = 20, heights = c(2, 1))

png('../pix/specs/smudge_chaos.png', width = 12, height = 10, units = 'cm', res = 600)
spectrogram(sm, 16000, windowLength = 20, osc = FALSE)
dev.off()

png('../pix/specs/smudge_chaos_osc.png', width = 12, height = 10, units = 'cm', res = 600)
spectrogram(sm, 16000, windowLength = 20, heights = c(1, 1))
dev.off()


