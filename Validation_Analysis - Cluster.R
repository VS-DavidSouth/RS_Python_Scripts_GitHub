################## Validation_Analysis.R #######################

############################
####### DESCRIPTION ########
############################

#
# Created by Grace Kuiper, 4/25/19
#
# Script Description:
#      This script will analyze the results of the HPAI hybrid model validation. The results of three
#      primary validation methods - Buffer Capture, Grid Density, and Ellipse Overlap - will be analyzed
#      and figures will be produced for communicating results. An analysis of distances between farms
#      are also included. 
#
# DS notes: it should probably be documented that the user should install the tidyverse, data.table, and
#           gsubfn packages. 

########################################
##################SETUP#################
########################################

library(tidyverse)
library(data.table)
library(gsubfn)

########################################
##############GRID DENSITY##############
########################################

grid_density_home <- "O:/AI Modeling Coop Agreement 2017/Grace Cap Stone Validation/Validation_Results/Grid_Density"

grids <- list.files(path=grid_density_home, full.names = T, recursive = F)
x <- c("AR_Cluster", "AR_Logan", "AR_Yell","AR_Scott")
grids <- grids[grepl(paste(x, collapse = "|"), grids)]

AutoReview_grids <- data.frame()
TP_FN_grids <- data.frame()
FLAPS_grids <- data.frame()

#      Import Grid Density results into separate data.frames based on
#      data/model type: hybrid, FLAPS, ground truth
for (i in 1:length(grids)) {
  if (grepl("AutoReview",grids[i])){
    AutoReview <- fread(grids[i],blank.lines.skip = T,stringsAsFactors = F,
                        header = T, fill = T)
    AutoReview$County <- strapply(grids[i],"Grid_Density/(.*)_AutoReview_Grid",simplify=TRUE)
    AutoReview_grids <- rbind(AutoReview_grids,AutoReview,fill=TRUE)
  }
  if (grepl("TP_FN",grids[i])){
    TP_FN <- fread(grids[i],blank.lines.skip = T,stringsAsFactors = F,
                   header = T, fill = T)
    TP_FN$County <- strapply(grids[i],"Grid_Density/(.*)_TP_FN_Grid",simplify=TRUE)
    TP_FN_grids <- rbind(TP_FN_grids,TP_FN,fill=TRUE)
  }
  if (grepl("FLAPS",grids[i])){
    FLAPS <- fread(grids[i], blank.lines.skip = T,stringsAsFactors = F,
                   header = T, fill = T)
    FLAPS$County <- strapply(grids[i],"Grid_Density/(.*)_FLAPS_Grid",simplify=TRUE)
    FLAPS_grids <- rbind(FLAPS_grids,FLAPS,fill=TRUE)
  }
}

AutoReview_grids_counties <- AutoReview_grids[which(AutoReview_grids$County!="AR_Cluster"),]
AutoReview_grids_cluster <- AutoReview_grids[which(AutoReview_grids$County=="AR_Cluster"),]
AutoReview_grids_list<-list(AutoReview_grids_counties,AutoReview_grids_cluster)

TP_FN_grids_counties <- TP_FN_grids[which(TP_FN_grids$County!="AR_Cluster"),]
TP_FN_grids_cluster <- TP_FN_grids[which(TP_FN_grids$County=="AR_Cluster"),]
TP_FN_grids_list<-list(TP_FN_grids_counties,TP_FN_grids_cluster)

FLAPS_grids_counties <- FLAPS_grids[which(FLAPS_grids$County!="AR_Cluster"),]
FLAPS_grids_cluster <- FLAPS_grids[which(FLAPS_grids$County=="AR_Cluster"),]
FLAPS_grids_list<-list(FLAPS_grids_counties,FLAPS_grids_cluster)

#      Eliminate unnecessary field (select County, Shape_Length, Shape_Area, Join_Count,
#      and OBJECTID); rename Join_Count variable to include model type (e.g. Count_AutoReview)
#      calculate the proportion of points within grid cell by dividing Join_Count by total
#      number of points for that model within the county.
for (i in 1:length(AutoReview_grids_list)) {
  AutoReview_grids_temp<-as.data.frame(AutoReview_grids_list[i])
  AutoReview_counts_temp <- AutoReview_grids_temp %>%
    mutate(Count_AutoReview=Join_Count) %>%
    select(OBJECTID,Shape_Length,Shape_Area,County,Count_AutoReview) %>%
    group_by(County,Shape_Length) %>%
    mutate(Prop_AutoReview=(Count_AutoReview/sum(Count_AutoReview)))
  if (grepl("AR_Cluster",unique(AutoReview_grids_temp$County))) {
    assign(paste("AutoReview_counts_cluster"),AutoReview_counts_temp)
  }
  else {
    assign(paste("AutoReview_counts_counties"),AutoReview_counts_temp)
  }
}
AutoReview_counts_temp<-NULL

