# This code makes extended data figure 8, a sensitivty analysis of
# changes in predicted population exposured to floods form the WRI Aqueduct model
# at different return periods

#add working directory for .csv files
setwd("/Users/bethtellman/Desktop/papers/GFD/gfd_nature-master/data")

library(ggplot2)
library(countrycode)
library(plyr)

#ssp2 population data
#add total pop data from SSP2
#2010
SSP22010<-read.csv("data/SSP2010.csv")
SSP22010$pop2010<-SSP22010$sum
#2030
SSP22030<-read.csv("data/SSP2030.csv")
SSP22010$pop2030<-SSP22030$sum
#join 2010 ands 2030 data
SSP2<-join(SSP22010,SSP22030, by= "system.index")
#assign country codes
SSP2$cc<- countrycode(SSP2$country, "country.name", "iso2c" ,  origin_regex=TRUE)

#aqueduct flood data, see Aqueduct dictionary for explanation of each column name
Aquecountry0<-read.csv('data/aqueductcountrydata.csv')
#assign it country codes and names
Aquecountry0$cc<- countrycode(Aquecountry0$unit_name, "country.name", "iso2c" ,  origin_regex=TRUE)
Aquecountry0$continent<- countrycode(Aquecountry0$cc, "iso2c", "continent" ,  origin_regex=TRUE)

#join SSP and Aqueduct data
Aquecountry<- join(Aquecountry0,SSP2, by="cc")

#change ratio, porportional changes in flood population exposed vs. population growth from SSP
changeccp500<-(Aquecountry$P30_28_500/Aquecountry$pop2030)/(Aquecountry$P10_bh_500/Aquecountry$pop2010)
changeccp100<-(Aquecountry$P30_28_100/Aquecountry$pop2030)/(Aquecountry$P10_bh_100/Aquecountry$pop2010)
changeccp250<-(Aquecountry$P30_28_250/Aquecountry$pop2030)/(Aquecountry$P10_bh_250/Aquecountry$pop2010)
changeccp50<-(Aquecountry$P30_28_50/Aquecountry$pop2030)/(Aquecountry$P10_bh_50/Aquecountry$pop2010)
changeccp25<-(Aquecountry$P30_28_25/Aquecountry$pop2030)/(Aquecountry$P10_bh_25/Aquecountry$pop2010)
changeccp10<-(Aquecountry$P30_28_10/Aquecountry$pop2030)/(Aquecountry$P10_bh_10/Aquecountry$pop2010)
#store in the data frame
Aquecountry$changeccp500<-changeccp500
Aquecountry$changeccp100<-changeccp100
Aquecountry$changeccp250<-changeccp250
Aquecountry$changeccp50<-changeccp50
Aquecountry$changeccp25<-changeccp25
Aquecountry$changeccp10<-changeccp10

#abschange
Aquecountry$changeccabs500<-Aquecountry$P30_28_500-Aquecountry$P10_bh_500
Aquecountry$changeccabs100<-Aquecountry$P30_28_100-Aquecountry$P10_bh_100
Aquecountry$changeccabs250<-Aquecountry$P30_28_250-Aquecountry$P10_bh_250
Aquecountry$changeccabs50<-Aquecountry$P30_28_50-Aquecountry$P10_bh_50
Aquecountry$changeccabs25<-Aquecountry$P30_28_25-Aquecountry$P10_bh_25
Aquecountry$changeccabs10<-Aquecountry$P30_28_10-Aquecountry$P10_bh_10

#percentchange
Aquecountry$changeccper500<-(Aquecountry$P30_28_500-Aquecountry$P10_bh_500)/Aquecountry$P10_bh_500*100
Aquecountry$changeccper100<-(Aquecountry$P30_28_100-Aquecountry$P10_bh_100)/Aquecountry$P10_bh_250*100
Aquecountry$changeccper250<-(Aquecountry$P30_28_250-Aquecountry$P10_bh_250)/Aquecountry$P10_bh_100*100
Aquecountry$changeccper50<-(Aquecountry$P30_28_50-Aquecountry$P10_bh_50)/Aquecountry$P10_bh_50*100
Aquecountry$changeccper25<-(Aquecountry$P30_28_25-Aquecountry$P10_bh_25)/Aquecountry$P10_bh_25*100
Aquecountry$changeccper10<-(Aquecountry$P30_28_10-Aquecountry$P10_bh_10)/Aquecountry$P10_bh_10*100
library(reshape2)

#melt data frame, aqueduct flood population exposure
AQmeltp<-melt(Aquecountry, id.vars = c("continent", "unit_name"), measure.vars= c('changeccp500','changeccp250','changeccp100',
                                                                                 'changeccp25',
                                                                                 'changeccp10'))
library(dplyr)
AQmeltp <- AQmeltp %>%
  mutate(variable_rec = factor(recode(variable,
                               "changeccp500"="500",
                               "changeccp250"="250",
                               "changeccp100"="100",
                               "changeccp25"="25",
                               "changeccp10"="10")))

#melt data frame, aqueduct flood population exposure in 2030
AQmelt2030<-melt(Aquecountry, id.vars = c("continent", "unit_name"), measure.vars= c('P30_28_500', 'P30_28_250','P30_28_100',
                                                                                  'P30_28_50','P30_28_25', 'P30_28_10'))
