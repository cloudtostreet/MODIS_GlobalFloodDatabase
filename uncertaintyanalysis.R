#main GFD numbers

GFDmainstats<-read.csv('data/GFDabove_13_wBias.csv')

#this script generate the uncertainty metrics and quadrat plot in the Supplementary discussion

#how different would population have to be to "flip" the trend

GFDmainstats$floodpop2000<-GFDmainstats$pop_2000_flood_rural+GFDmainstats$pop_2000_flood_semiurban+GFDmainstats$pop_2000_flood_urban
GFDmainstats$pop2000<-(GFDmainstats$pop_2000_all_rural+GFDmainstats$pop_2000_all_semiurban+GFDmainstats$pop_2000_all_urban)
GFDmainstats$pop2015<-(GFDmainstats$pop_2000_all_rural+GFDmainstats$pop_2000_all_semiurban+GFDmainstats$pop_2000_all_urban+
                         GFDmainstats$pop_delta_all_rural+GFDmainstats$pop_delta_all_semiurban+GFDmainstats$pop_delta_all_urban)
GFDmainstats$floodpop2015<-GFDmainstats$floodpop2000+GFDmainstats$pop_delta_flood_rural+GFDmainstats$pop_delta_flood_semiurban+GFDmainstats$pop_delta_flood_urban

#equation 2, solve for flood pop in 2015 if no trend were present
GFDmainstats$x<-(GFDmainstats$floodpop2000/GFDmainstats$pop2000)*GFDmainstats$pop2015
#euquation 3, solve for margin of error
GFDmainstats$errorrange<-GFDmainstats$floodpop2015-GFDmainstats$x

#estimate population in floodplain for HRSL
GFDmainstats$HRSL2015<-GFDmainstats$floodpop2015*GFDmainstats$bias_factor

#equation 4, uncertainty range for HRSL
GFDmainstats$uncertaintyrange<-GFDmainstats$errorrange-(GFDmainstats$floodpop2015-GFDmainstats$HRSL2015)
#normalize by floodpop 2015 GHSL
GFDmainstats$uncperc<-GFDmainstats$uncertaintyrange/GFDmainstats$floodpop2015

#exploratory graphs of the data
hist((GFDmainstats$uncertaintyrange))
min(GFDmainstats$uncperc)
max(GFDmainstats$uncperc)
plot(GFDmainstats$uncertaintyrange/1000000,GFDmainstats$relexp)
plot(GFDmainstats$uncertaintyrange,GFDmainstats$relexp)
#percentchange


#quadrant plot, Figure 2 in the paper
library(ggplot2)
library(ggrepel)
p<-ggplot(GFDmainstats, aes(x=uncperc, y=relexp, color=continent, label= unit_name)) +
  geom_point(size=.5) +
  #lims(x=c(0,6),y=c(0,4)) +
  scale_x_continuous(limits= c(-2,2))+
  #,labels=c("0" = "decreasing population", "3" = "increasing population"))+
  scale_y_continuous(expand = c(0, 0),
                     limits= c(0,6))+
  #,labels=c(".5" = "population growth", "3" = "climate change"))+
  #geom_label_repel(size = 1,
  #fill = "deepskyblue",
  #colour = "black",
  #min.segment.length = unit(0, "lines"))+
  theme_minimal() +
  coord_fixed() +
  geom_vline(xintercept = 0) + geom_hline(yintercept = 1) +
  geom_text(aes(label = cc),
            position = "jitter", hjust=0.6, vjust=1.1, size = 3) +
  labs(x = "Uncertainty feasibility", 
       y = "Flood trend")+
  #annotate("text", x = 3, y = 0, label = "C Demographic Risk")+
  annotate("text", x = 1, y = .5, label = "unc. high for dec.")+
  annotate("text", x = -1.5, y = .5, label = "unc. low ")+
  annotate("text", x = -1.5, y = 2.5, label = "unc. low ")+
  annotate("text", x = 1, y = 4, label = " unc. high for inc.")+
  theme(axis.title.x = element_text(size = 16),
        axis.title.y = element_text(size = 16),
        legend.text=element_text(size=16), legend.title=element_text(size=14))

p

#remove uncertain countries, recalculte mean of trend reported in the paper
#these are the uncertain countries
GFDmainstatsuncertain<-subset(GFDmainstats, GFDmainstats$uncperc>0)
GFDmainstatscertain<-subset(GFDmainstats, GFDmainstats$uncperc<0)

#recalculate flood trend in paper if uncertain countries are remove
mean(GFDmainstatscertain$relexp, na.rm=TRUE)


