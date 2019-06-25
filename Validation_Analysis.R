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
grid_density <- function(counties='all'){
    grid_density_home <- "O:/AI Modeling Coop Agreement 2017/Grace Cap Stone Validation/Validation_Results/Grid_Density"
    
    grids <- list.files(path=grid_density_home, full.names = T, recursive = F)
    ####for cluster analysis:
    #grids <- grids[grepl(c("AR_Cluster","AR_Yell","AR_Logan","AR_Scott"),grids)]
    ####for regular validation analysis:
    grids <- grids[!grepl(c("Cluster"),grids)]
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

    #      Eliminate unnecessary field (select County, Shape_Length, Shape_Area, Join_Count,
    #      and OBJECTID); rename Join_Count variable to include model type (e.g. Count_AutoReview)
    #      calculate the proportion of points within grid cell by dividing Join_Count by total
    #      number of points for that model within the county.
    AutoReview_counts <- AutoReview_grids %>%
      mutate(Count_AutoReview=Join_Count) %>%
      select(OBJECTID,Shape_Length,Shape_Area,County,Count_AutoReview) %>%
      group_by(County,Shape_Length) %>%
      mutate(Prop_AutoReview=(Count_AutoReview/sum(Count_AutoReview)))
    
    TP_FN_counts <- TP_FN_grids %>%
      mutate(Count_TP_FN=Join_Count) %>% ## DS: For some reason, "Count_TP_FN" is causing problems.
      #select(1,19:21,24) %>%
      select(OBJECTID,Shape_Length,Shape_Area,County,Count_TP_FN) %>% ## The problem was that this select
      #line previously selected by column number, versus by column name. Some of the new counties must have
      #more or different variables, because there are more columns than there used to be in the TP_FN_grids.
      #as a results, column 24 used to be the new "Count_TP_FN" variable created in line 74; with the new
      #counties, column 24 is actually a variable called "ICOUNT_1". So, line 75 was selectin "ICOUNT_1"
      #instead of "Count_TP_FN", and then the results dataframe that was piped into line 84 didn't have a
      #Count_TP_FN variable with which to calculate Prop_TP_FN. I've solved the problem by selecting by
      #variable name in line 76, instead of column number. Let me know if you have any questions. ~Grace
      group_by(County,Shape_Length) %>%
      mutate(Prop_TP_FN=(Count_TP_FN/sum(Count_TP_FN)))
      
    FLAPS_counts <- FLAPS_grids %>%
      mutate(Count_FLAPS=Join_Count) %>%
      select(OBJECTID,Shape_Length,Shape_Area,County,Count_FLAPS) %>%
      group_by(County,Shape_Length) %>%
      mutate(Prop_FLAPS=(Count_FLAPS/sum(Count_FLAPS)))
    
    #      Merge counts of three model types into one dataset
    Grid_counts <- merge(AutoReview_counts,TP_FN_counts,by = c("OBJECTID","Shape_Length","Shape_Area","County"))
    Grid_counts <- merge(Grid_counts,FLAPS_counts, by = c("OBJECTID","Shape_Length","Shape_Area","County"))
    
    #      Convert shape length to km from meters and to width from perimeter; convert shape
    #      area from m^2 to km^2
    Grid_counts <- Grid_counts %>%
      mutate(Shape_Length=Shape_Length/4000) %>%
      mutate(Shape_Area=Shape_Area/1000000)
    
    #      Calculate RMSE values from difference in counts and difference in proportions
    #      between number of modelled (FLAPS or hybrid) points within a cell and number
    #      of ground truth points within a cell
    Grid_counts <- Grid_counts %>%
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
      
    Grid_counts <- Grid_counts[with(Grid_counts,order(-Shape_Length,-OBJECTID)),]
    
    #      Gather and organize data to produce line graphs for visualizing results of
    #      "Grid Density" method
    RMSE_plot <- Grid_counts[which(!duplicated(Grid_counts$Shape_Length)),c(2,14,17,18,19)]
    RMSE_prop <- gather(RMSE_plot[,c(1:3)], prop_model, RMSE_prop, RMSE_Prop_AutoReview:RMSE_Prop_FLAPS, factor_key=TRUE)
    RMSE_prop_AutoReview <- RMSE_prop %>%
      filter(prop_model=="RMSE_Prop_AutoReview") %>%
      mutate(model="AutoReview")
    RMSE_prop_FLAPS <- RMSE_prop %>%
      filter(prop_model=="RMSE_Prop_FLAPS") %>%
      mutate(model="FLAPS")
    RMSE_prop <- rbind(RMSE_prop_FLAPS,RMSE_prop_AutoReview)
    
    RMSE_count <- gather(RMSE_plot[,c(1,4,5)], count_model, RMSE_count, RMSE_Count_AutoReview:RMSE_Count_FLAPS, factor_key=TRUE)
    RMSE_count_AutoReview <- RMSE_count %>%
      filter(count_model=="RMSE_Count_AutoReview") %>%
      mutate(model="AutoReview")
    RMSE_count_FLAPS <- RMSE_count %>%
      filter(count_model=="RMSE_Count_FLAPS") %>%
      mutate(model="FLAPS")
    RMSE_count <- rbind(RMSE_count_FLAPS,RMSE_count_AutoReview)
    
    RMSE_plot <- merge(RMSE_prop,RMSE_count,by=c("Shape_Length","model"))
    RMSE_plot <- RMSE_plot[with(RMSE_plot,order(Shape_Length)),]
    
    #      Create line graph to visualize results of "Grid Counts" method
    par(mar=c(6, 4.5, 4, 5.5) + 0.1)
    
    RMSE_rows_prop_AutoReview <- rownames(RMSE_plot[RMSE_plot$prop_model=="RMSE_Prop_AutoReview",])
    RMSE_rows_prop_FLAPS <- rownames(RMSE_plot[RMSE_plot$prop_model=="RMSE_Prop_FLAPS",])
    plot(RMSE_plot[c(RMSE_rows_prop_AutoReview),"Shape_Length"],
         RMSE_plot[c(RMSE_rows_prop_AutoReview),"RMSE_prop"],
         pch=16, cex=0.8,axes=FALSE, ylim=c(0,0.2),
         xlab="Grid Cell Size", ylab="", type="b",col="#fdb863",
         main="RMSE for diff. in farm distribution between FLAPS or hybrid and truth")
    axis(2, ylim=c(0,0.2),col="#e66101",col.axis="#e66101",las=1)  ## las=1 makes horizontal labels
    axis(1, xlim=c(-2,62),col="black",las=2)  ## las=1 makes horizontal labels
    lines(RMSE_plot[c(RMSE_rows_prop_FLAPS),"Shape_Length"],
          RMSE_plot[c(RMSE_rows_prop_FLAPS),"RMSE_prop"],
          type="o", pch=22, cex=0.8, lty=2, col="#e66101")
    mtext("RMSE by difference in proportion of counts",side=2,line=3,cex=0.8)
    
    par(new=TRUE)
    
    RMSE_rows_count_AutoReview <- rownames(RMSE_plot[RMSE_plot$count_model=="RMSE_Count_AutoReview",])
    RMSE_rows_count_FLAPS <- rownames(RMSE_plot[RMSE_plot$count_model=="RMSE_Count_FLAPS",])
    plot(RMSE_plot[c(RMSE_rows_count_AutoReview),"Shape_Length"], 
         RMSE_plot[c(RMSE_rows_count_AutoReview),"RMSE_count"], pch=15, cex=0.8,xlab="", ylab="", 
         ylim=c(0,40), axes=FALSE, type="b", col="#b2abd2")
    lines(RMSE_plot[c(RMSE_rows_count_FLAPS),"Shape_Length"],
          RMSE_plot[c(RMSE_rows_count_FLAPS),"RMSE_count"],
          type="o", pch=22, cex=0.8,lty=2, col="#5e3c99")
    
    mtext("RMSE by difference in number of counts",side=4,line=2,cex=0.8) 
    axis(4, ylim=c(0,40), col="#5e3c99",col.axis="#5e3c99",las=1)
    
    legend(x=1.5,y=39.5,title="Model compared to truth",legend=c("Hybrid","FLAPS"),
           text.col="black",col="black",lty=c(1,2),pch=c(15,22),bty="n")
}

