5# -*- coding: utf-8 -*-
"""
Created on Tue Jan 10 08:28:20 2023

@author: natalie.larkin
"""

# load packages 
import jupyter
import pandas as pd
import os
import plotly 
import numpy as np
import datetime
from dateutil.relativedelta import relativedelta


# set working directory 
root = "C:/Users/natalie.larkin/OneDrive - Social Finance Ltd/Desktop/Quality Data - Tool 2"
os.chdir(root)
print(root)
print(os.getcwd())
# Define file paths
input_loc = os.path.join(root,"Data/raw")
int_loc = os.path.join(root,"Data/intermediate")
out_loc = os.path.join(root,"Data/analysis")


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
            #df = df[['type', 'date', 'child unique id', 'ethnicity', 'gender']] #<- this would limit 
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
########################################################################################
all_data = build_annexarecord(input_file)

output_to_test = all_data[["child unique id", "type", "date"]]
output_to_test.to_excel(os.path.join(root, "Data/intermediate", "extract_to_review.xlsx"))

# extract the first type of event an individual has 
first_event = all_data.sort_values("date").groupby('child unique id').first()
# tabulate the first type of event 



##############################################################
############################################################## 
# renaming for simplicity
all_data =all_data.rename(columns = {"child unique id":"id"})
df = all_data


# create a variable we can use to sort when the date is all the same 
event_order = ["contact", "referral", "assessment_start", "assessment_authorised", "cin_start"]
n = 1 
# set to 100 for everthing else 
df["event_ord"] = 100

for t in event_order:
    df.loc[df["type"] == t, "event_ord"] = n
    n = n+1 
df = df.sort_values(by = ['id', 'date', 'event_ord'])

tt = df[['id','date', 'type','event_ord']]

# function to create flags for whether it is a specific time, the cumulative sum, and the max number
def flag_types(df, t):
    df = df.sort_values(by = ["id", "date", "event_ord"])
    df[("is_" +  t)] = (df["type"] == t)
    df[("id_cum_" +  t)] = df[("is_" +  t)].astype("int").groupby(df["id"]).transform("cumsum")
    df[("id_num_" +  t)] = df[("is_" +  t)].astype("int").groupby(df["id"]).transform("max")
    return df

types_to_var = ["referral", "assessment_start", "cpp_start", "lac_start", "assessment_authorised", "cin_start"]

for t in types_to_var: 
    print(t)
    df = flag_types(df, t)

# limit to those who have a referral
df = df[df["id_num_referral"] >= 1]

# drop things before the first referral 
df = df[df["id_cum_referral"] >= 1]

#create new ID for each child-referral sequence 
df["ref_id"] = df["id"].astype("str") +  "_" +  df["id_cum_referral"].astype("str")



 

##############################
# SUBSET BASED ON WIDGET 
##############################

#going to spread by referral ID 

referral_vars = ["ethnicity", "date of birth", "gender", "number of referrals in last 12 months", "referral source"]
core_vars = ["ref_id", "date"] + referral_vars
ref_dta = df[df["type"] == "referral"]
ref_dta = ref_dta[core_vars]

ref_dta =ref_dta.rename(columns = {"number of referrals in last 12 months":"num_ref", 
                                   "date of birth" : "dob", 
                                   "referral source" : "ref_source", 
                                   "date" : "ref_date"})

#MERGE FILTERING VARIABLES BACK ON 
df = df.drop(referral_vars, axis=1) 
df = df.merge(ref_dta, left_on = "ref_id", right_on = "ref_id", validate ="many_to_one")


# FILTERING VARIABLES 
#df = df[df["num_ref"] == "1"] 
df = df[df["gender"] == "b) Female"] 
#df = df[df["ethnicity"] == "a) WBRI"] 
#df = df[df["ref_source"] == "q) 6: Police"] 

################################
# LIMIT THE SAMPLE TO THOSE WITH 45 DAYS BETWEEN REFERRAL AND FINAL DATE IN DATA SET 
################################
last_date = df["date"].max()
print(last_date)
df["time_diff"] = last_date - df["ref_date"]
df["time_diff"] = df["time_diff"].dt.days
# limit to those who have at least 45 days following referral
df = df[df["time_diff"] >= 45]

