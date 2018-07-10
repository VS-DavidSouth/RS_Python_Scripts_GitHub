####################### [SCRIPT_NAME].py #######################

############################
####### DESCRIPTION ########
############################

##
## Created by [NAME] [DATE], updated [DATE]
##
## Script Description:
##

############################
########## SETUP ###########
############################

#[IMPORT STATEMENTS]

############################
######## PARAMETERS ########
############################

#[VARRIABLE] = [THING]

############################
##### DEFINE FUNCTIONS #####
############################

def checkTime():
    ##
    ## This function returns a string of how many minutes or hours the
    ##  script has run for so far.
    ##
    timeSoFar = time.time() - start_time
    timeSoFar /= 60     # changes this from seconds to minutes
    
    if timeSoFar < 60. :
        return str(int(round(timeSoFar))) + " minutes"

    else:
        return str(round( timeSoFar / 60. , 1)) + " hours"

############################
######### DO STUFF #########
############################

# Actually reference the functions defined above

if __name__ == '__main__':
    
    ############################
    ######### CLEANUP ##########
    ############################
    
    print "---------------------\nSCRIPT COMPLETE!"
    print "The script took a total of", checkTime() + "."
    print "---------------------"
    

