## This script is meant to be referenced by other scripts using 'import'.
## It contains two dictionaries, one for converting states names to
## their abbreviations, and the other is the reverse.
##
## To use these dictionaries, include the following code in other scripts:
##      sys.path.insert(0, r'O:\AI Modeling Coop Agreement 2017\David_working\Python')
##      from Converting_state_names_and_abreviations import *

def nameFormat (name):
    ##
    ## Function description:
    ##      This function removes symbols that cause problems with file names.
    ##
    ## Input Variables:
    ##      name: the county name that you want to format
    ##
    ## Returns:
    ##      The name, with all the annoying symbols removed, as a string.
    ##
    
    output = name.replace(" ", "_").replace("'","").replace(".","").replace("-","_")

    return output


def entryFormat(name):
    ##
    ## This function turns underscores ('_') to spaces. Note that this will not truly convert counties
    ## back to their original state, because some counties had names like St. Claire, which was
    ## formatted to St_Claire, and this function would reformat it to St Claire, which is not the same.
    ##
    output = name.replace("_", " ")

    return output

state_name_to_abbrev = {    ##
    'Alabama': 'AL',        ## This dictionary is used to document state names and also to switch the 
    'Alaska': 'AK',         ## full state name (Alabama)for the abbreviation (AL). This  section of the
    'Arizona': 'AZ',        ## code was found on github at https://gist.github.com/rogerallen/1583593
    'Arkansas': 'AR',       ## Everything after Wyoming (on both dictionaries) was added for this script.
    'California': 'CA',     ##
    'Colorado': 'CO',
    'Connecticut': 'CT',
    'Delaware': 'DE',
    'Florida': 'FL',
    'Georgia': 'GA',
    'Hawaii': 'HI',
    'Idaho': 'ID',
    'Illinois': 'IL',
    'Indiana': 'IN',
    'Iowa': 'IA',
    'Kansas': 'KS',
    'Kentucky': 'KY',
    'Louisiana': 'LA',
    'Maine': 'ME',
    'Maryland': 'MD',
    'Massachusetts': 'MA',
    'Michigan': 'MI',
    'Minnesota': 'MN',
    'Mississippi': 'MS',
    'Missouri': 'MO',
    'Montana': 'MT',
    'Nebraska': 'NE',
    'Nevada': 'NV',
    'New Hampshire': 'NH',
    'New Jersey': 'NJ',
    'New Mexico': 'NM',
    'New York': 'NY',
    'North Carolina': 'NC',
    'North Dakota': 'ND',
    'Ohio': 'OH',
    'Oklahoma': 'OK',
    'Oregon': 'OR',
    'Pennsylvania': 'PA',
    'Rhode Island': 'RI',
    'South Carolina': 'SC',
    'South Dakota': 'SD',
    'Tennessee': 'TN',
    'Texas': 'TX',
    'Utah': 'UT',
    'Vermont': 'VT',
    'Virginia': 'VA',
    'Washington': 'WA',
    'West Virginia': 'WV',
    'Wisconsin': 'WI',
    'Wyoming': 'WY',
    'District of Columbia': 'DC',
    'Northern Mariana Islands':'MP',
    'Palau': 'PW',
    'Puerto Rico': 'PR',
    'Virgin Islands': 'VI',}

state_abbrev_to_name = {
    'AL': 'Alabama',
    'AK': 'Alaska',
    'AZ': 'Arizona',
    'AR': 'Arkansas',
    'CA': 'California',
    'CO': 'Colorado',
    'CT': 'Connecticut',
    'DE': 'Delaware',
    'FL': 'Florida',
    'GA': 'Georgia',
    'HI': 'Hawaii',
    'ID': 'Idaho',
    'IL': 'Illinois',
    'IN': 'Indiana',
    'IA': 'Iowa',
    'KS': 'Kansas',
    'KY': 'Kentucky',
    'LA': 'Louisiana',
    'ME': 'Maine',
    'MD': 'Maryland',
    'MA': 'Massachusetts',
    'MI': 'Michigan',
    'MN': 'Minnesota',
    'MS': 'Mississippi',
    'MO': 'Missouri',
    'MT': 'Montana',
    'NE': 'Nebraska',
    'NV': 'Nevada',
    'NH': 'New Hampshire',
    'NJ': 'New Jersey',
    'NM': 'New Mexico',
    'NY': 'New York',
    'NC': 'North Carolina',
    'ND': 'North Dakota',
    'OH': 'Ohio',
    'OK': 'Oklahoma',
    'OR': 'Oregon',
    'PA': 'Pennsylvania',
    'RI': 'Rhode Island',
    'SC': 'South Carolina',
    'SD': 'South Dakota',
    'TN': 'Tennessee',
    'TX': 'Texas',
    'UT': 'Utah',
    'VT': 'Vermont',
    'VA': 'Virginia',
    'WA': 'Washington',
    'WV': 'West Virginia',
    'WI': 'Wisconsin',
    'WY': 'Wyoming',
    'DC': 'District of Columbia',
    'MP': 'Northern Mariana Islands',
    'PW': 'Palau',
    'PR': 'Puerto Rico',
    'VI': 'Virgin Islands',}

# Here is the code for using in ArcGIS Arcade, for use in web maps, etc.
# Copy the following and remove the '#'
#var OG_dict ='{"Alabama":"AL","Alaska":"AK","Arizona":"AZ","Arkansas":"AR","California":"CA","Colorado":"CO","Connecticut":"CT","Delaware":"DE","Florida":"FL","Georgia":"GA","Hawaii":"HI","Idaho":"ID","Illinois":"IL","Indiana":"IN","Iowa":"IA","Kansas":"KS","Kentucky":"KY","Louisiana":"LA","Maine":"ME","Maryland":"MD","Massachusetts":"MA","Michigan":"MI","Minnesota":"MN","Mississippi":"MS","Missouri":"MO","Montana":"MT","Nebraska":"NE","Nevada":"NV","New Hampshire":"NH","New Jersey":"NJ","New Mexico":"NM","New York":"NY","North Carolina":"NC","North Dakota":"ND","Ohio":"OH","Oklahoma":"OK","Oregon":"OR","Pennsylvania":"PA","Rhode Island":"RI","South Carolina":"SC","South Dakota":"SD","Tennessee":"TN","Texas":"TX","Utah":"UT","Vermont":"VT","Virginia":"VA","Washington":"WA","West Virginia":"WV","Wisconsin":"WI","Wyoming":"WY","District of Columbia":"DC"}';
#var dict = Dictionary(OG_dict);
#var result = '';
#for (var key in dict){
#    if($feature["STATE_NAME"]==key) result = dict[key]
#};
#return result;