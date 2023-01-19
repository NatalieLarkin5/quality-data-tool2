# -*- coding: utf-8 -*-
"""
Created on Tue Jan 10 08:28:20 2023

@author: natalie.larkin
"""

# load packages 
import jupyter
import pandas as pd
import os
import plotly 

# set working directory 
root = "C:/Users/natalie.larkin/OneDrive - Social Finance Ltd/Desktop/ANNEX A SANKEY BUILD"
os.chdir(root)
print(root)
print(os.getcwd())
# Define file paths
input_loc = os.path.join(root,"Data/raw")
int_loc = os.path.join(root,"Data/intermediate")

print(input_loc)
# add output location eventually 
raw_file_name = 'DummyAnnexA.xlsx' 

# Define file names
input_file = os.path.join(input_loc, raw_file_name)
output_wide_journeys_contacts = os.path.join(int_loc, 'contacts_wide_journeys.xlsx')
output_wide_journeys_referrals = os.path.join(int_loc, 'referrals_wide_journeys.xlsx')

# Events we want to include in the child journeys
journey_events = {'contact': {'Contacts':'date of Contact'},
          'early_help_assessment_start': {'Early Help':'Assessment start date'},
          'early_help_assessment_end': {'Early Help':'Assessment completion date'},
          'referral': {'Referrals':'date of referral'},
          'assessment_start': {'Assessments':'Continuous Assessment Start date'},
          'assessment_authorised':{'Assessments':'Continuous Assessment date of Authorisation'},
          's47': {'Sec47 and ICPC': 'Strategy discussion initiating Section 47 Enquiry Start date'},
          'icpc': {'Sec47 and ICPC': 'date of Initial Child Protection Conference'},
          'cin_start': {'Children in Need': 'CIN Start date'},
          'cin_end': {'Children in Need': 'CIN Closure date'},
          'cpp_start': {'Child Protection': 'Child Protection Plan Start date'},
          'cpp_end': {'Child Protection': 'Child Protection Plan End date'},
          'lac_start': {'Children in Care': 'date Started to be Looked After'},
          'lac_end': {'Children in Care': 'date Ceased to be Looked After'}}


# Abbreviations for events (for the "journeys reduced")
events_map = {'contact': 'C',
        'referral': 'R',
        'early_help_assessment_start': 'EH',
        'early_help_assessment_end': 'EH|',
        'assessment_start': 'AS',
        'assessment_authorised': 'AA',
        's47': 'S47',
        'icpc': 'ICPC',
        'cin_start': 'CIN',
        'cin_end': 'CIN|',
        "cpp_start": 'CPP',
        "cpp_end": 'CPP|',
        "lac_start": 'LAC',
        "lac_end": 'LAC|'}


# Functions

def build_annexarecord(input_file, events=journey_events):
    '''
    Creates a flat file with three columns:
    1) child unique id
    2) date
    3) Type
    Based on events in Annex A lists defined in the events argument
    '''

    # Create empty dataframe in which we'll drop our events
    df_list = []

    # Loop over our dictionary to populate the log
    for event in events:
        contents = events[event]
        list_number = list(contents.keys())[0]
        date_column = contents[list_number]
       
        # Load Annex A list
        df = pd.read_excel(os.path.join(input_file), sheet_name=list_number) 
        
        # Get date column information
        df.columns = [col.lower().strip() for col in df.columns]
        
        date_column_lower = date_column.lower()
        if date_column_lower in df.columns:
            df = df[df[date_column_lower].notnull()] # extract dates that aren't null
            df['type'] = event
            df['date'] = df[date_column_lower]
            #df = df[['type', 'date', 'Child Unique ID', 'Ethnicity', 'Gender']] <- this would limit 
            df_list.append(df)
        else:
            print('>>>>>  Could not find column {} in {}'.format(date_column, list_number))
    
    # Pull all events into a unique datafrane annexarecord
    annexarecord = pd.concat(df_list, sort=False)
    
    # Clean annexarecord
    # Define categories to be able to sort events
    ordered_categories = ["contact",
                      "referral",
                      "early_help_assessment_start",
                      "early_help_assessment_end",
                      "assessment_start",
                      "assessment_authorised",
                      "s47",
                      "icpc",
                      "cin_start",
                      "cin_end",
                      "cpp_start",
                      "cpp_end",
                      "lac_start",
                      "lac_end"]
    annexarecord.type = annexarecord.type.astype('category')
    annexarecord.type.cat.set_categories([c for c in ordered_categories if c in annexarecord.type.unique()], inplace=True, ordered=True)
    # Ensure dates are in the correct format
    annexarecord.date = pd.to_datetime(annexarecord.date)
    
    # Sort data so that it is by child, then date 
    annexarecord = annexarecord.sort_values(by=['child unique id', 'date'])
    
    return annexarecord

########################################################################################

def joined_string(series):
    """
    Turns all elements from a series into a string, joining elements with "->"
    """
    list_elements = series.tolist()
    return " -> ".join(list_elements)

