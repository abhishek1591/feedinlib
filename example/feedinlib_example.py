#!/usr/bin/python3
# -*- coding: utf-8

import pandas as pd
import logging
import os
try:
    from urllib.request import urlretrieve
except:
    from urllib import urlretrieve

try:
    from matplotlib import pyplot as plt
    plot_fkt = True
except:
    plot_fkt = False

from feedinlib import powerplants as plants
from feedinlib import models
from feedinlib import weather

# Feel free to remove or change these lines
import warnings
warnings.simplefilter(action="ignore", category=RuntimeWarning)
logging.getLogger().setLevel(logging.INFO)

# Specification of the wind model
required_parameter_wind = {
    'h_hub': 'height of the hub in meters',
    'd_rotor': 'diameter of the rotor in meters',
    'wind_conv_type': 'wind converter according to the list in the csv file.'}

# Specification of the pv model
required_parameter_pv = {
    'azimuth': 'Azimuth angle of the pv module',
    'tilt': 'Tilt angle of the pv module',
    'module_name': 'According to the sandia module library.',
    'albedo': 'Albedo value'}

# Specification of the weather data set CoastDat2
coastDat2 = {
    'dhi': 0,
    'dirhi': 0,
    'pressure': 0,
    'temp_air': 2,
    'v_wind': 10,
    'Z0': 0}

# Specification of the pv module
advent210 = {
    'module_name': 'Advent_Solar_Ventura_210___2008_',
    'azimuth': 180,
    'tilt': 30,
    'albedo': 0.2}

# Specification of the pv module
yingli210 = {
    'module_name': 'Yingli_YL210__2008__E__',
    'azimuth': 180,
    'tilt': 30,
    'albedo': 0.2}

# Specifications of the wind turbines
enerconE126 = {
    'h_hub': 135,
    'd_rotor': 127,
    'wind_conv_type': 'ENERCON E 126 7500'}

vestasV90 = {
    'h_hub': 105,
    'd_rotor': 90,
    'wind_conv_type': 'VESTAS V 90 3000'}


def download_file(filename, url):
    if not os.path.isfile(filename):
        logging.info('Copying weather data from {0} to {1}'.format(
            url, filename))
        urlretrieve(url, filename)


def fetch_example_files():
    basic_path = os.path.join(os.path.expanduser("~"), '.oemof')
    filename1 = os.path.join(basic_path, 'weather.csv')
    url1 = 'http://vernetzen.uni-flensburg.de/~git/weather.csv'
    filename2 = os.path.join(basic_path, 'weather_wittenberg.csv')
    url2 = 'http://vernetzen.uni-flensburg.de/~git/weather_wittenberg.csv'
    if not os.path.exists(basic_path):
        os.makedirs(basic_path)
    download_file(filename1, url1)
    download_file(filename2, url2)
    return filename1, filename2


def ready_example_data(filename, datetime_column='Unnamed: 0'):
    df = pd.read_csv(filename)
    return df.set_index(pd.to_datetime(df[datetime_column])).tz_localize(
        'UTC').tz_convert('Europe/Berlin').drop(datetime_column, 1)


filename1, filename2 = fetch_example_files()

# Two Variants to create your weather object
# 1. Variant: Passing all data to the weather class
weather_df = ready_example_data(filename1)
my_weather_a = weather.FeedinWeather(
    data=weather_df,
    timezone='Europe/Berlin',
    latitude=52,
    longitude=12,
    data_heigth=coastDat2)

# 2. Variant: Loading a csv-file that has the feedinlib-csv-header (see docs)
my_weather_b = weather.FeedinWeather()
my_weather_b.read_feedinlib_csv(filename=filename2)

# Loading the weather data
my_weather = my_weather_b

# Initialise the wind model. By now there is only one model but in future
# version one can switch between different models.
wind_model = models.WindPowerPlant(
    required=list(required_parameter_wind.keys()))

# Initialise different power plants
E126_power_plant = plants.WindPowerPlant(model=wind_model, **enerconE126)
V90_power_plant = plants.WindPowerPlant(model=wind_model, **vestasV90)

# Create a feedin series for a specific powerplant under specific weather
# conditions. One can define the number of turbines or the over all capacity.
# If no multiplier is set, the time series will be for one turbine.
E126_feedin = E126_power_plant.feedin(weather=my_weather, number=2)
V90_feedin = V90_power_plant.feedin(
    weather=my_weather, installed_capacity=15000)

E126_feedin.name = 'E126'
V90_feedin.name = 'V90'

if plot_fkt:
    E126_feedin.plot(legend=True)
    V90_feedin.plot(legend=True)
    plt.show()
else:
    print(V90_feedin)

# Initialise the pv model and apply it
pv_model = models.Photovoltaic(required=list(required_parameter_pv.keys()))
yingli_module = plants.Photovoltaic(model=pv_model, **yingli210)
advent_module = plants.Photovoltaic(model=pv_model, **advent210)

pv_feedin1 = yingli_module.feedin(weather=my_weather, number=30000)
pv_feedin2 = yingli_module.feedin(weather=my_weather, area=15000)
pv_feedin3 = yingli_module.feedin(weather=my_weather, peak_power=15000)
pv_feedin4 = yingli_module.feedin(weather=my_weather)
pv_feedin5 = advent_module.feedin(weather=my_weather)

pv_feedin4.name = 'Yingli'
pv_feedin5.name = 'Advent'

# Output
if plot_fkt:
    pv_feedin4.plot(legend=True)
    pv_feedin5.plot(legend=True)
    plt.show()
else:
    print(pv_feedin5)

# Use directly methods of the model
w_model = models.WindPowerPlant(required=[])
w_model.get_wind_pp_types()
cp_values = models.WindPowerPlant(required=[]).fetch_cp_values(
    wind_conv_type='ENERCON E 126 7500')
if plot_fkt:
    plt.plot(cp_values.loc[0, :][2:55].index,
             cp_values.loc[0, :][2:55].values, '*')
    plt.show()
else:
    print(cp_values.loc[0, :][2:55].values)

logging.info('Done!')
