import streamlit as st
import altair as alt
import datetime 

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import js2xml
import re
import datetime as dt
import matplotlib.dates as mdates
import scipy.stats as stats
import sklearn
import time
import math 

from pyecharts import options as opts
from pyecharts.charts import Bar
from streamlit_echarts import st_pyecharts

# cached function for fast response
@st.cache(show_spinner=False)
def get_data():
    with st.spinner(text="Fetching data..."):
        url = "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/owid-covid-data.csv"
        data = pd.read_csv(url)
        df = pd.DataFrame(data=data)
        return df
    
# CSS Theme 
st.markdown(
    """
<link href="https://fonts.googleapis.com/css2?family=Open+Sans&display=swap" rel="stylesheet">

<style>
.reportview-container .markdown-text-container {
    font-family: 'Open Sans', sans-serif;
}
.sidebar .sidebar-content {
    background-image: linear-gradient(#303039,#303039);
    color: #303039;
}
.Widget>label {
    color: white;
    font-family: 'Open Sans', sans-serif;
}
[class^="st-b"]  {
    color: white;
    font-family: 'Open Sans', sans-serif;
}
.st-bb {
    background-color: transparent;
}
.st-cz {
    fill: white;
}
.btn-outline-secondary{
    border-color: #e83e8c;
    color: #e83e8c;
}
.st-at {
    background-color: #303039;
}
.st-df {
    background-color: #303039;
}
footer {
    font-family: 'Open Sans', sans-serif;
}
</style>
""",
    unsafe_allow_html=True,
)

countries = ['Afghanistan', 'Albania', 'Algeria', 'Andorra', 'Angola', 'Anguilla', 'Antigua and Barbuda', 'Argentina', 'Armenia', 'Aruba', 'Australia', 'Austria', 'Azerbaijan', 'Bahamas', 'Bahrain', 'Bangladesh', 'Barbados', 'Belarus', 'Belgium', 'Belize', 'Benin', 'Bermuda', 'Bhutan', 'Bolivia', 'Bonaire Sint Eustatius and Saba', 'Bosnia and Herzegovina', 'Botswana', 'Brazil', 'British Virgin Islands', 'Brunei', 'Bulgaria', 'Burkina Faso', 'Burundi', 'Cambodia', 'Cameroon', 'Canada', 'Cape Verde', 'Cayman Islands', 'Central African Republic', 'Chad', 'Chile', 'China', 'Colombia', 'Congo', 'Costa Rica', "Cote d'Ivoire", 'Croatia', 'Cuba', 'Curacao', 'Cyprus', 'Czech Republic', 'Democratic Republic of Congo', 'Denmark', 'Djibouti', 'Dominica', 'Dominican Republic', 'Ecuador', 'Egypt', 'El Salvador', 'Equatorial Guinea', 'Eritrea', 'Estonia', 'Ethiopia', 'Faeroe Islands', 'Falkland Islands', 'Fiji', 'Finland', 'France', 'French Polynesia', 'Gabon', 'Gambia', 'Georgia', 'Germany', 'Ghana', 'Gibraltar', 'Greece', 'Greenland', 'Grenada', 'Guam', 'Guatemala', 'Guernsey', 'Guinea', 'Guinea-Bissau', 'Guyana', 'Haiti', 'Honduras', 'Hungary', 'Iceland', 'India', 'Indonesia', 'International', 'Iran', 'Iraq', 'Ireland', 'Isle of Man', 'Israel', 'Italy', 'Jamaica', 'Japan', 'Jersey', 'Jordan', 'Kazakhstan', 'Kenya', 'Kosovo', 'Kuwait', 'Kyrgyzstan', 'Laos', 'Latvia', 'Lebanon', 'Liberia', 'Libya', 'Liechtenstein', 'Lithuania', 'Luxembourg', 'Macedonia', 'Madagascar', 'Malawi', 'Malaysia', 'Maldives', 'Mali', 'Malta', 'Mauritania', 'Mauritius', 'Mexico', 'Moldova', 'Monaco', 'Mongolia', 'Montenegro', 'Montserrat', 'Morocco', 'Mozambique', 'Myanmar', 'Namibia', 'Nepal', 'Netherlands', 'New Caledonia', 'New Zealand', 'Nicaragua', 'Niger', 'Nigeria', 'Northern Mariana Islands', 'Norway', 'Oman', 'Pakistan', 'Palestine', 'Panama', 'Papua New Guinea', 'Paraguay', 'Peru', 'Philippines', 'Poland', 'Portugal', 'Puerto Rico', 'Qatar', 'Romania', 'Russia', 'Rwanda', 'Saint Kitts and Nevis', 'Saint Lucia', 'Saint Vincent and the Grenadines', 'San Marino', 'Saudi Arabia', 'Senegal', 'Serbia', 'Seychelles', 'Sierra Leone', 'Singapore', 'Sint Maarten (Dutch part)', 'Slovakia', 'Slovenia', 'Somalia', 'South Africa', 'South Korea', 'South Sudan', 'Spain', 'Sri Lanka', 'Sudan', 'Suriname', 'Swaziland', 'Sweden', 'Switzerland', 'Syria', 'Taiwan', 'Tanzania', 'Thailand', 'Timor', 'Togo', 'Trinidad and Tobago', 'Tunisia', 'Turkey', 'Turks and Caicos Islands', 'Uganda', 'Ukraine', 'United Arab Emirates', 'United Kingdom', 'United States', 'United States Virgin Islands', 'Uruguay', 'Uzbekistan', 'Vatican', 'Venezuela', 'Vietnam', 'Zambia', 'Zimbabwe']

st.title("Viral Infection Analysis System 🦠😷")
country_name = st.sidebar.selectbox("Select countries 🌎", countries)
st.write(" ## Here are the latest cases in " + country_name)

data = get_data()
df = data[data['location']== country_name].iloc[:, 2:9].sort_values(by=['date'], ascending=False).replace(np.nan,0).drop(['location','new_cases_smoothed'], axis = 1).reset_index(drop=True)
df['date'] = df['date'].astype('datetime64[ns]') 
df.columns = ['Date', 'Total Cases', 'New Cases', 'Total Deaths', 'New Deaths']
st.write(df)
st.write(" ### Cases of COVID-19 as of "+ df['Date'][0].strftime("%d %B, %Y"))

chart_data = df.set_index("Date")
cases_type = st.multiselect("Select data to show", ("New Cases", "Total Cases", "New Deaths", "Total Deaths"), ["New Cases"])
if not cases_type:
    st.error("Please select at least one table.")

chart = st.empty()

if 'New Cases' in cases_type:
    chart = st.bar_chart(chart_data[['New Cases']])

if 'Total Cases' in cases_type:
    chart = st.bar_chart(chart_data[['Total Cases']])

if 'New Deaths' in cases_type:
    chart = st.bar_chart(chart_data[['New Deaths']])

if 'Total Deaths' in cases_type:
    chart = st.bar_chart(chart_data[['Total Deaths']])


    