#absolute change
AQmeltabschange<-melt(Aquecountry, id.vars = c("continent", "unit_name"), measure.vars= c('changeccabs500','changeccabs250','changeccabs100',
                                                                                          'changeccabs25',
                                                                                          'changeccabs10'))
#recode for plotting
AQmeltabschange<- AQmeltabschange%>%
  mutate(variable_rec = factor(recode(variable,
                                      "changeccabs500"="500",
                                      "changeccabs250"="250",
                                      "changeccabs100"="100",
                                      "changeccabs25"="25",
                                      "changeccabs10"="10")))

#percentchange
AQmeltperchange<-melt(Aquecountry, id.vars = c("continent", "unit_name"), measure.vars= c('changeccper500','changeccper250','changeccper100',
                                                                                          'changeccper25',
                                                                                          'changeccper10'))
#recode for plotting
AQmeltperchange<- AQmeltperchange%>%
  mutate(variable_rec = factor(recode(variable,
                                      "changeccper500"="500",
                                      "changeccper250"="250",
                                      "changeccper100"="100",
                                      "changeccper25"="25",
                                      "changeccper10"="10")))

#remove obs with NA in column
AQmeltabschangenoNA<-AQmeltabschange[!is.na(AQmeltabschange$continent),]
AQmeltpNA<-AQmeltp[!is.na(AQmeltp$continent),]
AQmeltperchangeNA<-AQmeltperchange[!is.na(AQmeltperchange$continent),]

#this is to make extended data figure 7
pcp<-ggplot(AQmeltpNA, aes(x=variable_rec, y=value, fill=continent))

library(scales)
library(Hmisc)
prop<-pcp+ 
  geom_boxplot()+
  ggtitle("d")+
  labs(y= "change in proportion \n pop. exposed to floods 2030-2010", x="return period ")+
  #stat_summary(fun.data = mean_cl_boot, na.rm=TRUE, geom = "pointrange", position=position_dodge(.5),width = 0.2)+
  theme(plot.title = element_text(size=8 * ggplot2:::.pt,  face = "bold"),
        text = element_text(size=5 * ggplot2:::.pt),
        axis.text.x=element_text(size=5 * ggplot2:::.pt),
        axis.title.y=element_text(size=5 * ggplot2:::.pt),
        axis.text.y=element_text(size=5 * ggplot2:::.pt))
prop

Aquecountry$popgrowth<-(Aquecountry$pop2030-Aquecountry$pop2010)/Aquecountry$pop2010*100
AquecountryNA<-Aquecountry[!is.na(Aquecountry$continent),]

pop<-ggplot(AquecountryNA, aes(y=popgrowth, x=continent, fill=continent)) +
  geom_boxplot()+
  ggtitle("c")+
  labs(y= "percent increase \n total population 2030-2010")+
  #stat_summary(fun.data = mean_cl_boot, na.rm=TRUE, geom = "pointrange", position=position_dodge(.5),width = 0.2)+
  theme(plot.title = element_text(size=8 * ggplot2:::.pt,  face = "bold"),
        axis.text.x=element_blank(),
        axis.title.x=element_blank(),
        text = element_text(size=5 * ggplot2:::.pt),
        axis.title.y=element_text(size=5 * ggplot2:::.pt),
        axis.text.y=element_text(size=5 * ggplot2:::.pt))
pop


pcabschange<-ggplot(AQmeltabschangenoNA, aes(x=variable_rec, y=(value), fill=continent))
abs<-pcabschange+ ggtitle("a")+
  geom_boxplot()+
  #ylim(0,20)+
  labs(y= "change in total \n pop. exposed to floods 2030-2010", x="return period ")+
  #stat_summary(fun.data = mean_cl_boot, na.rm=TRUE, geom = "pointrange", position=position_dodge(.5), width = 0.2) +
#scale_y_continuous(labels=unit_format(units="M", scale= 1e-6))+
  #scale_y_continuous( trans="log10")+
  scale_y_log10(breaks = trans_breaks("log10", function(x) 10^x),
                labels = trans_format("log10", math_format(10^.x))) +
  annotation_logticks(sides="l") +
  #coord_trans(y = "log10")+
  theme(plot.title = element_text(size=8 * ggplot2:::.pt,  face = "bold"),
        text = element_text(size=5 * ggplot2:::.pt),
        axis.text.x=element_text(size=5 * ggplot2:::.pt),
        axis.title.y=element_text(size=5 * ggplot2:::.pt),
        axis.text.y=element_text(size=5 * ggplot2:::.pt))
abs
pperchange<-ggplot(AQmeltperchangeNA, aes(x=variable_rec, y=value, fill=continent))

per<-pperchange+ ggtitle("b")+
  geom_boxplot()+
  labs(y= "percent increase \n pop. exposed to floods 2030-2010", x="return period ")+
  #stat_summary(fun.data = mean_cl_boot, na.rm=TRUE, geom = "pointrange", position=position_dodge(.5), width = 0.2) +
    theme(plot.title = element_text(size=8 * ggplot2:::.pt,  face = "bold"),
          text = element_text(size=5 * ggplot2:::.pt),
          axis.text.x=element_text(size=5 * ggplot2:::.pt),
          axis.title.y=element_text(size=5 * ggplot2:::.pt),
          axis.text.y=element_text(size=5 * ggplot2:::.pt))
per
library(ggpubr)
boxes<-ggarrange(abs,per, pop,prop, ncol=2, nrow=2 ,common.legend= TRUE)
boxes
