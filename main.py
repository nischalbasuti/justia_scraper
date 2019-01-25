from urllib.request import urlopen
from bs4 import BeautifulSoup
import re
import states


def get_case_pdf_links(years):
    # Get the case page urls.
    BASE_URL = states.BASE_URL
    case_urls = []
    for state_url in states.urls:
        print(state_url)

        state_page = urlopen(state_url) 
        state_soup = BeautifulSoup(state_page, 'html.parser')

        district_courts_urls = [ BASE_URL+ele['href'] for ele in state_soup.findAll('a') if re.match(r'US District Court for',ele.text) ]

        for year in years:
            for district_courts_url in district_courts_urls:

                # Concatinate year to the url.
                district_courts_url = district_courts_url + year
                print(district_courts_url)

                # Get the page and create soup object.
                district_year_page = urlopen(district_courts_url) 
                district_year_soup = BeautifulSoup(district_year_page, 'html.parser')

                case_urls.extend(district_year_soup.findAll('a', attrs={'class', 'case-name'}))

                while len(district_year_soup.findAll('span', attrs={'class', 'next pagination page'})) > 0:
                    next_url = BASE_URL + district_year_soup.findAll('span', attrs={'class', 'next pagination page'})[0].find_next('a')['href']
                    district_year_page = urlopen(next_url) 
                    district_year_soup = BeautifulSoup(district_year_page, 'html.parser')

                    case_urls.extend(district_year_soup.findAll('a', attrs={'class', 'case-name'}))

    case_urls = [ BASE_URL + case_url['href'] for case_url in case_urls]

    # Get the case pdf urls.
    pdf_urls = []
    for case_url in case_urls:
        print(case_url)
        case_page = urlopen(case_url) 
        case_soup = BeautifulSoup(case_page, 'html.parser')

        pdf_urls.append('https:'+case_soup.findAll('a', attrs={'class', 'pdf-icon pull-right has-margin-bottom-20'})[0]['href'])

    return pdf_urls

years = input("Enter the years to scrape from (comma seperated): ").split(",")
print("scrapping", years)
keywords = input("Enter keywords (comma seperated): ").lower().split(",")
print("searching for", keywords)

import requests
import textract
import os

# Download the pdfs
count = 0
for url in get_case_pdf_links(years):
    r = requests.get(url, stream=True)
    print("downloading", url)
    r.raw.decode_content = True

    pdf_path = "pdfs/%d.pdf" % count
    with open(pdf_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

    pdf_text = textract.process(pdf_path).decode('utf-8').lower()

    contains_all_keywords = False
    for word in keywords:
        if re.search(word, pdf_text):
            contains_all_keywords = True
        else:
            contains_all_keywords = False
            break

    if not contains_all_keywords:
        os.remove(pdf_path)
    count += 1
