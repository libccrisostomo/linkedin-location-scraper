# importing libraries
from selenium import webdriver
import time
from bs4 import BeautifulSoup
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from sklearn.impute import KNNImputer
from sklearn import preprocessing
import numpy as np
import plotly.express as px

pd.options.mode.chained_assignment = 'raise'


def scrape_LI_page(username, password, keyword='Data Scientist', location='World',
                   experience_levels=('Entry level', 'Associate', 'Mid-Senior level',
                                      'Internship', 'Director', 'Executive'), start_page=1,
                   max_page=None, filename='job_locations'):
    """ Opens a LinkedIn page, logs the user in, and initiates a job search with customizable keywords, location,
    and experience levels (list of strings). Works for LI in english only. Saves a txt file called job_locations.txt
    by default (can be personalized).
    \n

    :param username: username of the account
    :type username: str
    :param password: str, Password of the account
    :type password: str
    :param keyword: job keyword to look for in search
    :param location: job locations to include in search
    :param experience_levels: experience levels, available: ['Entry level', 'Associate', 'Mid-Senior level', 'Internship', 'Director', 'Executive']. Selects all by default
    :param start_page: number of page to start scraping on
    :type start_page: int
    :param max_page: int, maximum number of pages to scrape
    :type max_page: int
    :param filename: name of the txt file that will be saved
    :type filename: str """

    # defining browser as chrome and starting page LinkedIn

    if experience_levels is None:
        experience_levels = ['Entry level', 'Associate', 'Mid-Senior level',
                             'Internship', 'Director', 'Executive']

    browser = webdriver.Chrome(executable_path='./Chromedriver/chromedriver')

    # Open login page
    browser.get('https://www.linkedin.com/login?fromSignIn=true&trk=guest_homepage-basic_nav-header-signin')

    # Enter login info:
    username_id = browser.find_element_by_id('username')
    username_id.send_keys(username)
    pw_id = browser.find_element_by_id('password')
    pw_id.send_keys(password)
    pw_id.submit()

    # Go to webpage
    browser.get('https://www.linkedin.com/jobs/?showJobAlertsModal=false')

    # Find customizable search box id's
    search_boxes = browser.find_elements_by_class_name('jobs-search-box__text-input')
    search_boxes_list = [i.get_attribute('id') for i in search_boxes]
    search_boxes_id = list(filter(None, search_boxes_list))  # list of id's with class = jobs-search-box__text-input

    # Send input to keyword search box
    job_id = browser.find_element_by_id(search_boxes_id[0])
    job_id.send_keys([keyword])

    # Send input to location search box
    location_id = browser.find_element_by_id(search_boxes_id[1])
    location_id.send_keys(location)

    # Click search button
    search_button = browser.find_element_by_class_name('jobs-search-box__submit-button')
    search_button.click()

    # Find customizable filter buttons
    time.sleep(3)  # wait until the page has finished loading
    buttons = browser.find_elements_by_xpath("//button")
    buttons_list = [i.get_attribute('id') for i in buttons]
    buttons_list = list(filter(None, buttons_list))

    # click Experience Level Button
    experience_dropdown = browser.find_element_by_id(buttons_list[13])  # it's the 13th button
    experience_dropdown.click()

    for level in experience_levels:
        # select experience filters
        browser.find_element_by_xpath('//*[text()="' + str(level) + '"]').click()

    # click search button

    experience_dropdown = WebDriverWait(browser, 10).until(EC.element_to_be_clickable(
        (By.ID, buttons_list[13])))
    experience_dropdown.click()
    time.sleep(2)

    # Get page source code
    src = browser.page_source
    soup = BeautifulSoup(src, 'lxml')

    # Strip text from source code
    # Get number os job postings for search
    results = soup.find('small', {'class': 'display-flex t-12 t-black--light t-normal'}).get_text().strip().split()[0]
    results = float(results.replace(',', ''))  # converting str into float
    print('There are ' + str(results) + ' jobs for your search ( ͡°( ͡° ͜ʖ( ͡° ͜ʖ ͡°)ʖ ͡°) ͡°)')

    # Crawling jobs!

    # close the message box to prevent it from obscuring the page buttons, in case the window is minimized
    close_messages = WebDriverWait(browser, 20).until(EC.element_to_be_clickable(
        (By.ID, buttons_list[-2])))  # second to last button on page
    close_messages.click()
    time.sleep(5)  # wait until page is loaded

    # pages available to click
    pages_displayed = browser.find_elements_by_xpath("//*[contains(@class, 'artdeco-pagination__indicator "
                                                     "artdeco-pagination__indicator--number ember-view')]")
    pages = [i.text for i in pages_displayed]

    if not max_page:
        max_page = int(pages[-1])  # max page to click on (last page)

    job_location_list = []  # to save all the locations
    actual_page = start_page  # starting page
    browser.set_window_size(1000, 800)  # so that we can scroll down a page that will only consist of the job offers

    # this loop scrapes the lob locations for every available page

    while actual_page <= max_page:
        # range starts at 2 because page 1 is default
        print('Scrolling page ' + str(actual_page))
        browser.execute_script("window.scrollTo(0, 0)")
        job_location_list = location_crawler(job_location_list, browser)

        if (int(pages[-3]) == actual_page) and (max_page - actual_page) != 3:
            # then we click '...' and land automatically on the next page

            ellipsis_page = browser.find_elements_by_xpath('//button[@type="button" and contains(., "…")]')[-1]
            ellipsis_page.click()
            print('Moving on to page ' + str(actual_page + 1) + '...')

            # reload available pages list
            time.sleep(3)
            pages_displayed = browser.find_elements_by_xpath("//*[contains(@class, 'artdeco-pagination__indicator "
                                                             "artdeco-pagination__indicator--number ember-view')]")
            pages = [i.text for i in pages_displayed]

        elif actual_page != max_page:
            # then we will select the next page
            next_page = browser.find_elements_by_xpath(
                '//button[@type="button" and contains(., "' + str(actual_page + 1) + '")]')
            # there can be several buttons that contain the number we're looking for, hence the next line to find
            # right button
            next_page = list(filter(lambda x: x.text == str(actual_page + 1), next_page))[0]
            next_page.click()
            time.sleep(2)
            pages_displayed = browser.find_elements_by_xpath("//*[contains(@class, 'artdeco-pagination__indicator "
                                                             "artdeco-pagination__indicator--number ember-view')]")
            pages = [i.text for i in pages_displayed]
            print('Moving on to page ' + str(actual_page + 1) + '...')

        else:
            # we have reached the last page
            print('Successfully retrieved ' + str(actual_page) + ' pages with locations of ' + str(
                len(job_location_list)) + ' job offers.')

        # saving job_location_list to txt file
        with open('.\\Data\\Raw .txt files\\' + str(filename) + '.txt', 'w') as f:
            f.write('hello')
            for item in job_location_list:
                try:
                    f.write("%s\n" % item)
                except UnicodeEncodeError:
                    print('This location could not be saved: ' + item)

        actual_page += 1


