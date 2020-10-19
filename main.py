import streamlit as st
import altair as alt
import numpy as np
import pandas as pd
import tweepy
import re
import covid_daily

from googletrans import Translator
from textblob import TextBlob
from statsmodels.tsa.ar_model import AR
from statsmodels.tsa.arima_model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX


# cached function for fast response
@st.cache(show_spinner=False)
def getData():
    with st.spinner(text="Fetching data..."):
        # data = covid_daily.data(country=country_name, chart='graph-cases-daily', as_json=False)
        # data2 = covid_daily.data(country=country_name, chart='coronavirus-cases-linear', as_json=False)
        # data3 = covid_daily.data(country=country_name, chart='graph-active-cases-total', as_json=False)
        # data4 = covid_daily.data(country=country_name, chart='graph-deaths-daily', as_json=False)
        # data5 = covid_daily.data(country=country_name, chart='coronavirus-deaths-linear', as_json=False)
        #
        # df = pd.DataFrame(data)
        # df['Total Cases'] = data2
        # df['Active Cases'] = data3
        # df['New Deaths'] = data4
        # df['Total Deaths'] = data5

        # return df
        # old code
        url = "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/owid-covid-data.csv"
        df = pd.DataFrame(data=pd.read_csv(url))
        return df


@st.cache(show_spinner=False)
def getReport(country: str):
    with st.spinner(text="Fetching data..."):
        if country == 'United States':
            country = 'USA'
        report = covid_daily.overview(as_json=False)
        report = report[report['Country,Other'] == country]
        return report


def capitalize_list(item):
    return item.upper()


def cleanText(text):
    text = re.sub('@[A-Za-z0–9]+:', '', text, flags = re.MULTILINE)
    text = re.sub(r"(?:\@|https?\://)\S+", "", text, flags = re.MULTILINE)
    text = re.sub('#', '', text, flags = re.MULTILINE)
    text = re.sub('\+n', '', text, flags = re.MULTILINE)
    text = re.sub('\n', '', text, flags = re.MULTILINE)
    text = re.sub('RT[\s]+', '', text, flags = re.MULTILINE)
    text = re.sub('⃣', '', text, flags = re.MULTILINE)
    text = re.sub('&amp;', '', text, flags = re.MULTILINE)
    text = re.sub(' +', ' ', text, flags = re.MULTILINE)
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


@st.cache(show_spinner=False)
def getTwitterData(userName: str):
    with st.spinner(text="Fetching data..."):
        consumerKey = '2GEG6e2BlCA79Iw1BDZTMcfsm'
        consumerSecret = 'KbqBsUxLWEhyDCWwUQ5rEyCRB2DDq3MtUsLrpi4WRmMqRmaZ7e'
        accessToken = '1862224740-JBq4GzpKSYVbWnwWvtU2EcxocA9TNYqjF0SWsed'
        accessSecret = 'UzTpWyApEQ5UpJIXnVeIPWV8sLoPvnKmDOtzfT9hpOMmO'

        authenticate = tweepy.OAuthHandler(consumerKey, consumerSecret)
        authenticate.set_access_token(accessToken, accessSecret)
        api = tweepy.API(authenticate, wait_on_rate_limit=True)

        posts = tweepy.Cursor(api.search, q="COVID-19 from:" + userName, rpp=100, tweet_mode="extended").items()

        # posts = api.user_timeline(screen_name=userName, count=100, lang="en", tweet_mode="extended")
        df_twitter = pd.DataFrame([tweet.full_text for tweet in posts], columns=['Tweets'])

        # Data cleaning & translation
        df_twitter['Tweets'] = df_twitter['Tweets'].apply(cleanText)
        df_twitter['Tweets'] = df_twitter['Tweets'].apply(translateText)
        df_twitter['Subjectivity'] = df_twitter['Tweets'].apply(getSubjectivity)
        df_twitter['Polarity'] = df_twitter['Tweets'].apply(getPolarity)
        df_twitter['Analysis'] = df_twitter['Polarity'].apply(getAnalysis)

        return df_twitter