########################################
############ELLIPSE OVERLAP#############
########################################
ellipse_overlap <-  function(counties="all"){
    ellipse_home <- "O:/AI Modeling Coop Agreement 2017/Grace Cap Stone Validation/Validation_Results/Ellipses"  ## DS: altered
    
    ellipses <- list.files(path=ellipse_home, full.names = T, recursive = F)
    ####for cluster analysis:
    #ellipses <- ellipses[grepl("Cluster",ellipses)]
    ####for regular validation analysis:
    ellipses <- ellipses[!grepl("Cluster",ellipses)]
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
    
    
    #      Eliminate unnecessary fields (select County, Ellipse_Size, and Shape_Area; rename 
    #      Shape_Area variable to include model type and ellipse vs. intersection (e.g.
    #      TP_FN_ellipse_area); calculate total areas of ellipses or intesections for each
    #      county by model type (FLAPS or hybrid) or ground truth
    TP_FN_ellipse <- select(TP_FN_ellipse,County,Ellipse_Size,Shape_Area)
    AutoReview_ellipse <- select(AutoReview_ellipse,County,Ellipse_Size,Shape_Area)
    FLAPS_ellipse <- select(FLAPS_ellipse,County,Ellipse_Size,Shape_Area)
    AutoReview_intersection <- select(AutoReview_intersection,County,Ellipse_Size,Shape_Area)
    FLAPS_intersection <- select(FLAPS_intersection,County,Ellipse_Size,Shape_Area)
    
    #      Calculate total ellipse intersection areas per county at each ellipse size
    #      by summing by County and Ellipse_Size.
    TP_FN_ellipse <- aggregate(TP_FN_ellipse[,"Shape_Area"],
                                    by=TP_FN_ellipse[,c("County","Ellipse_Size")],
                                    FUN=sum)
    FLAPS_ellipse <- aggregate(FLAPS_ellipse[,"Shape_Area"],
                               by=FLAPS_ellipse[,c("County","Ellipse_Size")],
                               FUN=sum)
    AutoReview_ellipse <- aggregate(AutoReview_ellipse[,"Shape_Area"],
                               by=AutoReview_ellipse[,c("County","Ellipse_Size")],
                               FUN=sum)
    FLAPS_intersection <- aggregate(FLAPS_intersection[,"Shape_Area"],
                               by=FLAPS_intersection[,c("County","Ellipse_Size")],
                               FUN=sum)
    AutoReview_intersection <- aggregate(AutoReview_intersection[,"Shape_Area"],
                               by=AutoReview_intersection[,c("County","Ellipse_Size")],
                               FUN=sum)
    
    TP_FN_ellipse <- TP_FN_ellipse %>%
      mutate(TP_FN_ellipse_area=Shape_Area) %>%
      select(-3)
    AutoReview_ellipse <- AutoReview_ellipse %>%
      mutate(AutoReview_ellipse_area=Shape_Area) %>%
      select(-3)
    FLAPS_ellipse <- FLAPS_ellipse %>%
      mutate(FLAPS_ellipse_area=Shape_Area) %>%
      select(-3)
    AutoReview_intersection <- AutoReview_intersection %>%
      mutate(AutoReview_intersection_area=Shape_Area) %>%
      select(-3)
    FLAPS_intersection <- FLAPS_intersection %>%
      mutate(FLAPS_intersection_area=Shape_Area) %>%
      select(-3)
    
    #      Merge all data.frames into a single Ellipse_areas data.frame
    Ellipse_areas <- merge(TP_FN_ellipse,AutoReview_ellipse,by = c("County","Ellipse_Size"),all=TRUE)
    Ellipse_areas <- merge(Ellipse_areas,FLAPS_ellipse,by = c("County","Ellipse_Size"),all=TRUE)
    Ellipse_areas <- merge(Ellipse_areas,AutoReview_intersection,by = c("County","Ellipse_Size"),all=TRUE)
    Ellipse_areas <- merge(Ellipse_areas,FLAPS_intersection,by = c("County","Ellipse_Size"),all=TRUE)
    
    #      Calculate the proportion metric for Ellipse Overlap method. This metric is the 
    #      product of the proportion of the hybrid intersection areas out of the total 
    #      hybrid ellipse areas and the proportion of the hybrid intersection areas out
    #      of the total hybrid ellipse areas.
    Ellipse_areas_differences <- Ellipse_areas %>%
      group_by(Ellipse_Size) %>%
      mutate(intersection_FLAPS_prop = (FLAPS_intersection_area/TP_FN_ellipse_area) * (FLAPS_intersection_area/FLAPS_ellipse_area)) %>%
      mutate(intersection_AutoReview_prop = (AutoReview_intersection_area/TP_FN_ellipse_area) * (AutoReview_intersection_area/AutoReview_ellipse_area))
    
    #      Gather and organize data to produce line graphs for visualizing results of
    #      "Ellipse Overlap" method
    Ellipse_plots_data <- gather(Ellipse_areas_differences[,c(1,2,8,9)],model, proportion_overlap, intersection_FLAPS_prop:intersection_AutoReview_prop, factor_key=TRUE)
    
    Ellipse_plots_data_10000 <- Ellipse_plots_data %>%
      filter(Ellipse_Size=="10000") %>%
      mutate(Ellipse_Size_="10000 meters")
    Ellipse_plots_data_20000 <- Ellipse_plots_data %>%
      filter(Ellipse_Size=="20000") %>%
      mutate(Ellipse_Size_="20000 meters")
    Ellipse_plots_data_3000 <- Ellipse_plots_data %>%
      filter(Ellipse_Size=="3000") %>%
      mutate(Ellipse_Size_=" 3000 meters")
    
    Ellipse_plots_data <- rbind(Ellipse_plots_data_3000,Ellipse_plots_data_10000)
    Ellipse_plots_data <- rbind(Ellipse_plots_data,Ellipse_plots_data_20000)
    
    Ellipse_plots_data_FLAPS <- Ellipse_plots_data %>%
      filter(model=="intersection_FLAPS_prop") %>%
      mutate(model_="FLAPS")
    Ellipse_plots_data_AutoReview <- Ellipse_plots_data %>%
      filter(model=="intersection_AutoReview_prop") %>%
      mutate(model_="Hybrid")
    
    Ellipse_plots_data <- rbind(Ellipse_plots_data_FLAPS,Ellipse_plots_data_AutoReview)
    
    #      Create line graph to visualize results of "Ellipse Overlap" method
    Ellipse_plot <- ggplot(Ellipse_plots_data, aes( x = model_, y = proportion_overlap , fill = model_) ) +
      geom_boxplot(outlier.colour = c("grey40") , outlier.size=3.5) + 
      scale_fill_manual(values=c("cadetblue", "orange", "orangered3")) +
      facet_wrap(~Ellipse_Size_) + theme_bw() +labs(title="Standard Deviational Ellipse Proportion Overlap with Ground Truth",
                                            x="Grid Size for Ellipse Groups", y="Propotion of Ellipse Area Overlap") + 
      guides(fill = guide_legend("Model_Type")) 
    print(Ellipse_plot + theme(strip.text.x = element_text(size=16, face="bold")) + 
      theme(axis.text.x = element_text(colour="black",
                                         size = 11,
                                         face = "bold.italic",
                                         angle=45,
                                         vjust=1,
                                         hjust=1)))
      
    
    # Ellipse_areas_proportions_10000 <- gather(Ellipse_areas[1,c(3,6,7)],model,overlapped,
    #                                           AutoReview_intersection_area:FLAPS_intersection_area,
    #                                           factor_key=TRUE)
    # Ellipse_areas_proportions_10000<-Ellipse_areas_proportions_10000[,c(1,3)] %>%
    #   mutate(not_overlapped=TP_FN_ellipse_area-overlapped) %>%
    #   select(overlapped,not_overlapped)
    # rownames(Ellipse_areas_proportions_10000) <- c("AutoReview","FLAPS")
    # Ellipse_areas_proportions_10000<-as.matrix(Ellipse_areas_proportions_10000)
    # prop.test(Ellipse_areas_proportions_10000)
    # 
    # Ellipse_areas_proportions_20000 <- gather(Ellipse_areas[2,c(3,6,7)],model,overlapped,
    #                                           AutoReview_intersection_area:FLAPS_intersection_area,
    #                                           factor_key=TRUE)
    # Ellipse_areas_proportions_20000<-Ellipse_areas_proportions_20000[,c(1,3)] %>%
    #   mutate(not_overlapped=TP_FN_ellipse_area-overlapped) %>%
    #   select(overlapped,not_overlapped)
    # rownames(Ellipse_areas_proportions_20000) <- c("AutoReview","FLAPS")
    # Ellipse_areas_proportions_20000<-as.matrix(Ellipse_areas_proportions_20000)
    # prop.test(Ellipse_areas_proportions_20000)
    # 
    # Ellipse_areas_proportions_3000 <- gather(Ellipse_areas[3,c(3,6,7)],model,overlapped,
    #                                           AutoReview_intersection_area:FLAPS_intersection_area,
    #                                           factor_key=TRUE)
    # Ellipse_areas_proportions_3000<-Ellipse_areas_proportions_3000[,c(1,3)] %>%
    #   mutate(not_overlapped=TP_FN_ellipse_area-overlapped) %>%
    #   select(overlapped,not_overlapped)
    # rownames(Ellipse_areas_proportions_3000) <- c("AutoReview","FLAPS")
    # Ellipse_areas_proportions_3000<-as.matrix(Ellipse_areas_proportions_3000)
    # prop.test(Ellipse_areas_proportions_3000)
}    

