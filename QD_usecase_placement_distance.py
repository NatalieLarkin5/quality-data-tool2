
# load packages 
import jupyter
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go 
from ipywidgets import widgets
from ipywidgets import interact
import numpy as np
import datetime

import urllib.request
import json

# set working directory 
root = "C:/Users/natalie.larkin/OneDrive - Social Finance Ltd/Desktop/Quality Data - Tool 2"
os.chdir(root)
print(root)
print(os.getcwd())
# Define file paths
input_loc = os.path.join(root,"Data/raw/fake903csv")

# add output location eventually 
epi_file_name = 'episodes_pl_distance.csv' 

epis = pd.read_csv(os.path.join(input_loc, epi_file_name)) 
header = pd.read_csv(os.path.join(input_loc, "header.csv")) 

#rename columns
epis = epis.rename(columns = {"CHILD":"id"})
epis.columns = map(str.lower, epis.columns)

header = header.rename(columns = {"CHILD":"id"})
header.columns = map(str.lower, header.columns)

epis["cnt"] = 1
# tag the number of episodes
epis = epis.sort_values(by = ["id","decom"])
epis[("epi_num")] = epis["cnt"].groupby(epis["id"]).transform("cumsum")

epis["first_placement"] = epis["epi_num"] == 1


epis = epis.merge(header, on = "id", validate = "many_to_one")



@interact
def read_values(
    xvar=widgets.Dropdown(options=[("Placement type","pl"), ("Gender", "sex"), ("Ethnicity", "ethnic"), ("First placement episode in data?", "first_placement")],
                               value='ethnic',
                               description='Child or episode characteristic',
                          style= {'description_width': 'initial'})):

    
    dt = epis.sort_values(by = xvar) 
    dt["ind"] = dt.reset_index().index
   
    
    fig = px.scatter(dt, 
                 x = "pl_distance", 
                 color = xvar, 
                 y = "ind", 
                 title = "Placement distance from home post code by episode and characteristics")
    fig.update_layout(yaxis_title = "Placement episode", 
                      xaxis_title = "Placement distance from home post code (km)")
    go.FigureWidget(fig.to_dict()).show()