for (i in 1:length(TP_FN_grids_list)) {
  TP_FN_grids_temp<-as.data.frame(TP_FN_grids_list[i])
  TP_FN_counts_temp <- TP_FN_grids_temp %>%
    mutate(Count_TP_FN=Join_Count) %>%
    select(OBJECTID,Shape_Length,Shape_Area,County,Count_TP_FN) %>%
    group_by(County,Shape_Length) %>%
    mutate(Prop_TP_FN=(Count_TP_FN/sum(Count_TP_FN)))
  if (grepl("AR_Cluster",unique(TP_FN_grids_temp$County))) {
    assign(paste("TP_FN_counts_cluster"),TP_FN_counts_temp)
  }
  else {
    assign(paste("TP_FN_counts_counties"),TP_FN_counts_temp)
  }
}
TP_FN_counts_temp<-NULL

for (i in 1:length(FLAPS_grids_list)) {
  FLAPS_grids_temp<-as.data.frame(FLAPS_grids_list[i])
  FLAPS_counts_temp <- FLAPS_grids_temp %>%
    mutate(Count_FLAPS=Join_Count) %>%
    select(OBJECTID,Shape_Length,Shape_Area,County,Count_FLAPS) %>%
    group_by(County,Shape_Length) %>%
    mutate(Prop_FLAPS=(Count_FLAPS/sum(Count_FLAPS)))
  if (grepl("AR_Cluster",unique(FLAPS_grids_temp$County))) {
    assign(paste("FLAPS_counts_cluster"),FLAPS_counts_temp)
  }
  else {
    assign(paste("FLAPS_counts_counties"),FLAPS_counts_temp)
  }
}
FLAPS_counts_temp<-NULL
#      Merge counts of three model types into one dataset
Grid_counts_counties <- merge(AutoReview_counts_counties,TP_FN_counts_counties,
                              by = c("OBJECTID","Shape_Length","Shape_Area","County"))
Grid_counts_counties <- merge(Grid_counts_counties,FLAPS_counts_counties,
                              by = c("OBJECTID","Shape_Length","Shape_Area","County"))

Grid_counts_cluster <- merge(AutoReview_counts_cluster,TP_FN_counts_cluster,
                              by = c("OBJECTID","Shape_Length","Shape_Area","County"))
Grid_counts_cluster <- merge(Grid_counts_cluster,FLAPS_counts_cluster,
                              by = c("OBJECTID","Shape_Length","Shape_Area","County"))

#      Convert shape length to km from meters and to width from perimeter; convert shape
#      area from m^2 to km^2
Grid_counts_counties <- Grid_counts_counties %>%
  mutate(Shape_Length=Shape_Length/4000) %>%
  mutate(Shape_Area=Shape_Area/1000000)

Grid_counts_cluster <- Grid_counts_cluster %>%
  mutate(Shape_Length=Shape_Length/4000) %>%
  mutate(Shape_Area=Shape_Area/1000000)

#      Calculate RMSE values from difference in counts and difference in proportions
#      between number of modelled (FLAPS or hybrid) points within a cell and number
#      of ground truth points within a cell
Grid_counts_counties <- Grid_counts_counties %>%
  group_by(Shape_Length) %>%
  add_count(Shape_Length) %>%
  mutate(Count_Diff_AutoReview=(Count_TP_FN-Count_AutoReview)) %>%
  mutate(Prop_Diff_AutoReview=(Prop_TP_FN-Prop_AutoReview)) %>%
  mutate(RMSE_Prop_AutoReview=sqrt(sum((Prop_Diff_AutoReview^2)/n))) %>%
  mutate(Count_Diff_FLAPS=(Count_TP_FN-Count_FLAPS)) %>%
  mutate(Prop_Diff_FLAPS=(Prop_TP_FN-Prop_FLAPS)) %>%
  mutate(RMSE_Prop_FLAPS=sqrt(sum((Prop_Diff_FLAPS^2)/n))) %>%
  mutate(RMSE_Count_AutoReview=sqrt(sum((Count_Diff_AutoReview^2)/n))) %>%
  mutate(RMSE_Count_FLAPS=sqrt(sum((Count_Diff_FLAPS^2)/n)))
  
Grid_counts_counties <- Grid_counts_counties[with(Grid_counts_counties,order(-Shape_Length,-OBJECTID)),]