########################################
############BUFFER CAPTURE##############
########################################

buffer_capture <- function(counties="all"){
    buffers_home <- "O:/AI Modeling Coop Agreement 2017/Grace Cap Stone Validation/Validation_Results/Buffer_Capture" ## DS - altered
    buffers <- list.files(path=buffers_home, full.names = T, recursive = F)
    ####for regular validation analysis (not cluster):
    buffers <- buffers[!grepl("Cluster",buffers)]
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
    
    #      Sum count and proportion variables by buffer distance.
    capture_plot_final <- aggregate(x=capture_plot[,c("Count_AutoReview","Count_FLAPS","Prop_AutoReview","Prop_FLAPS")],
                                    by=list(capture_plot[,"BUFF_DIST"]),
                                    FUN=sum)
    capture_plot_final <- capture_plot_final %>%
      mutate(BUFF_DIST=Group.1) %>%
      select(-1)
    capture_plot_final <- capture_plot_final %>%
      group_by(BUFF_DIST) %>%
      mutate(Prop_FLAPS=(Prop_FLAPS/(nrow(capture_plot)/5))*100) %>%
      mutate(Prop_AutoReview=(Prop_AutoReview/(nrow(capture_plot)/5))*100)
    
    #      Convert tables from wide to long.
    capture_plot_count <- gather(capture_plot_final[,c(1,2,5)], count_measure, count_value, Count_AutoReview:Count_FLAPS, factor_key=TRUE)
    capture_plot_prop <- gather(capture_plot_final[,c(3,4,5)], prop_measure, prop_value, Prop_AutoReview:Prop_FLAPS, factor_key=TRUE)
    capture_plot_final <- merge(capture_plot_prop,capture_plot_count,by="BUFF_DIST")
    
    #      Create box-and-whiskers plots to display "Buffer Capture" method results.
    par(mar=c(6, 4.5, 4, 5.5) + 0.1)
    
    capture_prop_AutoReview <- rownames(capture_plot_final[capture_plot_final$prop_measure=="Prop_AutoReview",])
    capture_prop_FLAPS <- rownames(capture_plot_final[capture_plot_final$prop_measure=="Prop_FLAPS",])
    plot(capture_plot_final[c(capture_prop_AutoReview),"BUFF_DIST"],
         capture_plot_final[c(capture_prop_AutoReview),"prop_value"],
         pch=16, cex=0.8,axes=FALSE, ylim=c(0,100),
         xlab="Buffer size (meters)", ylab="", type="b",col="#f08671",
         main="Results of 'buffer capture' method for assessing locational accuracy")
    axis(2, ylim=c(0,100),col="#ca0020",col.axis="#ca0020",las=1)  ## las=1 makes horizontal labels
    axis(1, xlim=c(-90,5090),col="black",las=2)  ## las=1 makes horizontal labels
    lines(capture_plot_final[c(capture_prop_FLAPS),"BUFF_DIST"],
          capture_plot_final[c(capture_prop_FLAPS),"prop_value"],
          type="o", pch=22, cex=0.8, lty=2, col="#ca0020")
    mtext("% of buffers that capture a modelled farm",side=2,line=3,cex=0.8)
    
    par(new=TRUE)
    
    capture_count_AutoReview <- rownames(capture_plot_final[capture_plot_final$count_measure=="Count_AutoReview",])
    capture_count_FLAPS <- rownames(capture_plot_final[capture_plot_final$count_measure=="Count_FLAPS",])
    plot(capture_plot_final[c(capture_count_AutoReview),"BUFF_DIST"], 
         capture_plot_final[c(capture_count_AutoReview),"count_value"], pch=15, cex=0.8,xlab="", ylab="", 
         ylim=c(0,50000), axes=FALSE, type="b", col="#92c5de")
    lines(capture_plot_final[c(capture_count_FLAPS),"BUFF_DIST"],capture_plot_final[c(capture_count_FLAPS),"count_value"],
          type="o", pch=22, cex=0.8,lty=2, col="#0571b0")
    
    mtext("Number of modelled farms captured by buffer",side=4,line=3.7,cex=0.8) 
    axis(4, ylim=c(0,50000), col="#0571b0",col.axis="#0571b0",las=1)
    
    legend(x=10,y=49700,title="Model captured",legend=c("Hybrid","FLAPS"),
           text.col="black",col="black",lty=c(1,2),pch=c(15,22),bty="n")
}

