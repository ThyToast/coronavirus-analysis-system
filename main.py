import streamlit as st
import altair as alt
import datetime
import js2xml
import re
import datetime as dt
import matplotlib.dates as mdates
import scipy.stats as stats
import sklearn
import time
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import tweepy
import re

from googletrans import Translator
from pandas import ExcelWriter
from textblob import TextBlob
from pyecharts import options as opts
from pyecharts.charts import Bar
from streamlit_echarts import st_pyecharts


# cached function for fast response
@st.cache(show_spinner=False)
def getData():
    with st.spinner(text="Fetching data..."):
        url = "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/owid-covid-data.csv"
        df = pd.DataFrame(data=pd.read_csv(url))
        return df


def cleanText(text):
    text = re.sub('@[A-Za-z0–9]+:', '', text)
    text = re.sub('#', '', text)
    text = re.sub('\+n', '', text)
    text = re.sub('RT[\s]+', '', text)
    text = re.sub('https?:\/\/\S+', '', text)
    text = re.sub('⃣', '', text)
    return text


def translateText(text):
    translator = Translator()
    return translator.translate(text).text


def getSubjectivity(text):
    return TextBlob(text).sentiment.subjectivity


def getPolarity(text):
    return TextBlob(text).sentiment.polarity


def getAnalysis(score):
    if score < 0:
        return 'Negative'
    elif score == 0:
        return 'Neutral'
    else:
        return 'Positive'


def getTwitterData(userName: str):
    consumerKey = '2GEG6e2BlCA79Iw1BDZTMcfsm'
    consumerSecret = 'KbqBsUxLWEhyDCWwUQ5rEyCRB2DDq3MtUsLrpi4WRmMqRmaZ7e'
    accessToken = '1862224740-JBq4GzpKSYVbWnwWvtU2EcxocA9TNYqjF0SWsed'
    accessSecret = 'UzTpWyApEQ5UpJIXnVeIPWV8sLoPvnKmDOtzfT9hpOMmO'

    authenticate = tweepy.OAuthHandler(consumerKey, consumerSecret)
    authenticate.set_access_token(accessToken, accessSecret)
    api = tweepy.API(authenticate, wait_on_rate_limit=True)

    posts = api.user_timeline(screen_name=userName, count=100, lang="en", tweet_mode="extended")
    df_twitter = pd.DataFrame([tweet.full_text for tweet in posts], columns=['Tweets'])

    # Data cleaning & translation
    df_twitter['Tweets'] = df_twitter['Tweets'].apply(cleanText)
    df_twitter['Tweets'] = df_twitter['Tweets'].apply(translateText)
    df_twitter['Subjectivity'] = df_twitter['Tweets'].apply(getSubjectivity)
    df_twitter['Polarity'] = df_twitter['Tweets'].apply(getPolarity)
    df_twitter['Analysis'] = df_twitter['Polarity'].apply(getAnalysis)


