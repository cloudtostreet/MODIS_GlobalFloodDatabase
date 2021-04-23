#set working directory where the csv lives
setwd("/Users/bethtellman/Desktop/papers/GFD/figures/")

#this is the dataset of population exposed to floods in the WRI data and in the GFD
#for countries that passed the quality control threshold for inclusion
popcountrwri<-read.csv('data/gfd_popsummary.csv')
summary(popcountrwri)

#this summs the population exposed across rural, urban, and semi urban land use classes from GHSL
#2000 is the population exposed in 2000 and "delta" is the additional populatione exposed using 2015 population data
popcountrwri$floodpopGFD<-(popcountrwri$pop_2000_flood_rural+
  popcountrwri$pop_2000_flood_urban+ popcountrwri$pop_2000_flood_semiurban +
  popcountrwri$pop_delta_flood_urban + popcountrwri$pop_delta_flood_semiurban +
  popcountrwri$pop_delta_flood_rural)

#this code creates extended data figure #10
library(ggplot2)
ggplot (popcountrwri ,
        aes(log(P10_bh_100), log(floodpopGFD), colour= continent)) +
  labs(title="", x="Population (log) at risk of floods 100-year return period, GLOFRIS", y= "Population (log) exposed to floods, observed 2000-2018", colour= "")+
  geom_point(size=1)+
  geom_point(size=1)+
  #xlim(8,21)+
  #ylim(8,21)+
  theme(axis.text.x = element_text(size=12, vjust=0.6),
        axis.text.y = element_text(size=12, vjust=0.6),
        axis.title.x = element_text(size=18, vjust=0.6),
        axis.title.y = element_text(size=18, vjust=0.6),
        legend.text = element_text(size=12, vjust=0.6)
        )+
  geom_text(aes(label=country))+
  geom_abline(slope=1, intercept=0, colour="blue")+
  geom_smooth(method=lm, se=FALSE, fullrange=TRUE, color='#2C3E50')

ggplot (popcountrwri ,
        aes(log(P10_bh_100), log(sum), colour= continent)) +
  labs(title="", x="Population (log) at risk of floods, GLOFRIS", y= "Population (log) exposed to floods, observed 2000-2018", colour= "")+
  geom_point(size=1)+
  geom_point(size=1)+
  #xlim(8,21)+
  #ylim(8,21)+
  theme(axis.text.x = element_text(size=12, vjust=0.6),
        axis.text.y = element_text(size=12, vjust=0.6),
        axis.title.x = element_text(size=12, vjust=0.6),
        axis.title.y = element_text(size=12, vjust=0.6),
        legend.text = element_text(size=12, vjust=0.6)
  )+
  geom_text(aes(label=country))+
  abline()+
  geom_smooth(method=lm, se=FALSE, fullrange=TRUE, color='#2C3E50')

#pearson correlation between the two datasets
cor.test(popcountrwri$P10_bh_100, popcountrwri$floodpopGFD, method="pearson")