Grid_counts_cluster <- Grid_counts_cluster %>%
  group_by(Shape_Length) %>%
  add_count(Shape_Length) %>%
  mutate(Count_Diff_AutoReview=(Count_TP_FN-Count_AutoReview)) %>%
  mutate(Prop_Diff_AutoReview=(Prop_TP_FN-Prop_AutoReview)) %>%
  mutate(RMSE_Prop_AutoReview=sqrt(sum((Prop_Diff_AutoReview^2)/n))) %>%
  mutate(Count_Diff_FLAPS=(Count_TP_FN-Count_FLAPS)) %>%
  mutate(Prop_Diff_FLAPS=(Prop_TP_FN-Prop_FLAPS)) %>%
  mutate(RMSE_Prop_FLAPS=sqrt(sum((Prop_Diff_FLAPS^2)/n))) %>%
  mutate(RMSE_Count_AutoReview=sqrt(sum((Count_Diff_AutoReview^2)/n))) %>%
  mutate(RMSE_Count_FLAPS=sqrt(sum((Count_Diff_FLAPS^2)/n)))

Grid_counts_cluster <- Grid_counts_cluster[with(Grid_counts_cluster,order(-Shape_Length,-OBJECTID)),]

#      Gather and organize data to produce line graphs for visualizing results of
#      "Grid Density" method
RMSE_plot_counties <- Grid_counts_counties[which(!duplicated(Grid_counts_counties$Shape_Length)),c(2,14,17,18,19)]
RMSE_prop_counties <- gather(RMSE_plot_counties[,c(1:3)], prop_model, RMSE_prop, RMSE_Prop_AutoReview:RMSE_Prop_FLAPS, factor_key=TRUE)
RMSE_prop_AutoReview_counties <- RMSE_prop_counties %>%
  filter(prop_model=="RMSE_Prop_AutoReview") %>%
  mutate(model="AutoReview for counties")
RMSE_prop_FLAPS_counties <- RMSE_prop_counties %>%
  filter(prop_model=="RMSE_Prop_FLAPS") %>%
  mutate(model="FLAPS for counties")
RMSE_prop_counties <- rbind(RMSE_prop_FLAPS_counties,RMSE_prop_AutoReview_counties)

RMSE_count_counties <- gather(RMSE_plot_counties[,c(1,4,5)], count_model, RMSE_count, RMSE_Count_AutoReview:RMSE_Count_FLAPS, factor_key=TRUE)
RMSE_count_AutoReview_counties <- RMSE_count_counties %>%
  filter(count_model=="RMSE_Count_AutoReview") %>%
  mutate(model="AutoReview for counties")
RMSE_count_FLAPS_counties <- RMSE_count_counties %>%
  filter(count_model=="RMSE_Count_FLAPS") %>%
  mutate(model="FLAPS for counties")
RMSE_count_counties <- rbind(RMSE_count_FLAPS_counties,RMSE_count_AutoReview_counties)

RMSE_plot_cluster <- Grid_counts_cluster[which(!duplicated(Grid_counts_cluster$Shape_Length)),c(2,14,17,18,19)]
RMSE_prop_cluster <- gather(RMSE_plot_cluster[,c(1:3)], prop_model, RMSE_prop, RMSE_Prop_AutoReview:RMSE_Prop_FLAPS, factor_key=TRUE)
RMSE_prop_AutoReview_cluster <- RMSE_prop_cluster %>%
  filter(prop_model=="RMSE_Prop_AutoReview") %>%
  mutate(model="AutoReview for cluster")
RMSE_prop_FLAPS_cluster <- RMSE_prop_cluster %>%
  filter(prop_model=="RMSE_Prop_FLAPS") %>%
  mutate(model="FLAPS for cluster")
RMSE_prop_cluster <- rbind(RMSE_prop_FLAPS_cluster,RMSE_prop_AutoReview_cluster)

RMSE_count_cluster <- gather(RMSE_plot_cluster[,c(1,4,5)], count_model, RMSE_count, RMSE_Count_AutoReview:RMSE_Count_FLAPS, factor_key=TRUE)
RMSE_count_AutoReview_cluster <- RMSE_count_cluster %>%
  filter(count_model=="RMSE_Count_AutoReview") %>%
  mutate(model="AutoReview for cluster")
RMSE_count_FLAPS_cluster <- RMSE_count_cluster %>%
  filter(count_model=="RMSE_Count_FLAPS") %>%
  mutate(model="FLAPS for cluster")
RMSE_count_cluster <- rbind(RMSE_count_FLAPS_cluster,RMSE_count_AutoReview_cluster)