st.beta_set_page_config(
    layout="centered",
    initial_sidebar_state="auto",
    page_title="Viral Infection Analysis System",  # String or None. Strings get appended with "• Streamlit".
    page_icon="coronavirus.ico",
)

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
.sidebar .sidebar-content h1{
    color: white;
}
[class^="st-b"]  {
    color: white;
    font-family: 'Open Sans', sans-serif;
}
[class^="st-ae st-fh st-fi st-fj st-c5 st-fk st-fa st-fl st-fm"]  {
    color: white;
    font-family: 'Open Sans', sans-serif;
}
[class^="st-ae st-af st-ag st-ah st-fn st-f8 st-fl st-fo st-fp"]  {
    color: white !important;
    font-family: 'Open Sans', sans-serif;
}
.st-bb {
    background-color: transparent;
}
.st-cz {
    fill: white;
}
.st-dr{
    fill: white;
}
.st-ae st-af st-ag st-ah st-fn st-f8 st-fl st-fo st-fp{
    color: white !important;
}
.st-cy{
    color: white !important;
}
.st-bn{
    color: white;
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

countries = ['Afghanistan', 'Albania', 'Algeria', 'Andorra', 'Angola', 'Anguilla', 'Antigua and Barbuda', 'Argentina',
             'Armenia', 'Aruba', 'Australia', 'Austria', 'Azerbaijan', 'Bahamas', 'Bahrain', 'Bangladesh', 'Barbados',
             'Belarus', 'Belgium', 'Belize', 'Benin', 'Bermuda', 'Bhutan', 'Bolivia', 'Bonaire Sint Eustatius and Saba',
             'Bosnia and Herzegovina', 'Botswana', 'Brazil', 'British Virgin Islands', 'Brunei', 'Bulgaria',
             'Burkina Faso', 'Burundi', 'Cambodia', 'Cameroon', 'Canada', 'Cape Verde', 'Cayman Islands',
             'Central African Republic', 'Chad', 'Chile', 'China', 'Colombia', 'Congo', 'Costa Rica', "Cote d'Ivoire",
             'Croatia', 'Cuba', 'Curacao', 'Cyprus', 'Czech Republic', 'Democratic Republic of Congo', 'Denmark',
             'Djibouti', 'Dominica', 'Dominican Republic', 'Ecuador', 'Egypt', 'El Salvador', 'Equatorial Guinea',
             'Eritrea', 'Estonia', 'Ethiopia', 'Faeroe Islands', 'Falkland Islands', 'Fiji', 'Finland', 'France',
             'French Polynesia', 'Gabon', 'Gambia', 'Georgia', 'Germany', 'Ghana', 'Gibraltar', 'Greece', 'Greenland',
             'Grenada', 'Guam', 'Guatemala', 'Guernsey', 'Guinea', 'Guinea-Bissau', 'Guyana', 'Haiti', 'Honduras',
             'Hungary', 'Iceland', 'India', 'Indonesia', 'International', 'Iran', 'Iraq', 'Ireland', 'Isle of Man',
             'Israel', 'Italy', 'Jamaica', 'Japan', 'Jersey', 'Jordan', 'Kazakhstan', 'Kenya', 'Kosovo', 'Kuwait',
             'Kyrgyzstan', 'Laos', 'Latvia', 'Lebanon', 'Liberia', 'Libya', 'Liechtenstein', 'Lithuania', 'Luxembourg',
             'Macedonia', 'Madagascar', 'Malawi', 'Malaysia', 'Maldives', 'Mali', 'Malta', 'Mauritania', 'Mauritius',
             'Mexico', 'Moldova', 'Monaco', 'Mongolia', 'Montenegro', 'Montserrat', 'Morocco', 'Mozambique', 'Myanmar',
             'Namibia', 'Nepal', 'Netherlands', 'New Caledonia', 'New Zealand', 'Nicaragua', 'Niger', 'Nigeria',
             'Northern Mariana Islands', 'Norway', 'Oman', 'Pakistan', 'Palestine', 'Panama', 'Papua New Guinea',
             'Paraguay', 'Peru', 'Philippines', 'Poland', 'Portugal', 'Puerto Rico', 'Qatar', 'Romania', 'Russia',
             'Rwanda', 'Saint Kitts and Nevis', 'Saint Lucia', 'Saint Vincent and the Grenadines', 'San Marino',
             'Saudi Arabia', 'Senegal', 'Serbia', 'Seychelles', 'Sierra Leone', 'Singapore',
             'Sint Maarten (Dutch part)', 'Slovakia', 'Slovenia', 'Somalia', 'South Africa', 'South Korea',
             'South Sudan', 'Spain', 'Sri Lanka', 'Sudan', 'Suriname', 'Swaziland', 'Sweden', 'Switzerland', 'Syria',
             'Taiwan', 'Tanzania', 'Thailand', 'Timor', 'Togo', 'Trinidad and Tobago', 'Tunisia', 'Turkey',
             'Turks and Caicos Islands', 'Uganda', 'Ukraine', 'United Arab Emirates', 'United Kingdom', 'United States',
             'United States Virgin Islands', 'Uruguay', 'Uzbekistan', 'Vatican', 'Venezuela', 'Vietnam', 'Zambia',
             'Zimbabwe']

st.title("Viral Infection Analysis System 🦠😷")
st.sidebar.title("Menu")
page_select = st.sidebar.radio("Select page to view", ('COVID-19 Cases', 'COVID-19 Forecast', 'Health Advice'))

# when covid 19 cases is selected
if page_select == "COVID-19 Cases":
    country_name = st.sidebar.selectbox("Select countries 🌎", countries)
    st.write(" ## Here are the latest cases of COVID-19 in " + country_name)

    data = getData()
    df = data[data['location'] == country_name].iloc[:, 2:9].sort_values(by=['date', 'total_cases'], ascending=False). \
        replace(np.nan, 0) \
        .drop(['location', 'new_cases_smoothed'], axis=1).reset_index(drop=True)
    df['date'] = df['date'].astype('datetime64[ns]')
    df.columns = ['Date', 'Total Cases', 'New Cases', 'Total Deaths', 'New Deaths']
    st.write(df)
    st.write(" ### New cases as of " + df['Date'][0].strftime("%d %B, %Y"))

    chart_data = df.set_index("Date")
    cases_type = st.multiselect("Select data to show", ("New Cases", "Total Cases", "New Deaths", "Total Deaths"),
                                ["New Cases"])
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

# when health advice is selected
if page_select == 'Health Advice':
    twitter_user = st.sidebar.selectbox("Select source of health advice", ('Ministry of Health Malaysia',
                                                                           'World Health Organisation',
                                                                           'WHO South-East Asia'))
    st.write(" ## Health advice & reports from the " + twitter_user)