# only leave people 

# CREATE A FUNCTION TO LIMIT DATA 
def clean_up_NFAs(dta):


    dta = dta.sort_values(by = ["ref_id", "date", "event_ord"])
    # REFERRAL NFAS 
    # we know referrals are going to be the first obs within each referral id
    if dta.iloc[0]["referral nfa?"] == "Yes": 
        # if the last event is a contact, save thelast row and the referral 
        print("referral NFA")
        if dta.iloc[-1]["type"] == "contact":
            dta_first = dta.iloc[[0]]
            dta_last  = dta.iloc[[-1]]
            dta = dta_first.append(dta_last)
        # if it's not a contact, then just keep the referral
        else:
            dta = dta.iloc[[0]]
        # create a new row for referral nfa 
        nfa_row = dta.iloc[[0]]
        nfa_row["type"] = "referral_nfa"
        # change the date to be one day after the referral (**need to check it is always earlier than the contact**)
        nfa_row["date"] = nfa_row["date"] + datetime.timedelta(days=1) 
        return dta.append(nfa_row)
    
    # replace NAs with blanks strings to solve type errors later
    dta["was the child assessed as requiring la children’s social care support?"] = dta["was the child assessed as requiring la children’s social care support?"].fillna('')
    # save the list of index numbers where the type is assessment start 
    asmt_index = np.where(dta["type"] == "assessment_start")
    
    # confirm there is a row with assessment start, then go in there
    # if no assessment, currently just moving along  
    if len(asmt_index[0]) > 0:
        # extract first index where there is an assessment (should be 1, but making sure)
        fa_i = asmt_index[0][0]
        # if they were assessment nfa...
        if "CS Close Case" in dta.iloc[fa_i]["was the child assessed as requiring la children’s social care support?"]: # -> make this more generic
            print("First assessment was NFA")
            # if the last event is a contact, save that the first row (referral), assessment row (should be 1), and contact 
            if dta.iloc[-1]["type"] == "contact":
                dta = dta.iloc[[0, fa_i, -1]]
            # if it's not a contact, then just keep the referral and assessment
            else:
                dta = dta.iloc[[0, fa_i]]
            
            # create a new row for referral nfa 
            ass_nfa_row = dta.iloc[[fa_i]]
            ass_nfa_row["type"] = "assessment_nfa"
            # change the date to be one day after the assessment (need to check it is always earlier than the contact)
            ass_nfa_row["date"] = ass_nfa_row["date"] + datetime.timedelta(days=1) 
            return dta.append(ass_nfa_row)
   
    return dta

df = df.groupby("ref_id").apply(clean_up_NFAs).sort_values(by=['id', 'date']).reset_index(drop=True)

################################################
# SET UP LOGIC FOR SKIPPING CIN PLAN
################################################
# below is the number of days of lag time after cin start date and CPP/LAC before we consider it a different plan step 
days_real_cin = 70 
# variable for is cin or is lac 
df['is_cpp_lac'] = ((df["is_cpp_start"] == 1) | (df['is_lac_start'] == 1)).astype("int")
df['is_cin_cpp_lac'] = ((df["is_cpp_start"] == 1) | (df['is_lac_start'] == 1) | (df['is_cin_start'] == 1)).astype("int")


def drop_fake_cin(dta):
    # create cumulative flag

    dta = dta.sort_values(by = ["id", "date"])
    #extract indices of eligible outcomes 
    cl = np.where((dta["type"] == "cpp_start") | (dta["type"] == "lac_start")) 
    #cl = np.where(dta["type"] in ["cpp_start", "lac_start"]) why doesn't this work? 
    dta["check"] = 500
    if len(cl[0]) > 0:
            # extract first place
            cli = cl[0][0]
            #extract index of cin plan start
            cini = np.where(dta["type"] == "cin_start")[0][0]

            # store the number of days between the two 
            num_days = (dta.loc[dta.index[cli], "date"] - dta.loc[dta.index[cini], "date"]).days
            dta["check"] =  num_days
            if num_days < days_real_cin :
                # drop first cin start row 
                dta = dta.drop(dta.index[cini])
                # drop cin end 
                ce = np.where(dta["type"] == "cin_end")
                if len(ce[0]) > 0:
                    d = ce[0][0]
                    dta = dta.drop(dta.index[d])
            
    return dta

 