RMSE_plot_counties <- merge(RMSE_prop_counties,RMSE_count_counties,by=c("Shape_Length","model"))
RMSE_plot_cluster <- merge(RMSE_prop_cluster,RMSE_count_cluster,by=c("Shape_Length","model"))
RMSE_plot <- rbind(RMSE_plot_counties,RMSE_plot_cluster)

RMSE_plot <- RMSE_plot[with(RMSE_plot,order(Shape_Length)),]

#      Create line graph to visualize results of "Grid Counts" method
par(mar=c(6, 4.5, 4, 5.5) + 0.1)

RMSE_rows_prop_AutoReview_counties <- rownames(RMSE_plot[RMSE_plot$prop_model=="RMSE_Prop_AutoReview" & 
                                                           RMSE_plot$model == "AutoReview for counties",])
RMSE_rows_prop_FLAPS_counties <- rownames(RMSE_plot[RMSE_plot$prop_model=="RMSE_Prop_FLAPS" &
                                                      RMSE_plot$model == "FLAPS for counties",])
plot(RMSE_plot[c(RMSE_rows_prop_AutoReview_counties),"Shape_Length"],
     RMSE_plot[c(RMSE_rows_prop_AutoReview_counties),"RMSE_prop"],
     pch=22, cex=0.8,lty=1,axes=FALSE, ylim=c(0,0.15),
     xlab="Grid Cell Size", ylab="", type="b",col="#fdb863",
     main="RMSE for diff. in farm distribution between FLAPS or hybrid and truth")
axis(2, ylim=c(0,0.15),col="#e66101",col.axis="#e66101",las=1)  ## las=1 makes horizontal labels
axis(1, xlim=c(-2,62),col="black",las=2)  ## las=1 makes horizontal labels
lines(RMSE_plot[c(RMSE_rows_prop_FLAPS_counties),"Shape_Length"],
      RMSE_plot[c(RMSE_rows_prop_FLAPS_counties),"RMSE_prop"],
      type="o", pch=22, cex=0.8, lty=2, col="#e66101")
RMSE_rows_prop_AutoReview_cluster <- rownames(RMSE_plot[RMSE_plot$prop_model=="RMSE_Prop_AutoReview" & 
                                                          RMSE_plot$model == "AutoReview for cluster",])
RMSE_rows_prop_FLAPS_cluster <- rownames(RMSE_plot[RMSE_plot$prop_model=="RMSE_Prop_FLAPS" &
                                                     RMSE_plot$model == "FLAPS for cluster",])
lines(RMSE_plot[c(RMSE_rows_prop_AutoReview_cluster),"Shape_Length"],
      RMSE_plot[c(RMSE_rows_prop_AutoReview_cluster),"RMSE_prop"],
      type="b", pch=16, cex=0.8, lty=1, col="#fdb863")
lines(RMSE_plot[c(RMSE_rows_prop_FLAPS_cluster),"Shape_Length"],
      RMSE_plot[c(RMSE_rows_prop_FLAPS_cluster),"RMSE_prop"],
      type="o", pch=16, cex=0.8, lty=2, col="#e66101")
mtext("RMSE by difference in proportion of counts",side=2,line=3,cex=0.8)

par(new=TRUE)

RMSE_rows_count_AutoReview_counties <- rownames(RMSE_plot[RMSE_plot$count_model=="RMSE_Count_AutoReview" &
                                                            RMSE_plot$model == "AutoReview for counties",])
RMSE_rows_count_FLAPS_counties <- rownames(RMSE_plot[RMSE_plot$count_model=="RMSE_Count_FLAPS" &
                                                       RMSE_plot$model=="FLAPS for counties",])
plot(RMSE_plot[c(RMSE_rows_count_AutoReview_counties),"Shape_Length"], 
     RMSE_plot[c(RMSE_rows_count_AutoReview_counties),"RMSE_count"], pch=22, cex=0.8,xlab="", ylab="", 
     ylim=c(0,30), axes=FALSE, type="b", col="#b2abd2",lty=1)
lines(RMSE_plot[c(RMSE_rows_count_FLAPS_counties),"Shape_Length"],
      RMSE_plot[c(RMSE_rows_count_FLAPS_counties),"RMSE_count"],
      type="o", pch=22, cex=0.8,lty=2, col="#5e3c99")
RMSE_rows_count_AutoReview_cluster <- rownames(RMSE_plot[RMSE_plot$count_model=="RMSE_Count_AutoReview" &
                                                           RMSE_plot$model == "AutoReview for cluster",])
RMSE_rows_count_FLAPS_cluster <- rownames(RMSE_plot[RMSE_plot$count_model=="RMSE_Count_FLAPS" &
                                                      RMSE_plot$model=="FLAPS for cluster",])
