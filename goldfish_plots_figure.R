
library(tidyverse)
library(sf)

#tp_fn_locations <- "O:/AI Modeling Coop Agreement 2017/Grace Cap Stone Validation/Validation_Results/TP_FN_Counties/"
tp_fn_fp_locations <- "C:/Users/apddsouth/Documents/TP_FN_FP/"

# define color pallete
#hist_pal <- c("#28D6DC", alpha("#F08080", .4))
hist_pal <- c(alpha("#28D6DC", .5), alpha("red", .3))

gather_the_goldfish <- function(){
    all_counties = 0
    count = 0
    file.names = dir(tp_fn_fp_locations, pattern="_TP_FN_FP.shp$")
    for(f in file.names){
        if (count==0){
            # if this is the first loop, fill all_counties with the first county
            #all_counties <- select(as.data.frame(st_read(dsn=paste0(tp_fn_locations, f))),
            #                        POINT_X, POINT_Y, ProbSurf_1, ICOUNT)
            all_counties = st_read(dsn=paste0(tp_fn_fp_locations, f)) %>% 
                as.data.frame() %>% 
                select(POINT_X, POINT_Y, ProbSurf_1, TP_FN_FP)
            
        } else {
            # then for all the other counties, add that county to the mix. all_counties gets bigger each time.
            #all_counties <- rbind(all_counties, select(st_read(dsn=paste0(tp_fn_locations, f)),
                                    #                   POINT_X, POINT_Y, ProbSurf_1, ICOUNT)
                                 # )
            all_counties = rbind(all_counties,
                                  st_read(dsn=paste0(tp_fn_fp_locations, f)) %>% 
                                      as.data.frame() %>% 
                                      select(POINT_X, POINT_Y, ProbSurf_1, TP_FN_FP)
            )
                
        }
    count = count + 1
    show(count)
    }
    
    show(paste("Completed!"))
    # return the output
    return(all_counties)
}

a <- gather_the_goldfish()

plot_the_goldfish <- function(goldfish_data=gather_the_goldfish(), bin_width=0.05, y_cutoff=5000, mode="density", position="dodge"){
    # Note that mode can be ..density.. or ..count..
    # position can be "identity" to overlay, "dodge" to be next to each other, and "stack" to stack on top
    hist_mode <- function(m){}
    
    # recategorize
    goldfish_data$category[goldfish_data$TP_FN_FP==1 | goldfish_data$TP_FN_FP==2] <- "Correct farm locations"
    goldfish_data$category[goldfish_data$TP_FN_FP==3] <- "False positives"
    
    # plot the plot
    ggplot(goldfish_data, aes(x=ProbSurf_1, y={if (mode=="density"){..density..} else if (mode=="count"){..count..}}, fill=category)) +
        geom_histogram(binwidth=bin_width, position=position, color="black") +
        
        scale_fill_manual(values=hist_pal) +
                stat_bin(binwidth=bin_width, geom="text", data=subset(goldfish_data, category=="Correct farm locations"),
                 colour="black", size=3.5,
                 aes(label=(..count..), 
                     group=category, 
                     y=0.8*({if (mode=="density"){..density..} else if (mode=="count"){..count..}})
                     )) +
        xlab(paste("Probability Surface value (bins of", bin_width, "each)")) +
        ylab({if (mode=="density"){"Density"} else if (mode=="count"){"Count"}}) +
        
        # format the legend. For more info, see here: http://www.sthda.com/english/wiki/ggplot2-legend-easy-steps-to-change-the-position-and-the-appearance-of-a-graph-legend-in-r-software
        theme(legend.position = c(.8, .8))
        
    # cut off the huge first band so we can see the chart better
    #coord_cartesian(ylim = c(0, y_cutoff))
    
}

plot_the_goldfish(a, bin_width=.1)

### Text from Automated Review script
# Column 1 is the numeric label for each bin.
# Columns 2 and 3 are the lower and upper values for that
# particular bin, respectively.
# Column 4 is the percentage of points that should be selected from
# that bin.
# Column 5 will be filled later with the number of points that should
# actually be drawn from that bin.
#ss_bins = (
#    (1, 0.1, 0.2, 3.88),
#    (2, 0.2, 0.3, 7.69),
#    (3, 0.3, 0.4, 11.95),
#    (4, 0.4, 0.5, 19.64),
#    (5, 0.5, 0.6, 23.34),
#    (6, 0.6, 0.7, 20.09),
#    (7, 0.7, 0.8, 11.08),
#    (8, 0.8, 0.9, 2.23),
#    (9, 0.9, 1.0, 0.09),
#)

