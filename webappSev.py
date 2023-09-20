import streamlit as st
import pandas as pd
import os
import plotly.express as px
from dotenv import load_dotenv
from sqlalchemy import create_engine
import plotly
import numpy as np
import datetime
import re
import base64

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOSTNAME = os.getenv("DB_HOSTNAME")
DB_NAME = os.getenv("DB_NAME")
connection_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOSTNAME}:5432/{DB_NAME}"
engine = create_engine(connection_string)

st.title("Interactive Customer Insights")
st.markdown("Yes nice great lovely")        #st.write doet hetzelfde

df_reviews = pd.read_sql_query(
    """
    select
        DATE(datetime) as review_date,
        location_city,
        count(*) as n_reviews,
        AVG(rating_delivery) as avg_del_score,
        AVG(rating_food) as avg_food_score
    from
        reviews revs
    left join
    restaurants rests
    on
        revs.restaurant_id = rests.restaurant_id
    where
        datetime >= '2022-01-01'
        and datetime < '2023-02-01'
        and location_city in ('Groningen', 'Amsterdam', 'Rotterdam')
    group by
        DATE(datetime),
        location_city
    """,
    con=engine
)

def min_max_dates(df_reviews):
    min_date_df = df_reviews.review_date.min()
    max_date_df = df_reviews.review_date.max()
    return min_date_df, max_date_df

min_date_df, max_date_df = min_max_dates(df_reviews)

min_date, max_date = st.slider(
    min_value=min_date_df,
    max_value=max_date_df,
    label="Select dates",
    value=(date(2022, 1, 1), date(2022, 12, 31))
)

#-Slider------------------------------------------------------

#st.slider("Date", 2022-1-1, 2023-31-1, 1)

#-First----------------------------------------------------------------------------------------------------------------#
avg_reviews = df_reviews.groupby(["location_city"], as_index=False)["n_reviews"].mean()
barchart = px.bar(
    avg_reviews,
    x="location_city",
    y="n_reviews",
    labels={
        "n_reviews": "No. of reviews / Day",
        "location_city": "",
    },
    title = 'Average number of reviews per city per day',
    width=600
)
st.plotly_chart(barchart, use_container_width=True)

#-Second---------------------------------------------------------------------------------------------------------------#

df_reviews["weekday"] = pd.to_datetime(df_reviews["review_date"]).dt.dayofweek
df_reviews["daytype"] = np.where(df_reviews["weekday"] < 5, "weekday", "weekend")
avg_reviews = df_reviews.groupby(["location_city", "daytype"])["n_reviews"].mean().reset_index()
barchart2 = px.bar(
    avg_reviews,
    x="location_city",
    y="n_reviews",
    color="daytype",
    barmode="group",
    labels={
        "n_reviews": "No. of reviews / Day",
        "location_city": ""
    },
    width=600
)
st.plotly_chart(barchart2, use_container_width=True)

#-Third----------------------------------------------------------------------------------------------------------------#
linechart = px.line(df_reviews, x='review_date', y='avg_del_score', color='location_city')
st.plotly_chart(linechart, use_container_width=True)

#-Fourth---------------------------------------------------------------------------------------------------------------#

df_reviews["day_of_year"] = pd.to_datetime(df_reviews["review_date"]).dt.dayofyear
scatter = px.scatter(
    df_reviews,
    x="day_of_year",
    y="avg_del_score",
    trendline="ols",
    trendline_color_override="red",
    facet_col="location_city",
    labels={
        "avg_del_score": "Avg Delivery Score on day",
        "day_of_year": "Day of year",
        "location_city": "Location",
    },
)
st.plotly_chart(scatter, use_container_width=True)

#-Fifth---------------------------------------------------------------------------------------------------------------#

scatter2 = px.scatter(
    df_reviews,
    x="day_of_year",
    y="avg_del_score",
    trendline="ols",
    trendline_color_override="red",
    facet_col="location_city",
    labels={
        "avg_del_score": "Avg Delivery Score on day",
        "day_of_year": "Day of year",
        "location_city": "Location",
    },
)

st.plotly_chart(scatter2, use_container_width=True)

#-Sixth---------------------------------------------------------------------------------------------------------------#

df_restaurants = pd.read_sql_query(
    """
    select * from (
        select rests.restaurant_id, rests."colophon_data_postalCode", count(*) as n_reviews, avg(rating_food) as avg_rating_food, avg(rating_delivery) as avg_rating_delivery
        from reviews rv
        left join restaurants rests
        on rv.restaurant_id = rests.restaurant_id
        where rv.datetime > '2022-01-01'
        and rv.datetime < '2023-01-01'
        group by rests.restaurant_id
    ) t
    where n_reviews > 500
    """,
    con=engine
)
df_cbs = pd.read_sql_query("select * from customer_analytics.buurten", con=engine)
df_restaurants['PC4'] = df_restaurants.colophon_data_postalCode.str[:4].astype(int)
df = pd.merge(df_restaurants, df_cbs, left_on='PC4', right_on='MeestVoorkomendePostcode')
scatter3 = px.scatter(df, x='avg_rating_delivery', y='Bevolkingsdichtheid')

st.plotly_chart(scatter3, use_container_width=True)

#-Seventh-------------------------------------------------------------------------------------------------------------#

inwoners_df = df[['Gemeentenaam', 'WijkenEnBuurten', 'Gehuwd', 'Gescheiden', 'Ongehuwd', 'Verweduwd']].melt(
    id_vars=['Gemeentenaam', 'WijkenEnBuurten'], var_name='Huwelijke status', value_name='Aantal Inwoners'
)
boxpl = px.box(inwoners_df, x='Huwelijke status', y='Aantal Inwoners')

st.plotly_chart(boxpl, use_container_width=True)

#-Eighth-------------------------------------------------------------------------------------------------------------#

df['AantalRestaurants'] = df.groupby(['Gemeentenaam', 'WijkenEnBuurten'])['restaurant_id'].transform("count")
leeftijden_wide = df[df.AantalRestaurants >= 3][[
    'Gemeentenaam', 'WijkenEnBuurten',
    'k_0Tot15Jaar', 'k_15Tot25Jaar', 'k_25Tot45Jaar',
    'k_45Tot65Jaar', 'k_65JaarOfOuder' 
]].drop_duplicates()
leeftijden_long = leeftijden_wide.melt(id_vars=['Gemeentenaam', 'WijkenEnBuurten'], var_name='Leeftijdscategorie', value_name='Aantal Inwoners')
leeftijden_long['BuurtLabel'] = leeftijden_long.Gemeentenaam.values + ' - ' + leeftijden_long.WijkenEnBuurten.values
histo = px.histogram(
    leeftijden_long,
    y="BuurtLabel",
    x="Aantal Inwoners",
    color="Leeftijdscategorie",
    barnorm="percent"
)
st.plotly_chart(histo, use_container_width=True)

#-The End-------------------------------------------------------------------------------------------------------------#