lines(RMSE_plot[c(RMSE_rows_count_AutoReview_cluster),"Shape_Length"],
      RMSE_plot[c(RMSE_rows_count_AutoReview_cluster),"RMSE_count"],
      type="b", pch=16, cex=0.8,lty=1, col="#b2abd2")
lines(RMSE_plot[c(RMSE_rows_count_FLAPS_cluster),"Shape_Length"],
      RMSE_plot[c(RMSE_rows_count_FLAPS_cluster),"RMSE_count"],
      type="o", pch=16, cex=0.8,lty=2, col="#5e3c99")
mtext("RMSE by difference in number of counts",side=4,line=2,cex=0.8) 
axis(4, ylim=c(0,30), col="#5e3c99",col.axis="#5e3c99",las=1)

legend(x=0,y=33,title="Model",legend=c("Hybrid","FLAPS"),
       text.col="black",col="black",lty=c(1,2),pch=NULL,bty="n")
legend(x=18,y=33,title="Geography",legend=c("cluster","counties"),
       text.col="black",col="black",lty=NULL,pch=c(16,22),bty="n")

########################################
############ELLIPSE OVERLAP#############
########################################

#ellipse_home <- "C:/Users/GKuiper/Desktop/Ellipses"  ## DS: original
ellipse_home <- "O:/AI Modeling Coop Agreement 2017/Grace Cap Stone Validation/Validation_Results/Ellipses"  ## DS: altered

ellipses <- list.files(path=ellipse_home, full.names = T, recursive = F)
x <- c("AR_Cluster", "AR_Logan", "AR_Yell","AR_Scott")
ellipses <- ellipses[grepl(paste(x, collapse = "|"), ellipses)]

TP_FN_ellipse <- data.frame()
AutoReview_ellipse <- data.frame()
FLAPS_ellipse <- data.frame()
AutoReview_intersection <- data.frame()
FLAPS_intersection <- data.frame()

#      Import Ellipse Overlap results into separate data.frames based on data/model
#      type: hybrid, FLAPS, ground truth and ellipse areas vs. intersection areas
for (i in 1:length(ellipses)) {
  if (grepl("AutoReview_Ellipse",ellipses[i])){
    AutoReview <- fread(ellipses[i],blank.lines.skip = T,stringsAsFactors = F,
                        header = T, fill = T)
    AutoReview$County <- strapply(ellipses[i],"Ellipses/(.*)_AutoReview_Ellipse",simplify=TRUE)
    AutoReview$Ellipse_Size <- strapply(ellipses[i],"_AutoReview_Ellipse_(.*)",simplify=TRUE)
    AutoReview_ellipse <- rbind(AutoReview_ellipse,AutoReview,fill=TRUE)
  }
  if (grepl("TP_FN_Ellipse",ellipses[i])){
    TP_FN <- fread(ellipses[i],blank.lines.skip = T,stringsAsFactors = F,
                   header = T, fill = T)
    TP_FN$County <- strapply(ellipses[i],"Ellipses/(.*)_TP_FN_Ellipse",simplify=TRUE)
    TP_FN$Ellipse_Size <- strapply(ellipses[i],"_TP_FN_Ellipse_(.*)",simplify=TRUE)
    TP_FN_ellipse <- rbind(TP_FN_ellipse,TP_FN,fill=TRUE)
  }
  if (grepl("FLAPS_Ellipse",ellipses[i])){
    FLAPS <- fread(ellipses[i],blank.lines.skip = T,stringsAsFactors = F,
                   header = T, fill = T)
    FLAPS$County <- strapply(ellipses[i],"Ellipses/(.*)_FLAPS_Ellipse",simplify=TRUE)
    FLAPS$Ellipse_Size <- strapply(ellipses[i],"_FLAPS_Ellipse_(.*)",simplify=TRUE)
    FLAPS_ellipse <- rbind(FLAPS_ellipse,FLAPS,fill=TRUE)
  }
  if (grepl("AutoReview_Intersection",ellipses[i])){
    AutoReview <- fread(ellipses[i],blank.lines.skip = T,stringsAsFactors = F,
                   header = T, fill = T)
    AutoReview$County <- strapply(ellipses[i],"Ellipses/(.*)_AutoReview_Intersection",simplify=TRUE)
    AutoReview$Ellipse_Size <- strapply(ellipses[i],"_AutoReview_Intersection_(.*)",simplify=TRUE)
    AutoReview_intersection <- rbind(AutoReview_intersection,AutoReview,fill=TRUE)
  }
  if (grepl("FLAPS_Intersection",ellipses[i])){
    FLAPS <- fread(ellipses[i],blank.lines.skip = T,stringsAsFactors = F,
                   header = T, fill = T)
    FLAPS$County <- strapply(ellipses[i],"Ellipses/(.*)_FLAPS_Intersection",simplify=TRUE)
    FLAPS$Ellipse_Size <- strapply(ellipses[i],"_FLAPS_Intersection_(.*)",simplify=TRUE)
    FLAPS_intersection <- rbind(FLAPS_intersection,FLAPS,fill=TRUE)
  }
}

