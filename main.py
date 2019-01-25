import os
import re
from urllib.request import urlopen

import requests
import textract
from bs4 import BeautifulSoup

import states

def get_case_pdf_links(years):
    # Get the case page urls.
    BASE_URL = states.BASE_URL
    case_urls = []
    for state_url in states.urls:
        print("state url:", state_url)

        state_page = urlopen(state_url) 
        state_soup = BeautifulSoup(state_page, 'html.parser')

        district_courts_urls = [ BASE_URL+ele['href'] for ele in state_soup.findAll('a') if re.match(r'US District Court for',ele.text) ]

        for year in years:
            for district_courts_url in district_courts_urls:

                # Concatinate year to the url.
                district_courts_url = district_courts_url + year
                print("district url:", district_courts_url)

                # Get the page and create soup object.
                district_year_page = urlopen(district_courts_url) 
                district_year_soup = BeautifulSoup(district_year_page, 'html.parser')

                case_urls.extend(district_year_soup.findAll('a', attrs={'class', 'case-name'}))

                while len(district_year_soup.findAll('span', attrs={'class', 'next pagination page'})) > 0:
                    next_url = BASE_URL + district_year_soup.findAll('span', attrs={'class', 'next pagination page'})[0].find_next('a')['href']
                    print("next url:", next_url)
                    district_year_page = urlopen(next_url) 
                    district_year_soup = BeautifulSoup(district_year_page, 'html.parser')

                    case_urls.extend(district_year_soup.findAll('a', attrs={'class', 'case-name'}))

    case_urls = [ BASE_URL + case_url['href'] for case_url in case_urls]

    # Get the case pdf urls.
    pdf_urls = []
    for case_url in case_urls:
        print("case url:", case_url)
        case_page = urlopen(case_url) 
        case_soup = BeautifulSoup(case_page, 'html.parser')

        try:
            pdf_urls.append('https:'+case_soup.findAll('a', attrs={'class', 'pdf-icon pull-right has-margin-bottom-20'})[0]['href'])
        except Exception as e:
            print("Error occured:", str(e))

    return pdf_urls

def download_pdfs(pdf_urls, prefix=''):
    # Download the pdfs
    count = 0
    for url in pdf_urls:
        r = requests.get(url, stream=True)
        print("downloading", url)
        r.raw.decode_content = True

        pdf_path = "pdfs/%s_%d.pdf" % (prefix, count)
        with open(pdf_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

        pdf_text = textract.process(pdf_path).decode('utf-8').lower()

        contains_all_keywords = False
        for word in keywords:
            try:
                if re.search(word, pdf_text):
                    contains_all_keywords = True
                else:
                    contains_all_keywords = False
                    break
            except Exception as e:
                print("Error occured:", str(e))
                contains_all_keywords = True
                break

        if not contains_all_keywords:
            try:
                os.remove(pdf_path)
            except Exception as e:
                print("Error occured:", str(e))
                break
        count += 1

if __name__ == '__main__':
    years = input("Enter the years to scrape from (comma seperated): ").split(",")
    print("scrapping", years)

    keywords = input("Enter keywords (comma seperated): ").lower().split(",")
    print("searching for", keywords)

    download_pdfs(get_case_pdf_links(years), '_'.join(years) + '_'.join(keywords))