def location_crawler(job_location_list, browser):
    """ Gets locations from every job offer in the specified LinkedIn page,
    and saves it to the list: job_location_list. Used in  scrape_LI_page. \n
    :param job_location_list: list to extend with job locations
    :type job_location_list: list
    :param browser: webdriver instance
    :return:  list with the extended job locations from all the pages until now"""
    time.sleep(2)
    scrollDownAllTheWay(browser)  # slowly scroll to the bottom om the page in order to get all locations
    job_list = browser.find_elements_by_xpath("//*[contains(@class, 'job-card-container__metadata-item')]")  # jobs
    location_list = [i.text for i in job_list]  # list of job locations
    job_location_list.extend(location_list)  # add job locations from this page to the list
    print('Added ' + str(len(location_list)) + ' locations to list. Total number of locations is ' + str(
        len(job_location_list)) + '.')
    return job_location_list


def scrollDown(driver, value):
    """ Scrolls down a page at a quantity of 'value'
    :param driver: webdriver instance
    :param value: scroll quantity indicator
    :type value: int
    """
    driver.execute_script("window.scrollBy(0," + str(value) + ")")


def scrollDownAllTheWay(driver):
    """ Slowly scrolls down a whole page, step by step as indicated in the function scrollDown, until the page is
    fully loaded, aka there are no changes to the html after further scroll.\n
    :param driver: webdriver instance
    :return: no return, the website is scrolled to the bottom"""
    old_page = driver.page_source
    while True:
        for i in range(2):
            scrollDown(driver, 700)
            time.sleep(2)
        new_page = driver.page_source
        if new_page != old_page:
            old_page = new_page
        else:
            break
    time.sleep(2)
    return True