TP_FN_ellipse <- select(TP_FN_ellipse,County,Ellipse_Size,Shape_Area)
AutoReview_ellipse <- select(AutoReview_ellipse,County,Ellipse_Size,Shape_Area)
FLAPS_ellipse <- select(FLAPS_ellipse,County,Ellipse_Size,Shape_Area)
AutoReview_intersection <- select(AutoReview_intersection,County,Ellipse_Size,Shape_Area)
FLAPS_intersection <- select(FLAPS_intersection,County,Ellipse_Size,Shape_Area)

TP_FN_ellipse[is.na(TP_FN_ellipse)] = 0
AutoReview_ellipse[is.na(AutoReview_ellipse)] = 0
FLAPS_ellipse[is.na(FLAPS_ellipse)] = 0
AutoReview_intersection[is.na(AutoReview_intersection)] = 0
FLAPS_intersection[is.na(FLAPS_intersection)] = 0

TP_FN_ellipse <- aggregate(TP_FN_ellipse[,"Shape_Area"],
                                    by=TP_FN_ellipse[,c("County","Ellipse_Size")],
                                    FUN=sum)
TP_FN_ellipse$TP_FN_ellipse<-TP_FN_ellipse$Shape_Area
TP_FN_ellipse$Shape_Area<- NULL

FLAPS_ellipse <- aggregate(FLAPS_ellipse[,"Shape_Area"],
                                    by=FLAPS_ellipse[,c("County","Ellipse_Size")],
                                    FUN=sum)
FLAPS_ellipse$FLAPS_ellipse<-FLAPS_ellipse$Shape_Area
FLAPS_ellipse$Shape_Area<-NULL

AutoReview_ellipse <- aggregate(AutoReview_ellipse[,"Shape_Area"],
                                         by=AutoReview_ellipse[,c("County","Ellipse_Size")],
                                         FUN=sum)
AutoReview_ellipse$AutoReview_ellipse<-AutoReview_ellipse$Shape_Area
AutoReview_ellipse$Shape_Area<-NULL

FLAPS_intersection <- aggregate(FLAPS_intersection[,"Shape_Area"],
                                         by=FLAPS_intersection[,c("County","Ellipse_Size")],
                                         FUN=sum)
FLAPS_intersection$FLAPS_intersection<-FLAPS_intersection$Shape_Area
FLAPS_intersection$Shape_Area<-NULL

AutoReview_intersection <- aggregate(AutoReview_intersection[,"Shape_Area"],
                                              by=AutoReview_intersection[,c("County","Ellipse_Size")],
                                              FUN=sum)
AutoReview_intersection$AutoReview_intersection<-AutoReview_intersection$Shape_Area
AutoReview_intersection$Shape_Area<-NULL

Ellipse_intersection_areas_AutoReview <- merge(AutoReview_intersection, AutoReview_ellipse, by=c("County","Ellipse_Size"),all=TRUE)
Ellipse_intersection_areas_AutoReview <- merge(Ellipse_intersection_areas_AutoReview, TP_FN_ellipse, by=c("County","Ellipse_Size"),all=TRUE)
Ellipse_intersection_areas_FLAPS <- merge(FLAPS_intersection, FLAPS_ellipse, by=c("County","Ellipse_Size"),all=TRUE)
Ellipse_intersection_areas_FLAPS <- merge(Ellipse_intersection_areas_FLAPS, TP_FN_ellipse, by=c("County","Ellipse_Size"),all=TRUE)
Ellipse_intersection_areas_AutoReview[is.na(Ellipse_intersection_areas_AutoReview)] = 0
Ellipse_intersection_areas_FLAPS[is.na(Ellipse_intersection_areas_FLAPS)] = 0

for (i in 1:nrow(Ellipse_intersection_areas_AutoReview)) {
  if (grepl(".csv",Ellipse_intersection_areas_AutoReview[i,"Ellipse_Size"])) {
    Ellipse_intersection_areas_AutoReview[i,"Ellipse_Size"]=sub(".csv.*","",Ellipse_intersection_areas_AutoReview[i,"Ellipse_Size"])
  }
}
for (i in 1:nrow(Ellipse_intersection_areas_FLAPS)) {
  if (grepl(".csv",Ellipse_intersection_areas_FLAPS[i,"Ellipse_Size"])) {
    Ellipse_intersection_areas_FLAPS[i,"Ellipse_Size"]=sub(".csv.*","",Ellipse_intersection_areas_FLAPS[i,"Ellipse_Size"])
  }
}

