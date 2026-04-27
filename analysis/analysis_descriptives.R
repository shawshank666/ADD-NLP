setwd(dirname(rstudioapi::getActiveDocumentContext()$path)) 

library(soundgen)
library(ggplot2)
library(patchwork)
library(randomForest)

if (FALSE) {
  # keep only the annotations of 1518 audio files available in the supplementary
  # materials to Anikin et al. (2023) Beyond speech
  df = read.csv('../data/nlp_manual.csv')
  audio_files = list.files('../sounds/beyond_speech')
  df = df[which(df$file %in% audio_files), ]
  write.csv(df, '../data/nlp_manual.csv', row.names = FALSE)
}

if (FALSE) {
  # acoustic analysis
  path_to_audio = '../sounds/beyond_speech'
  sounds = list.files(path_to_audio, pattern = '.wav')  # 1518 recordings
  an_manual = analyze(path_to_audio, pitchManual = '../data/pitch_manual_1745.csv', 
                      amRange = c(40, 150), silence = 0, cores = 4)
  # saveRDS(an_manual, '../data/bs_analyze.RDS')
  # 
  # an_autom = analyze(path_to_audio, amRange = c(40, 150), silence = 0, cores = 4)
  # saveRDS(an_autom, '../data/bs_analyze_autom.RDS')
  
  an_manual = readRDS('../data/bs_analyze.RDS')
  # an_manual = readRDS('../data/bs_analyze_autom.RDS')
  # View(an_manual$detailed[[1]] [which(an_manual$detailed[[1]]$voiced), ])
  step = diff(an_manual$detailed[[1]]$time[1:2])
  all_ann = read.csv('../data/nlp_manual.csv')
  length(unique(all_ann$file))
  txt_wo_txt = xfun::sans_ext(all_ann$file)
  nlp_lbls = unique(all_ann$label)
  
  out = NULL
  time_start = proc.time()
  for (i in 1:length(sounds)) {  # 1:length(sounds)
    f = sounds[i]
    a = an_manual$detailed[[i]]
    if (length(a) == 0) next
    a[, nlp_lbls] = FALSE
    
    # get NLP annotations (don't care about pitch jumps for now)
    nlp = all_ann[which(txt_wo_txt == xfun::sans_ext(f)), ]
    if (nrow(nlp) > 0) { # there are some NLPs
      # get the indices of frames with NLPs
      nFrames = nrow(a)  # == floor(a$duration * 1000 / step)
      # time stamps in analyze() start at (0 + step), so the first frame is 0-step ms
      nlp$frame_start = round(nlp$from / step) + 1
      nlp$frame_start[nlp$frame_start < 1] = 1
      nlp$frame_end = round(nlp$to / step) + 1
      nlp$frame_end[nlp$frame_end > nFrames] = nFrames
      
      # mark frames with NLPs in the output of analyze()
      for (j in 1:nrow(nlp)) {
        a[nlp$frame_start[j]:nlp$frame_end[j], nlp$label[j]] = TRUE
      }
    }
    a = cbind(data.frame(file = f), a)
    out = rbind(out, a)
    reportTime(i = i, nIter = length(sounds), time_start = time_start)
  }
  
  for (i in 1:nrow(out)) {
    out$cat[i] = switch(substr(as.character(out$file[i]), 1, 4),
                        'nonv' = 'Nonverbal',
                        'sing' = 'Singing',
                        'spee' = 'Speech')
  } 
  table(out$cat)
  
  ## add features from nonlinear time series analysis
  # ph_all = phasegram(path_to_audio, windowLength = 25, bins = 20, plot = FALSE, cores = 4)  # 26 h!!!
  # saveRDS(ph_all, '../data/phasegram.rds')
  ph_all = readRDS('../data/phasegram.rds')
  # colnames(ph_all[[1]]$descriptives)
  vars_to_add = c('shannon', 'nPeaks', 'ed', 'd2', 'ml', 'sur')
  nf = length(ph_all)
  time_start = proc.time()
  for (i in 1:nf) {
    idx_out = which(out$file == names(ph_all)[i])
    if (length(idx_out) > 0) {
      m_i = ph_all[[i]]$descriptives[, vars_to_add]
      out[idx_out, vars_to_add] = suppressWarnings(soundgen:::interpolMatrix(
        m_i, nr = length(idx_out)))
      reportTime(i, time_start, nf)
    }
  }
  
  saveRDS(out, '../data/bs_per_frame.RDS')
  # saveRDS(out, '../data/bs_per_frame_autom.RDS')
  
  # total duration
  tf = aggregate(duration ~ file, out, unique)
  nrow(tf)  # 1518 files
  sum(tf$duration) / 60 / 60  # total dur = 2 h
}

df = readRDS('../data/bs_per_frame.RDS')
# df = df[df$voiced, ]
mean(df$ampl > .01) # 85%
df = df[df$ampl > .01, ]
nlp_vars = c('sh', 'c', 'sb', 'fry')
df$nlp = as.character(apply(df[, nlp_vars], 1, function(x) nlp_vars[which(x)]))
table(df$nlp)
df$nlp[df$nlp %in% c('c', 'c("c", "sb")', 'c("sh", "c")')] = 'Chaos'
df$nlp[df$nlp == 'c("sh", "sb")'] = 'Subharmonics'
df$nlp[df$nlp == 'character(0)'] = 'None'
df$nlp[df$nlp == 'fry'] = 'Vocal fry'
df$nlp[df$nlp == 'sb'] = 'Sidebands'
df$nlp[df$nlp == 'sh'] = 'Subharmonics'
df = df[df$nlp != 'Vocal fry', ]
df$nlp[!df$voiced] = 'Unvoiced'
df$nlp = factor(df$nlp, levels = rev(c('None', 'Subharmonics', 'Sidebands', 'Chaos', 'Unvoiced')))
df$cat = factor(df$cat, levels = rev(c('Speech', 'Nonverbal', 'Singing')))
table(df$nlp)
# table(is.na(df$amEnvDep), is.na(df$sh))
# table(df$voiced, df$sh)
# head(df)
# colnames(df)
# summary(df$sh)

