# -*- coding: utf-8 -*-
"""
Created on Tue Jan 10 08:28:20 2023

@author: natalie.larkin
"""

# load packages 
import jupyter
import pandas as pd
import os
import plotly.express as px
import numpy as np
import datetime

# set working directory 
root = "C:/Users/natalie.larkin/OneDrive - Social Finance Ltd/Desktop/Quality Data - Tool 2/Use Case"
os.chdir(root)
print(root)
print(os.getcwd())
# Define file paths
input_loc = os.path.join(root,"Data/raw")
out_loc = os.path.join(root)


print(input_loc)
# add output location eventually 
raw_file_name = 'DummyAnnexA.xlsx' 

# Define file names
input_file = os.path.join(input_loc, raw_file_name)

# READ IN EARLY HELP AND COLLAPSE TO CHILD LEVEL 
df_EH = pd.read_excel(os.path.join(input_file), sheet_name= "Early Help") 

#rename Eh columns
df_EH = df_EH.rename(columns = {"Child Unique ID":"id", 
                                "Assessment start date" : "EH_start", 
                                "Assessment completion date" : "EH_end"})

df_EH = df_EH[["id", "EH_start", "EH_end"]]

# only keep first date per child 
df_EH_lim = df_EH.sort_values(by = ["id", "EH_start"]).groupby("id").first().reset_index()



# READ IN CIN 
df_CIN = pd.read_excel(os.path.join(input_file), sheet_name= "Children in Need") 

#rename CIN columns
df_CIN = df_CIN.rename(columns = {"Child Unique ID":"id", 
                                "CIN Start Date" : "CIN_start", 
                                "CIN Closure Date" : "CIN_end", 
                                "Primary Need Code" : "need_type", 
                                "Ethnicity" :"ethnicity", 
                                "Gender" :"gender"})
#limit CIN 
df_CIN = df_CIN[["id", "CIN_start", "CIN_end", "need_type", "gender", "ethnicity"]]

# only keep first CIN episode 
df_CIN_lim = df_CIN.sort_values(by = ["id", "CIN_start"]).groupby("id").first().reset_index()

# merge files together - only keeping those in the CiN file 
data = pd.merge(df_CIN_lim, df_EH_lim, how = "left", on = ["id"]).reset_index()

# create variable for Early Help before CiN 
data["EH_before_CIN"] = 0 
data.loc[data.EH_start < data.CIN_start, "EH_before_CIN"] = 1


gr_dt = data[["id", "EH_before_CIN", "need_type", "gender", "ethnicity"]]


################################################
################################################
# VISUALISATIONS 
################################################
################################################



def graph(data, group, xvar):
    
        dt = data.groupby([data[group], data[xvar]], as_index = False).size()
        dt['group_size'] = dt.groupby(dt[group])["size"].transform(np.sum)
        dt["perc"] = round((dt["size"]/dt["group_size"])*100, 1)
        fig = px.bar(dt, x = xvar, color = group, y = "perc", title = "test")
        fig.show()

        return dt
 

tst = graph(gr_dt, "EH_before_CIN", "need_type")

tst.show()