Ellipse_intersection_areas_AutoReview <- Ellipse_intersection_areas_AutoReview %>%
  mutate(not_overlapped_TP_FN=TP_FN_ellipse-AutoReview_intersection) %>%
  mutate(not_overlapped_AutoReview=AutoReview_ellipse-AutoReview_intersection) %>%
  select(not_overlapped_AutoReview,not_overlapped_TP_FN,AutoReview_intersection,County,Ellipse_Size)
Ellipse_intersection_areas_FLAPS <- Ellipse_intersection_areas_FLAPS %>%
  mutate(not_overlapped_TP_FN=TP_FN_ellipse-FLAPS_intersection) %>%
  mutate(not_overlapped_FLAPS=FLAPS_ellipse-FLAPS_intersection) %>%
  select(not_overlapped_FLAPS,not_overlapped_TP_FN,FLAPS_intersection,County,Ellipse_Size)

AutoReview_areas_10000<-Ellipse_intersection_areas_AutoReview %>%
  filter(Ellipse_Size=="10000") %>%
  select(not_overlapped_AutoReview,not_overlapped_TP_FN,AutoReview_intersection,County)
rownames(AutoReview_areas_10000)<-AutoReview_areas_10000$County
AutoReview_areas_10000$County<-NULL

AutoReview_areas_20000<-Ellipse_intersection_areas_AutoReview %>%
  filter(Ellipse_Size=="20000")
AutoReview_areas_3000<-Ellipse_intersection_areas_AutoReview %>%
  filter(Ellipse_Size=="3000")

FLAPS_areas_10000<-Ellipse_intersection_areas_FLAPS %>%
  filter(Ellipse_Size=="10000")
FLAPS_areas_20000<-Ellipse_intersection_areas_FLAPS %>%
  filter(Ellipse_Size=="20000")
FLAPS_areas_3000<-Ellipse_intersection_areas_FLAPS %>%
  filter(Ellipse_Size=="3000")



########################################
############BUFFER CAPTURE##############
########################################

#buffers_home <- "C:/Users/GKuiper/Desktop/Buffer_Capture"  ## DS: original
buffers_home <- "O:/AI Modeling Coop Agreement 2017/Grace Cap Stone Validation/Validation_Results/Buffer_Capture" ## DS - altered

buffers <- list.files(path=buffers_home, full.names = T, recursive = F)
x <- c("AR_Cluster", "AR_Logan", "AR_Yell","AR_Scott")
buffers <- buffers[grepl(paste(x, collapse = "|"), buffers)]

AutoReview_capture <- data.frame()
FLAPS_capture <- data.frame()

#      Import Buffer Capture results into separate data.frames based on data/model
#      type: hybrid or FLAPS
for (i in 1:length(buffers)) {
  if (grepl("AutoReview_Capture",buffers[i])){
    AutoReview <- fread(buffers[i],blank.lines.skip = T,stringsAsFactors = F,
                        header = T, fill = T)
    AutoReview$County <- strapply(buffers[i],"Buffer_Capture/(.*)_AutoReview_Capture",simplify=TRUE)
    AutoReview_capture <- rbind(AutoReview_capture,AutoReview,fill=TRUE)
  }
  if (grepl("FLAPS_Capture",buffers[i])){
    FLAPS <- fread(buffers[i],blank.lines.skip = T,stringsAsFactors = F,
                   header = T, fill = T)
    FLAPS$County <- strapply(buffers[i],"Buffer_Capture/(.*)_FLAPS_Capture",simplify=TRUE)
    FLAPS_capture <- rbind(FLAPS_capture,FLAPS,fill=TRUE)
  }
}

#      Eliminate unnecessary fields (select County, BUFF_DISTANCE [buffer distance], Join_Count,
#      and OBJECTID); and OBJECTID); rename Join_Count variable to include model type (e.g. 
#      Count_AutoReview); merge Buffer Capture counts from hybrid and FLAPS models into single
#      data.frame (capture_plot)
AutoReview_capture <- AutoReview_capture %>%
  mutate(Count_AutoReview=Join_Count) %>%
  select(-3)
FLAPS_capture <- FLAPS_capture %>%
  mutate(Count_FLAPS=Join_Count) %>%
  select(-3)

