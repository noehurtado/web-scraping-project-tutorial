import os
from bs4 import BeautifulSoup
import requests
import time
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

# Download HTML 
url = 'https://ycharts.com/companies/TSLA/revenues'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')

# Filtering HTML by tag name 
tesla_data = soup.find_all('td')

# Creating a clean list with dates and revenue values
tesla_qrev = [data.text.strip() for data in tesla_data]

# Separting the previous list and creating a df 
date, rev = tesla_qrev[::2], tesla_qrev[1::2]
tesla_rev = pd.DataFrame({
    'date': date,
    'rev': rev
})

# Dropping the last few rows, as those are not related to the quarterly revenue. 
tesla_rev.drop(tesla_rev.tail(14).index, inplace=True)

# Converting the date into datatime
tesla_rev['date'] = pd.to_datetime(tesla_rev['date'])
tesla_rev.sort_values('date', inplace=True)

# Adding full quantities to revenue for plotting later 
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

# Creating a second table to compare Tesla's revenue vs other car manufacturers (benchmark)
bench = tesla_qrev[-28:-18]
comp, rev_q2 = bench[::2], bench[1::2]
benchmark = pd.DataFrame({
    'company': comp, 
    'revenue Q2': rev_q2
    })
benchmark.loc[len(benchmark.index)] = ['Tesla Inc', tesla_rev.loc[tesla_rev.index[49]]['rev']]
benchmark['full_rev'] = benchmark['revenue Q2'].apply(converter)
benchmark = benchmark.reset_index(drop=True).sort_values('full_rev')

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