def forecastDf(df, country: str, index: int):
    y = df['Total Cases']
    y = y.astype(np.int)
    y = np.asanyarray(y)

    df['Case Type'] = "Actual Cases"
    df['Date'] = pd.to_datetime(df['Date'])

    model_ar_confirmed = ARIMA(y, order=(2, 0, 0))
    model_fit_ar_confirmed = model_ar_confirmed.fit(disp=False)
    predict_ar_confirmed = model_fit_ar_confirmed.predict(1, (len(y) + index - 1))

    ftr = df.append(pd.DataFrame({'Date': pd.date_range(start=df['Date'].iloc[-1], periods=index, freq='d',
                                                        closed='right')}))
    ftr['Total Cases'] = predict_ar_confirmed
    ftr['Case Type'] = "Forecasted Cases"
    ftr = ftr.reset_index(drop=True)

    df = df.append(ftr)
    st.write(ftr)
    chart = alt.Chart(df).mark_line().encode(
        y='Total Cases:Q',
        x='Date:T',
        color='Case Type:N',
        tooltip=['Date', 'Case Type', 'Total Cases']
    ).properties(
        width=700,
        height=500
    ).interactive()
    st.altair_chart(chart)

    # plt.plot(y, label='Actual Data', color='blue')
    # plt.plot(predict_ar_confirmed, label='Forecasted unknown data (Future)', color='orange')
    # plt.plot(predict_ar_confirmed[:len(
    #     predict_ar_confirmed)-64], label='Forecasted known data (Past/Present)', color='red')
    #
    # plt.title('COVID-19 Prediction for ' + country)
    # plt.xlabel('Time (Days)')
    # plt.ylabel('No. of Infected')
    # plt.legend()
    # plt.show()


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
    background-color: #303039;
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
.st-fn{
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
             'Uruguay', 'Uzbekistan', 'Vatican', 'Venezuela', 'Vietnam', 'Zambia',
             'Zimbabwe']

st.title("Viral Infection Analysis System 🦠😷")
st.sidebar.title("Menu")
page_select = st.sidebar.radio("Select page to view", ('COVID-19 Cases', 'COVID-19 Forecast', 'Health Advice & Report'))

# when health advice is selected
if page_select == 'Health Advice & Report':
    twitter_user = st.sidebar.selectbox("Select source of health advice and report", ('Ministry of Health Malaysia',
                                                                           'World Health Organisation',
                                                                           'WHO South-East Asia'))
    st.write(" ## Tweets & reports from the " + twitter_user)

    if twitter_user == 'Ministry of Health Malaysia':
        twitter_user = 'KKMPutrajaya'
    if twitter_user == 'World Health Organisation':
        twitter_user = 'WHO'
    if twitter_user == 'WHO South-East Asia':
        twitter_user = 'WHOSEARO'

    posts = getTwitterData(twitter_user)
    # st.write(posts)
    j = 1
    sortedDF = posts.sort_values(by=['Polarity'])
    # for i in range(0, sortedDF.shape[0]):
    #     if sortedDF['Analysis'][i] == 'Positive':
    #         st.write('### ** ' + str(j) + ')  **' + sortedDF['Tweets'][i])
    #         j = j + 1

    for i in range(0, sortedDF.shape[0]):
        st.write('### ** ' + str(j) + ')  **' + sortedDF['Tweets'][i])
        j = j + 1

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
    overview = getReport(country_name)

    st.write(" ### Updated as of " + df['Date'][0].strftime("%d %B, %Y"))
    st.write("### **Current reports: ** \n (source: [worldometers.info]("
             "https://www.worldometers.info/coronavirus/))")
    st.write("- ### " + overview['NewCases'].values[0].astype(int).astype(str) + " new cases \n- ### " +
             overview['ActiveCases'].values[0].astype(int).astype(str) + " active cases \n- ### " +
             overview['TotalCases'].values[0].astype(int).astype(str) + " infected in total\n- ### " +
             overview['NewDeaths'].values[0].astype(int).astype(str) + " new deaths\n- ### " +
             overview['TotalDeaths'].values[0].astype(int).astype(str) + " deaths in total")

    chart_data = df.set_index("Date")
    cases_type = st.multiselect("Select data to show", ("New Cases", "Total Cases", "New Deaths", "Total Deaths"),
                                ["New Cases"])
    data = df.melt('Date', var_name='Case Type', value_name='Number of Cases')
    available = data['Case Type'].isin(cases_type)
    data = data[available]

    if not cases_type:
        chart = st.empty
        st.error("Please select at least one data.")

    if cases_type:
        chart = alt.Chart(data).mark_bar().encode(
            y='Number of Cases:Q',
            x='Date:T',
            color='Case Type:N',
            tooltip=['Date', 'Case Type', 'Number of Cases']
        ).properties(
            width=700,
            height=500
        ).interactive()
        st.altair_chart(chart)

    df = df.set_index("Date")
    st.write(df)

