# Import the libraries
from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd 
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns

url = 'https://ycharts.com/companies/TSLA/revenues'
driver = webdriver.Chrome()
driver.get(url)

# Takes all the 'td' tags and save them in the variable revenue
revenue = driver.find_elements(By.TAG_NAME, "td")

# tesla_data contains quarterly dates and revenue per quarter. 
tesla_data = [rev.text for rev in revenue]

""" I could have removed the blank spaces at the beginning by adding an if statement (tesla_data = [rev.text for rev in revenue if rev.text != '']), which 
makes the process more lengthy. Therefore, I have decided to remove them manually in the next step."""

# Removing few blanks at the beginning and creating a df 
date, rev = tesla_data[4::2], tesla_data[5::2]
tesla_rev = pd.DataFrame({
    'date': date,
    'rev': rev
})

# Dropping the last few rows, as those are not related to the quarterly revenue. 
tesla_rev.drop(tesla_rev.tail(14).index, inplace=True)

# Converting the date into datatime
tesla_rev['date'] = pd.to_datetime(tesla_rev['date'])
tesla_rev.sort_values('date', inplace=True)

# Creating a converter from our current rev numbers to int (1e6 for millions and 1e9 for billions) and adding the quarters to the table
def converter(n):
    if n[-1] == 'M':
        return int(float(n[:-1]) * 1e6)
    if n[-1] == 'B':
        return int(float(n[:-1]) * 1e9)

tesla_rev['full_rev'] = tesla_rev['rev'].apply(converter)
tesla_rev['quarter'] = tesla_rev['date'].dt.to_period('Q').astype(str)

# Creating a database with data from tesla_rev dataframe
conn = sqlite3.connect('tesla_database.db')
tesla_rev.to_sql('rev', conn, if_exists='replace', index=False)
conn.commit()

# Creating a second dataframe to compare Tesla's revenue vs other car manufacturers (benchmark)
bench = tesla_data[-28:-18]
comp, rev_q2 = bench[::2], bench[1::2]

benchmark = pd.DataFrame({
    'company': comp, 
    'revenue Q2': rev_q2
    })

# Adding Tesla to the dataframe 
benchmark.loc[len(benchmark.index)] = ['Tesla Inc', tesla_rev.loc[tesla_rev.index[49]]['rev']]
benchmark['full_rev'] = benchmark['revenue Q2'].apply(converter)
benchmark = benchmark.reset_index(drop=True).sort_values('full_rev')

# Adding this df to our database 
benchmark.to_sql('benchmark', conn, if_exists='replace', index=False)
conn.commit()

# Tesla's Quarterly Revenue since Q1-2012 plot
plt.figure(figsize=(15,6))
plt.title("Tesla's Quarterly Revenue since Q1-2012")
sns.barplot(x='quarter', y='full_rev', data=tesla_rev, color='red')
plt.xlabel('Date')
plt.xticks(rotation=90)
plt.ylabel('Revenue')
current_values = (plt.gca().get_yticks())/1000000
plt.gca().set_yticklabels(['{:,.0f} M'.format(x) for x in current_values])
plt.show()

# Tesla's Yearly Revenue 2012-2023 plot
yearly_rev = tesla_rev.groupby(tesla_rev['date'].dt.year)['full_rev'].sum().reset_index()
yearly_rev.drop(index=12, axis=0, inplace=True)
plt.figure(figsize=(15,6))
plt.title("Tesla's Yearly Revenue 2012-2023")
sns.barplot(x='date', y='full_rev', data=yearly_rev, palette='flare')
plt.xlabel('Year')
plt.ylabel('Revenue')
current_values = (plt.gca().get_yticks())/1000000000
plt.gca().set_yticklabels(['{:,.2f} B'.format(x) for x in current_values])
plt.show()

# Car Companies Benchmark - 2024Q2 Rev plot 
plt.figure(figsize=(12,6))
plt.title("Car Companies Benchmark - 2024Q2 Rev")
sns.barplot(data=benchmark, x='company', y='full_rev', hue='company')
plt.xlabel('Company')
plt.ylabel('Revenue')
current_values = (plt.gca().get_yticks())/1000000000
plt.gca().set_yticklabels(['{:,.2f} B'.format(x) for x in current_values])
plt.show()
