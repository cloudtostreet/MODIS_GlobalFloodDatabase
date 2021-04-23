#main GFD numbers
GFDmainstats<-read.csv('data/GFDabove_13_wBias.csv')

colnames(GFDmainstats)

#to make graphs of bias factor for GHSL/HRSL data
mean(GFDmainstats$bias_factor, na.rm=TRUE)
sd(GFDmainstats$bias_factor, na.rm=TRUE)
hist(GFDmainstats$bias_factor, na.rm=TRUE)
boxplot(GFDmainstats$bias_factor~GFDmainstats$continent, ylab="HRSL/GHSL population exposed estimates")


#mean proportion of population exposed to floods 2000-2015 in GFD with GHSL
mean(GFDmainstats$relexp, na.rm=TRUE)
sd(GFDmainstats$relexp, na.rm=TRUE)
hist(GFDmainstats$relexp)

#total new number of people exposed to floods with population growth with GHSL
sum(GFDmainstats$absolutechangef, na.rm=TRUE)

#total new number of people exposed to floods with population growth with HRSL
sum(GFDmainstats$absolutechangef*GFDmainstats$bias_factor, na.rm=TRUE)