df = df.groupby('ref_id').apply(drop_fake_cin).reset_index(drop=True)

# LATEST STATUS 
def flag_last_status(dta): 
        excl = "assessment_start"
    
        dta["last_status"] = 0
        dta = dta.sort_values(by = ["id", "date"])
        #extract indices of eligible outcomes 
        fo_index = np.where(dta["type"] != excl)
        # make sure there is at least some outcome
        if len(fo_index[0]) > 0:
            # extract index of last row 
            last_in = fo_index[0][-1]
            dta.loc[dta.index[last_in], "last_status"] = 1 

        return dta
    
df = df.groupby('ref_id').apply(flag_last_status).reset_index(drop=True)


# FIRST STATUS 
def flag_first_status(dta): 
        
        ffs = ["cpp_start", "lac_start", "cin_start", "assessment_nfa", "referral_nfa", "early_help_assessment_start"]
    
        dta["first_status"] = 0
        dta = dta.sort_values(by = ["id", "date"])
        #extract indices of eligible outcomes 
        ffs_ind =  np.isin(dta["type"], ffs)
        p2 = np.where(ffs_ind == True)
        print(len(p2[0]))
        # make sure there is at least some outcome
        if len(p2[0]) > 0:
            #extract index of last tow 
            ind = p2[0][0]
            dta.loc[dta.index[ind], "first_status"] = 1 

        return dta

df = df.groupby('ref_id').apply(flag_first_status).reset_index(drop=True)


# look closer at data  
check = df[["id", "ref_id", "date", "type", "event_ord", "last_status", "first_status", "case status", "check", "ethnicity", "gender"]].sort_values(by = ['id', 'date'])

# LIMIT OBSERVATIONS 
df_lim = check[(df["type"] == "referral") | (df["last_status"] == 1) | (df["first_status"] == 1)]

#NEED TO REPLICATE LAST ROW IF IT IS THE SAME FOR BOTH 
def dup_last_row(dta):

    if (dta.iloc[-1]["last_status"] == 1) & (dta.iloc[-1]["first_status"] == 1): 
        last_row = dta.iloc[[-1]]
        return dta.append(last_row)
    return dta 
    
df_lim = df_lim.groupby('ref_id').apply(dup_last_row).reset_index(drop=True)
 
#####################################
# STEP 2 - RESHAPING - this code is actually okay except do we want to duplicate the row if first status = final status
#######################################
 
def journey_fy(data, filtering_vars = ["gender", "ethnicity"]): 
    val = "last_status_" + data.iloc[-1]["type"]
 
    data.loc[data.index[-1], "type"] = val
    # limit variables 
    basic_vars = ["ref_id", "type", "date"]
    keep_vars = basic_vars + filtering_vars # need to fix this so it can be empty
    data = data[keep_vars]
    
    # create a new variable that has the next type of event chronologically. I.e., the end point of the journey
    # sort
    data = data.sort_values(by = ["date"])
    data["target"] = data["type"].shift(-1)
    
    # rename type to source 
    data = data.rename(columns = {"type":"source"})
    
    # drop last row within a group because it holds no new information 
    data.drop(index=data.index[-1], 
           axis=0, 
           inplace=True)

    #rename type to source 
    return data

journey = df_lim.groupby('ref_id').apply(journey_fy).reset_index(drop=True)
journey = journey[["target", "source", "ref_id"]]

# collapse data frame 
df_coll = journey.groupby(['target', 'source']).count().reset_index()

#output data for SANKEY
# Save to Excel
df_coll.to_excel(os.path.join(out_loc, "sankey_input.xlsx"), index = False)


#NOTES THESE ARE PLACES THAT ARE RELATIVELY HARD CODED
#if "CS Close Case" in dta.iloc[fa_i]["was the child assessed as requiring la children’s social care support?"]: # -> make this more generic
#     if dta.iloc[0]["referral nfa?"] == "Yes": 