def process_df(df, country_filter=True):
    """ Processes the location list obtained by scrape_data.py. \n
    - Eliminates the Region of the location, keeping only City and Country
    - Imputes missing values (KNN Imputer w/ 10 neighbors)
    - Uniformizes different notations of city names
    - Eliminates records with location 'Remote'
    - Filters records by country if desired
    :param df: dataframe of a txt file obtained by scrape_data.py
    :param country_filter: a country to filter by, default None
    :type country_filter: str
    :return: pandas DataFrame with processed locations"""

    # importing job location data
    df.columns = ['City', 'Region', 'Country']
    # Missing values in Country
    # if a record only has a missing value in country, we can assume that the country name is in the 'Region' column
    df.loc[:, 'Country'] = df.Country.fillna(df['Region'])

    # Dropping Region: Region is not really interesting... column can be dropped
    df.drop(['Region'], axis=1, inplace=True)

    # Dropping Remote jobs
    # If the City name is = 'remote', then there is no location for the job
    df = df.loc[df.City != 'Remote']

    # eliminate the words 'Metropolian' and 'Area' from city names, as well as some enhancements I manually saw
    new_city = df.loc[:, 'City'].map(lambda x: x.replace('Metropolitan', '').replace('Area', '').replace(
        'Region', '').replace('Community of', '').replace('Greater', '').replace('Lisboa', 'Lisbon').replace(
        'Den Haag', 'The Hague').strip())
    df = df.copy()  # to prevent raising SettingWithCopyError
    df.loc[:, 'City'] = new_city
    df.loc[:, 'Country'] = df.loc[:, 'Country'].map(lambda x: str(x).strip())  # removing unnecessary spaces

    # Remaining missing values in Country
    # some of these missing values can be imputed. For instance, if a record with 'City'='Paris', we can deduce from the
    # remaining data that the missing country is 'France'
    imputer = KNNImputer(n_neighbors=10)
    # converting missing values to strings
    df = df.fillna('nan')
    # saving indices of NaN
    df_nan_index = df.loc[df.Country == 'nan'].index

    # encoding cities and countries, to apply the KKN Imputer
    # defining and fitting label encoder instances for City and Country
    le_city = preprocessing.LabelEncoder()
    le_country = preprocessing.LabelEncoder()

    df.loc[:, 'City'] = le_city.fit_transform(df['City'])
    df.loc[:, 'Country'] = le_country.fit_transform(df['Country'])

    # reinserting missing values
    df.loc[df.index.isin(df_nan_index), 'Country'] = np.nan

    # filling missing values
    df = pd.DataFrame(imputer.fit_transform(df), columns=['City', 'Country'])
    # KNN Imputer returns the average value of the nearest neighbors, but we want int only
    df = df.astype('int32')

    # transforming the labels back to city and country names
    df.loc[:, 'City'] = le_city.inverse_transform(df['City'])
    df.loc[:, 'Country'] = le_country.inverse_transform(df['Country'])

    # if City == Country, then the location of the record misses the city. I'm dropping these records
    df = df.loc[df.City != df.Country]

    # sometimes there is strange information in the 'City' column. I'm dropping every record with numbers in city name
    df = df[~df['City'].str.contains(r'\d', regex=True)]

    # filtering the df by the country of most occurrences. This prevents false locations to persist in the data
    if country_filter and df.Country.nunique() <= 5:
        df = df.loc[df['Country'] == df.Country.value_counts().index[0]]

    return df


