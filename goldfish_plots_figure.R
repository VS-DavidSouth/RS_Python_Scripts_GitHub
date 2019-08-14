
library(tidyverse)
library(sf)

tp_fn_locations <- "O:/AI Modeling Coop Agreement 2017/Grace Cap Stone Validation/Validation_Results/TP_FN_Counties/"

gather_the_goldfish <- function(){
    all_counties = 0
    count = 0
    file.names = dir(tp_fn_locations, pattern ="_TP_FN.shp$")
    for(f in file.names){
        if (count==0){
            # if this is the first loop, fill all_counties with the first county
            #all_counties <- select(as.data.frame(st_read(dsn=paste0(tp_fn_locations, f))),
            #                        POINT_X, POINT_Y, ProbSurf_1, ICOUNT)
            all_counties = st_read(dsn=paste0(tp_fn_locations, f)) %>% 
                as.data.frame() %>% 
                select(POINT_X, POINT_Y, ProbSurf_1, ICOUNT)
            
        } else {
            # then for all the other counties, add that county to the mix. all_counties gets bigger each time.
            #all_counties <- rbind(all_counties, select(st_read(dsn=paste0(tp_fn_locations, f)),
                                    #                   POINT_X, POINT_Y, ProbSurf_1, ICOUNT)
                                  )
            all_counties = rbind(all_counties,
                                  st_read(dsn=paste0(tp_fn_locations, f)) %>% 
                                      as.data.frame() %>% 
                                      select(POINT_X, POINT_Y, ProbSurf_1, ICOUNT)
            )
                
        }
        count = count + 1
        show(count)
    }
    show(paste("Completed!"))
    # return the output
    return(all_counties)
}