ggplot(df, aes(HNR, cat, color = nlp)) +
  geom_boxplot(outlier.size = .1) + xlab('dB') + ylab('') + ggtitle('HNR') 

sumtab = as.data.frame(matrix(c(
  'amEnvDep', 'AM from envelope',
  'amMsPurity', 'AM from MS',
  'CPP', 'CPP',
  'entropy', 'Wiener entropy',
  'entropySh', 'Shannon entropy',
  'HNR', 'HNR',
  'roughness', 'Roughness',
  'subDep', 'SubDep',
  'shannon', 'Poincare entropy',
  # 'nPeaks', 'Poincare nPeaks',
  'ed', 'Embedding dim',
  'd2', 'Correlation dim D2',
  # 'ml', 'Lyapunov exp',
  'sur', 'Surrogate data'
), ncol = 2, byrow = TRUE))
colnames(sumtab) = c('orig', 'fmt')
# R2 per variable from simple linear regression
for (i in 1:nrow(sumtab)) {
  formula_i = as.formula(paste0(sumtab$orig[i], '~ nlp'))
  mod = lm(formula_i, data = df[df$voiced, ])
  sm = summary(mod)
  sumtab$r2[i] = sm$r.squared
}
# order according to how much variance in a particular acoustic characteristic is explained by the presence of NLP in a VOICED frame (ignore voiceless)
sumtab$fmt = paste0(sumtab$fmt, '\n', round(sumtab$r2 * 100), '%')
sumtab = sumtab[order(sumtab$r2, decreasing = TRUE), ]
sumtab$fmt = factor(sumtab$fmt, levels = sumtab$fmt)

df_long = reshape2::melt(df[, c('nlp', 'cat', sumtab$orig)])
df_long$fmt = sumtab$fmt[match(df_long$variable, sumtab$orig)]
# order according to how much variance in a particular acoustic characteristic is explained by the presence of NLP in a VOICED frame (ignore voiceless)
df_long$fmt = factor(df_long$fmt, levels = sumtab$fmt[order(sumtab$r2, decreasing = TRUE)])
df_long$value[df_long$variable == 'amMsPurity' & df_long$value < -50] = NA  # remove extreme outliers (super low amMsPurity in some unvoiced frames) to make the plot easier to read

ggplot(df_long, aes(value, cat, color = nlp)) +
  geom_boxplot(outlier.size = .1) +
  # coord_cartesian(xlim = quantile(df_long$value, probs = c(0.1, 0.9), na.rm = TRUE)) +
  # geom_text(data = sumtab, aes(-Inf, Inf, label = paste0('R2 = ', round(r2, 2))), inherit.aes = FALSE, hjust = 0, vjust = 1, size = 3) +
  facet_wrap(~fmt, scales = 'free') +
  scale_color_discrete(guide = guide_legend(reverse = TRUE)) +
  xlab('') + ylab('') +
  theme_bw() +
  theme(panel.grid = element_blank(),
        legend.title = element_blank(),
        legend.position = 'top')
# ggsave('../pix/descr.png', width = 25, height = 18, units = 'cm', dpi = 600)


myvars = c('amEnvDep', 'amMsPurity', 'CPP', 'entropy', 'entropySh', 'harmEnergy', 'harmHeight', 'HNR', 'roughness', 'subDep')
myvars[which(!myvars %in% colnames(df))]
library(randomForest)
df1 = droplevels(na.omit(df[, c('nlp', myvars)]))  # 100K, only voiced frames
mod_rf = randomForest(x = df1[, myvars], y = df1$nlp)
mod_rf
mean(mod_rf$confusion[, 'class.error']) # balanced accuracy = 44%
varImpPlot(mod_rf)



## Analysis of perceptual roughness
ms1 = modulationSpectrum('/home/allgoodguys/Documents/Research/epistles/023_harsh-is-large/sounds/synthetic', amRes = NULL, plot = FALSE, cores = 4)
rough1 = unlist(ms1$roughness)

ms2 = audSpectrogram('/home/allgoodguys/Documents/Research/epistles/023_harsh-is-large/sounds/synthetic', output = 'roughness', roughSD = 3, nFilters = 128, plot = FALSE, cores = 4)
rough2 = unlist(lapply(ms2, function(x) median(x$roughness, na.rm = TRUE)))

rat = read.csv('/home/allgoodguys/Documents/Research/epistles/023_harsh-is-large/ns1_ratings/data/ns1.csv')
ag = aggregate(response ~ sound, rat[rat$scale == 'roughness', ], median)
ag$rough_MPS = rough1[match(ag$sound, xfun::sans_ext(ms1$summary$file))]
ag$rough_audSpec = rough2[match(ag$sound, xfun::sans_ext(ms1$summary$file))]

write.csv(df, '../data/roughness_harsh-is-large.csv', row.names = FALSE)