# when display forecast is selected
if page_select == "COVID-19 Forecast":
    country_name = st.sidebar.selectbox("Select countries 🌎", countries)
    st.write(" ## Here are the forecasts for COVID-19 in " + country_name)
    data = getData()
    df = data[data['location'] == country_name].iloc[:, 2:5].sort_values(by=['date'], ascending=True). \
        replace(np.nan, 0) \
        .drop(['location'], axis=1).reset_index(drop=True)
    df['date'] = df['date'].astype('datetime64[ns]')
    df.columns = ['Date', 'Total Cases']

    index = st.slider('Select how many days to forecast: ', 1, 365)
    forecastDf(df, country_name, index)

# when covid 19 cases is selected (data based on worldometers)
# if page_select == "COVID-19 Cases":
#     countries = AVAILABLE_COUNTRIES
#     countries = [country.capitalize() for country in countries]
#     country_name = st.sidebar.selectbox("Select countries 🌎", countries)
#     st.write(" ## Here are the latest cases of COVID-19 in " + country_name)
#
#     df = getData(country_name)
#     df = df.sort_values(by=['Date', 'Total Cases'], ascending=False). \
#         replace(np.nan, 0).rename(columns = {'Novel Coronavirus Daily Cases': 'New Cases'})
#
#     overview = getReport(country_name)
#
#     day = df.index[0]
#     day += datetime.timedelta(days=1)
#     day = day.strftime("%d %B, %Y")
#
#     st.write("### **Current reports: ** \n (source: [worldometers.info]("
#              "https://www.worldometers.info/coronavirus/))")
#     st.write(" ### Updated as of " + day)
#     st.write("- ### " + overview['NewCases'].values[0].astype(int).astype(str) + " new cases \n- ### " +
#              overview['ActiveCases'].values[0].astype(int).astype(str) + " active cases \n- ### " +
#              overview['TotalCases'].values[0].astype(int).astype(str) + " infected in total\n- ### " +
#              overview['NewDeaths'].values[0].astype(int).astype(str) + " new deaths\n- ### " +
#              overview['TotalDeaths'].values[0].astype(int).astype(str) + " deaths in total")
#
#     cases_type = st.multiselect("Select data to show", ("New Cases", "Total Cases", "New Deaths", "Total Deaths"),
#                                 ["New Cases"])
#     df.reset_index(level=0, inplace=True)
#     data = df.melt('Date', var_name='Case Type', value_name='Number of Cases')
#     available = data['Case Type'].isin(cases_type)
#     data = data[available]
#
#     if not cases_type:
#         chart = st.empty
#         st.error("Please select at least one data.")
#
#     if cases_type:
#         chart = alt.Chart(data).mark_bar().encode(
#             y='Number of Cases:Q',
#             x='Date:T',
#             color='Case Type:N',
#             tooltip=['Date', 'Case Type', 'Number of Cases']
#         ).properties(
#             width=700,
#             height=500
#         ).interactive()
#         st.altair_chart(chart)
#
#     df = df.set_index("Date")
#     st.write(df)