########################################
########DISTANCES BETWEEN FARMS#########
########################################
farm_distances <- function(counties="all"){
    distances_home <- "O:/AI Modeling Coop Agreement 2017/Grace Cap Stone Validation/Validation_Results/Distances"  ## DS: edited
    
    distances <- list.files(path=distances_home, full.names = T, recursive = F)
    
    TP_FN_distances <- data.frame()
    AutoReview_distances <- data.frame()
    FLAPS_distances <- data.frame()
    
    #      Import Distances results into separate data.frames based on data/model type: 
    #      ground truth, hybrid, or FLAPS
    for (i in 1:length(distances)) {
      if (grepl("AutoReview_Distance",distances[i])){
        AutoReview <- fread(distances[i],blank.lines.skip = T,stringsAsFactors = F,
                            header = T, fill = T)
        AutoReview$County <- strapply(distances[i],"Distances/(.*)_AutoReview_Distance",simplify=TRUE)
        AutoReview_distances <- rbind(AutoReview_distances,AutoReview,fill=TRUE)
      }
      if (grepl("TP_FN_Distance",distances[i])){
        TP_FN <- fread(distances[i],blank.lines.skip = T,stringsAsFactors = F,
                       header = T, fill = T)
        TP_FN$County <- strapply(distances[i],"Distances/(.*)_TP_FN_Distance",simplify=TRUE)
        TP_FN_distances <- rbind(TP_FN_distances,TP_FN,fill=TRUE)
      }
      if (grepl("FLAPS_Distance",distances[i])){
        FLAPS <- fread(distances[i],blank.lines.skip = T,stringsAsFactors = F,
                       header = T, fill = T)
        FLAPS$County <- strapply(distances[i],"Distances/(.*)_FLAPS_Distance",simplify=TRUE)
        FLAPS_distances <- rbind(FLAPS_distances,FLAPS,fill=TRUE)
      }
    }
    
    #      Eliminate unnecessary fields (select County and NEAR_DIST); rename NEAR_DIST variable
    #      as model type (e.g. FLAPS, TP_FN, or AutoReview); create count variable
    FLAPS_near_distances <- FLAPS_distances %>%
      select(NEAR_DIST,County) %>%
      mutate(FLAPS=NEAR_DIST) %>%
      select(-1)
    
    TP_FN_near_distances <- TP_FN_distances %>%
      select(NEAR_DIST,County) %>%
      mutate(TP_FN=NEAR_DIST) %>%
      select(-1)
    
    AutoReview_near_distances <- AutoReview_distances %>%
      select(NEAR_DIST,County) %>%
      mutate(AutoReview=NEAR_DIST) %>%
      select(-1)
    
    AutoReview_near_distances$count <- c(1:nrow(AutoReview_near_distances))
    TP_FN_near_distances$count <- c(1:nrow(TP_FN_near_distances))
    FLAPS_near_distances$count <- c(1:nrow(FLAPS_near_distances))
    
    #      Merge three model distances data.frames into single data.frame and convert table from
    #      wide to long.
    Near_distances <- merge(AutoReview_near_distances[,c(2,3)],TP_FN_near_distances[,c(2,3)],by="count")
    Near_distances <- merge(Near_distances,FLAPS_near_distances[,c(2,3)],by="count")
    Near_distances$count <- NULL
    Near_distances <- gather(Near_distances,model,distances,AutoReview:FLAPS,factor_key=TRUE)
    
    Near_distances_AutoReview <- Near_distances %>%
      filter(model=="AutoReview") %>%
      mutate(Farms="Hybrid") %>%
      select(-1)
    Near_distances_TP_FN <- Near_distances %>%
      filter(model=="TP_FN") %>%
      mutate(Farms="Ground truth") %>%
      select(-1)
    Near_distances_FLAPS <- Near_distances %>%
      filter(model=="FLAPS") %>%
      mutate(Farms="FLAPS") %>%
      select(-1)
    
    Near_distances <- rbind(Near_distances_AutoReview,Near_distances_TP_FN)
    Near_distances <- rbind(Near_distances,Near_distances_FLAPS)
    
    #      Create histogram of distance between farms by model type
    library(ggplot2)
    near_dist_histogram <- 
        ggplot(Near_distances, aes(x=distances, color=Farms,fill=Farms)) +
        geom_histogram(alpha=0.5, position="dodge",bins=12) +
        theme(legend.position="right") +
        theme_classic() +
        labs(x = "Distances between farms (meters)", y = "Number of distances") +
        ggtitle("Distribution of models' distances between farms")
    print(near_dist_histogram)
    
    #      Conduct KS tests for statistical significance in differences in distribution of
    #      distances between farms.
    ks.test(FLAPS_near_distances$FLAPS, TP_FN_near_distances$TP_FN,alternative=c("two.sided"))
    ks.test(AutoReview_near_distances$AutoReview, TP_FN_near_distances$TP_FN,alternative=c("two.sided"))
}

########################################
#######RUNNING ALL THE FUNCTIONS########
########################################
# All the functions defined above are run if this script is being run by itself.
# If it is referenced with source(),these functions will not be run when this 
# script is called.
# Note that this is similar to the Python trick of:
#   if __name__=="__main__":
#       [code]
if (sys.nframe() == 0){
    grid_density()
    ellipse_overlap()  # When this is plotted by itself, works fine, but disappears if something else is plotted
    buffer_capture()
    farm_distances()
}
