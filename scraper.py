import datetime
import hashlib
import os
import time

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver

if __name__ == '__main__':
    if not os.path.exists('.cache'):
        os.makedirs('.cache')

    first_rank, last_rank = 2, 287
    fifa_url = 'https://www.fifa.com/fifa-world-ranking/ranking-table/men/rank={}/index.html'

    full_results = []
    driver = webdriver.Chrome()
    try:
        for i in range(first_rank, last_rank+1):
            retr_url = fifa_url.format(i)
            cache_path = os.path.join('.cache', hashlib.md5(retr_url.encode('utf-8')).hexdigest() + '.html')
            if not os.path.exists(cache_path):
                print('Cache miss! Retrieving {}'.format(retr_url))
                driver.get(retr_url)
                time.sleep(2)
                driver.find_element_by_link_text('201-211').click()  # Expand all teams.

                with open(cache_path, 'w') as cache_file:
                    cache_file.write(driver.page_source)

                soup = BeautifulSoup(driver.page_source, 'html.parser')
            else:
                print('Cache hit! {}'.format(retr_url))
                with open(cache_path, 'r') as cached_file:
                    soup = BeautifulSoup(cached_file, 'html.parser')

            # Date
            rank_date = soup.find('div', {'class': ['slider-wrap']}).find('li').text.strip()
            rank_date = datetime.datetime.strptime(rank_date, '%d %B %Y')

            # Ranking Table
            table_classes = {'class': ['table', 'tbl-ranking', 'table-striped']}
            tr_classes = {'class': ['anchor', 'expanded']}
            td_skip = [0, 3, 8, 17, 18]
            for table in soup.find_all('table', table_classes):
                for tr in table.find_all('tr', tr_classes):
                    try:
                        res = [td.text.strip() for i, td in enumerate(tr.find_all('td')) if i not in td_skip]
                        res += [rank_date]
                        full_results.append(res)
                    except TypeError:
                        pass
    finally:
        driver.quit()

    col_names = ['rank', 'country_full', 'country_abrv', 'total_points', 'previous_points', 'rank_change',
                 'cur_year_avg', 'cur_year_avg_weighted', 'last_year_avg', 'last_year_avg_weighted', 'two_year_ago_avg',
                 'two_year_ago_weighted', 'three_year_ago_avg', 'three_year_ago_weighted', 'confederation', 'rank_date']

    fifa_rank_df = pd.DataFrame(full_results, columns=col_names)
    fifa_rank_df['total_points'] = fifa_rank_df['total_points'].apply(lambda x: float(x.split('(')[1][:-1]))
    num_cols = ['rank', 'total_points', 'previous_points', 'rank_change', 'cur_year_avg', 'cur_year_avg_weighted',
                'last_year_avg', 'last_year_avg_weighted', 'two_year_ago_avg', 'two_year_ago_weighted',
                'three_year_ago_avg', 'three_year_ago_weighted']

    for nc in num_cols:
        fifa_rank_df[nc] = pd.to_numeric(fifa_rank_df[nc], errors='coerce')

    fifa_rank_df.to_csv('fifa_ranking.csv', index=False, encoding='utf-8')