def join_locations(df_joined_locations, df):
    """ Joins the locations of two dataframes with job locations. These DataFrames must have been returned
     by the process_data.pt \n
    :param df_joined_locations: A dataframe with columns 'City','Country' and 'Number of jobs'
    :type df: dataframe to merge with df_joined_locations
    :return: pandas DataFrame with the joined locations from df_joined_locations and df """
    df_joined = pd.concat([df_joined_locations, pd.merge(df.drop_duplicates(), df.groupby(
        by='City').count().rename(columns={'Country': 'Number of jobs'}), on='City')])
    return df_joined


def plot_sunburst(df, show=True, save=False, location='unspecified location', template='plotly', transparent_bg=False):
    """ Produces a Plotly sunburst plot for df. The plot can be saved, and shown. \n
    :param template: plotly template
    :param show: if True, plot will be show in browser. Defaults to True
    :param save: if True, plot will be saved to 'Plots' folder as html. Defaults to False
    :param df: DataFrame returned by the function process_df in process_data.py
    :param location: Location of the data origin, to save the plot with an appropriate filename
    :param transparent_bg: if True, the background of the plot is transparent

    """

    fig = px.sunburst(df, path=['Country', 'City'], template=template)
    fig.update_layout(title_text='Job locations in ' + location, title_x=0.5)

    if transparent_bg:
        fig.update_layout({
            'plot_bgcolor': 'rgba(0, 0, 0, 0)',
            'paper_bgcolor': 'rgba(0, 0, 0, 0)',
        })

    if show:
        fig.show()
    if save:
        fig.write_html('.//Plots//' + 'Plot of job locations in ' + location + '.html')
        print('Saved sunburst plot for job locations in ' + location + ' as html file')


def plot_scatter(df, show=True, save=False, min_jobs=10, text=False, template='plotly', transparent_bg=False):
    """ Produces a Plotly scatter plot for a DataFrame returned by process_data.py, combined with some extra information
    regarding average salary, cost of living + rent index, and number of jobs of the data in question. The extra
    information is obtained from the file CostOfLiving_AvgSalary.xlsx from the Sample Data folder. \n
    :param transparent_bg: if True, the background of the plot is transparent
    :param show: if True, plot will be show in browser. Defaults to True
    :param save: if True, plot will be saved to 'Plots' folder as html. Defaults to False
    :param df: DataFrame returned by the function join_locations (with locations of jobs from multiple searches). df_joined_locations defined visualize_data.py
    :param min_jobs: drops cities with less jobs than value
    :param text: if True, City names will be added as annotation
    :param template: plotly template
    :param transparent_bg: if True, the background of the plot is transparent
    """
    cost_of_living_avg_salary_df = pd.read_excel('.\\Data\\Extra Information\\CostOfLiving_AvgSalary.xlsx', index_col=0)
    df_all_info = pd.merge(cost_of_living_avg_salary_df, df.drop('Country', axis=1), how='inner', on='City')
    df_all_info = df_all_info.loc[df_all_info['Number of jobs'] >= min_jobs]

    fig = px.scatter(df_all_info, y='Average Monthly Net Salary', x='Cost of Living Plus Rent Index',
                     size='Number of jobs', hover_name='City', color='Country', log_x=True, size_max=60,
                     text='City' if text else None, template=template,
                     )
    fig.update_traces(textposition='top center')
    fig.add_annotation(x=1.49, y=4100,
                       text='Where dinheiro is papel',
                       showarrow=True,
                       arrowhead=1,
                       xanchor='left',
                       yanchor='auto',
                       ax=6,
                       ay=3950,
                       ayref='y',
                       font={'color': 'magenta'}
                       )
    fig.update_layout(title_text='Cost of living vs. Average salary vs. Number of jobs', title_x=0.5)

    if transparent_bg:
        fig.update_layout({
            'plot_bgcolor': 'rgba(0, 0, 0, 0)',
            'paper_bgcolor': 'rgba(0, 0, 0, 0)',
        })

    if show:
        fig.show()

    if save:
        fig.write_html('.//Plots//' + 'Scatter plot' + '.html')
        print('Saved scatter plot as html file')