#######################################################################################
def create_journeys(df, output_file):
    df = df[~df["date"].isnull()]
    df = df[~df["type"].isnull()]
    df = df.sort_values(['date', 'type'])
    
    # Add new column showing each event in format [00-00-0000/event]
    df["TimeEvent"] = "[" + df.date.astype(str) + "/" + df.type.astype(str) + "]"
    
    # Add new column showing each event in reduced form e.g. "C" for contact
    df["reduced"] = df.type.map(events_map)
    
    # Create both long and reduced journeys
    grouped = df.groupby("id")
    journey_long = grouped['TimeEvent'].apply(joined_string)
    journey_reduced = grouped['reduced'].apply(joined_string)
    
    # Create new dataframe with both long and reduced journeys
    journeys_df = pd.DataFrame({'Child journey': journey_long, 'Child journey reduced': journey_reduced}, index=journey_long.index)
    
    # Save to Excel
    writer = pd.ExcelWriter(output_file, engine='xlsxwriter')
    # Journeys
    journeys_df.to_excel(writer, sheet_name='Child journeys')
    # Events abbreviation
    pd.DataFrame({'Event': list(events_map.keys()), 'Reduced': list(events_map.values())}).to_excel(writer, sheet_name='Legend', index=None)
    writer.save()
    
    return print('Child journeys are done! Have a look in {}'.format(output_file))

########################################################################################
########################################################################################
all_data = build_annexarecord(input_file)

output_to_test = all_data[["child unique id", "type", "date"]]
output_to_test.to_excel(os.path.join(root, "Data/intermediate", "extract_to_review.xlsx"))

# extract the first type of event an individual has 
first_event = all_data.sort_values("date").groupby('child unique id').first()
# tabulate the first type of event 


all_data =all_data.rename(columns = {"child unique id":"id"})
# create indicator for all children that have a contact within the time period 
#step 1 - make an indicator for contacts
all_data["is_contact"] = (all_data['type'] == "contact")
# step two - create a new variable that takes the max 
all_data["has_contact"] = all_data["is_contact"].astype("int").groupby(all_data["id"]).transform('max')


# create indicator for all children that have a contact within the time period 
#step 1 - make an indicator for contacts
all_data["is_referral"] = (all_data['type'] == "referral")
# step two - create a new variable that takes the max 
all_data["has_referral"] = all_data["is_referral"].astype("int").groupby(all_data["id"]).transform('max')


# number of unique children in data set before filtering 
print(all_data["id"].unique().size)
# number of records in data set before filtering
print(all_data["id"].size)



#LIMIT DATA TO CHILDREN WITH A CONTACT
contacts_data = all_data[all_data["has_contact"] ==1]
contacts_data[["id", "type", "date"]].sort_values(by=['id', 'date']).to_excel(os.path.join(root, "Data/intermediate", "contacts_extract.xlsx"))

create_journeys(contacts_data, output_wide_journeys_contacts)

# number of unique children in data set after filtering 
print(contacts_data["id"].unique().size)
# number of records in data set after filtering
print(contacts_data["id"].size)
create_journeys(contacts_data, output_wide_journeys_contacts) # <- this is purely exploration

# LIMIT DATA TO CHILDREN WITH A REFERRAL
referrals_data = all_data[all_data["has_referral"] ==1]
referrals_data[["id", "type", "date"]].sort_values(by=['id', 'date']).to_excel(os.path.join(root, "Data/intermediate", "referrals_extract.xlsx"))
create_journeys(referrals_data, output_wide_journeys_referrals) # <- this is purely exploration

# number of unique children in data set before filtering 
print(referrals_data["id"].unique().size)
# number of records in data set before filtering
print(referrals_data["id"].size)


# CREATE A FUNCTION TO LIMIT DATA 
def limit_file(input_file, initiation="referral", first_outcomes = ["cin_start", "cp_start", "lac_start"]):
    #drop events prior to the referral 
    
    # define what counts as an initial outcome 
    # take the event that happens after the assessment 
    # if there is no assessment, take whatever is next 
    # if there is only an assessment, that equals NFA 
    input_file = input_file.sort_values(by = ["id", "date"])
    input_file["is_start"] = input_file["type"] == initiation
    #create a flag for all records starting with the initiation point
    input_file["keep_flag"] = input_file["is_start"].astype("int").groupby(input_file["id"]).transform("cumsum")
    # limit file to those starting with and following the initiation point
    input_file = input_file[input_file["keep_flag"] >= 1]
    
    # create a flag if they don't have an assessment following referral
    input_file["test"] = 
    
   #create a flag for outcomes 
    input_file["flag_outcome"] = input_file["type"].isin(first_outcomes).astype("int").groupby(input_file["id"]).transform("cumsum")
    
    
    #create a flag for the first outcome 
    
    return input_file



test1 = limit_file(referrals_data)