AutoReview_counts <- AutoReview_capture %>% select(County,BUFF_DIST,Count_AutoReview,OBJECTID)
FLAPS_counts <- FLAPS_capture %>% select(County,BUFF_DIST,Count_FLAPS,OBJECTID)
capture_plot_count <- merge(AutoReview_counts,FLAPS_counts,by=c("County","BUFF_DIST","OBJECTID"))

#      Create variables for calculating proportion of ground truth buffers that capture
#      hybrid or FLAPS points
capture_plot_AutoReview_prop_yes <- capture_plot_count %>%
  filter(Count_AutoReview>0) %>%
  mutate(Prop_AutoReview=1) %>%
  select(County,BUFF_DIST,OBJECTID,Prop_AutoReview)
capture_plot_AutoReview_prop_no <- capture_plot_count %>%
  filter(Count_AutoReview==0) %>%
  mutate(Prop_AutoReview=0) %>%
  select(County,BUFF_DIST,OBJECTID,Prop_AutoReview)
capture_plot_FLAPS_prop_yes <- capture_plot_count %>%
  filter(Count_FLAPS>0) %>%
  mutate(Prop_FLAPS=1) %>%
  select(County,BUFF_DIST,OBJECTID,Prop_FLAPS)
capture_plot_FLAPS_prop_no <- capture_plot_count %>%
  filter(Count_FLAPS==0) %>%
  mutate(Prop_FLAPS=0) %>%
  select(County,BUFF_DIST,OBJECTID,Prop_FLAPS)

capture_plot_AutoReview_prop <- rbind(capture_plot_AutoReview_prop_no,capture_plot_AutoReview_prop_yes)
capture_plot_FLAPS_prop <- rbind(capture_plot_FLAPS_prop_no,capture_plot_FLAPS_prop_yes)
capture_plot_prop <- merge(capture_plot_AutoReview_prop,capture_plot_FLAPS_prop,by=c("County",
                           "BUFF_DIST","OBJECTID"))
capture_plot <- merge(capture_plot_count,capture_plot_prop,by=c("County","BUFF_DIST","OBJECTID"))
capture_plot_counties <- capture_plot[which(capture_plot$County!="AR_Cluster"),]
capture_plot_cluster <- capture_plot[which(capture_plot$County=="AR_Cluster"),]

#      Sum count and proportion variables by buffer distance.
capture_plot_final_counties <- aggregate(x=capture_plot_counties[,c("Count_AutoReview","Count_FLAPS","Prop_AutoReview","Prop_FLAPS")],
                                by=list(capture_plot_counties[,"BUFF_DIST"]),
                                FUN=sum)
capture_plot_final_cluster <- aggregate(x=capture_plot_cluster[,c("Count_AutoReview","Count_FLAPS","Prop_AutoReview","Prop_FLAPS")],
                                        by=list(capture_plot_cluster[,"BUFF_DIST"]),
                                        FUN=sum)
capture_plot_final_counties <- capture_plot_final_counties %>%
  mutate(BUFF_DIST=Group.1) %>%
  select(-1)
capture_plot_final_cluster <- capture_plot_final_cluster %>%
  mutate(BUFF_DIST=Group.1) %>%
  select(-1)

capture_plot_final_counties <- capture_plot_final_counties %>%
  group_by(BUFF_DIST) %>%
  mutate(Prop_FLAPS=(Prop_FLAPS/(nrow(capture_plot)/5))*100) %>%
  mutate(Prop_AutoReview=(Prop_AutoReview/(nrow(capture_plot)/5))*100)
capture_plot_final_cluster <- capture_plot_final_cluster %>%
  group_by(BUFF_DIST) %>%
  mutate(Prop_FLAPS=(Prop_FLAPS/(nrow(capture_plot)/5))*100) %>%
  mutate(Prop_AutoReview=(Prop_AutoReview/(nrow(capture_plot)/5))*100)
#      Convert tables from wide to long.
capture_plot_count_counties <- gather(capture_plot_final_counties[,c(1,2,5)], count_measure, count_value, Count_AutoReview:Count_FLAPS, factor_key=TRUE)
capture_plot_count_cluster <- gather(capture_plot_final_cluster[,c(1,2,5)], count_measure, count_value, Count_AutoReview:Count_FLAPS, factor_key=TRUE)

capture_plot_prop_counties <- gather(capture_plot_final_counties[,c(3,4,5)], prop_measure, prop_value, Prop_AutoReview:Prop_FLAPS, factor_key=TRUE)
capture_plot_prop_cluster <- gather(capture_plot_final_cluster[,c(3,4,5)],prop_measure, prop_value, Prop_AutoReview:Prop_FLAPS, factor_key=TRUE)
capture_plot_final <- merge(capture_plot_prop,capture_plot_count,by="BUFF_DIST")
