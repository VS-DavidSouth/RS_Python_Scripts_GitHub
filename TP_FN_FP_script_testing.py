from Creating_TP_FN_FP_files import *

def collectSummaryStats():
    ##
    ## This function is similar to the collectCounties function except
    ##  instead it looks at the summary spreadsheet for all counties.
    ##
    global summaryStats
    summaryStats = []


    with open(summaryStatsCSV, 'rb') as CSVfile:
        reader = csv.reader(CSVfile)
        for row in reader:
            if not row[0] == 'State' and not row[0] == '' and not row[0] == 'MS2':     # skip the first row which just contains the column labels, also skip MS2 because it wasn't completed
                summaryStats.append(row)

    summaryStats = np.array (summaryStats)

print "Ready to test."

