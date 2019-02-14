#!/bin/env python3
import os
import re
import argparse
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
        # break  # TODO REMOVE THIS SHIZ, only for the first state.

    case_urls = [ BASE_URL + case_url['href'] for case_url in case_urls]

    # Get the case pdf urls.
    pdf_urls = []
    for case_url in case_urls:
        print("case url:", case_url)
        try:
            case_page = urlopen(case_url) 
            case_soup = BeautifulSoup(case_page, 'html.parser')
            pdf_urls.append('https:'+case_soup.findAll('a',
                attrs={'class',
                    'pdf-icon pull-right has-margin-bottom-20'})[0]['href'])
        except Exception as e:
            print("Error occured:", str(e))
            continue
    
    return pdf_urls

def download_pdfs(pdf_urls, keywords, prefix=''):
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

        contains_all_keywords = False
        try:
            pdf_text = textract.process(pdf_path).decode('utf-8').lower()

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
        except Exception as e:
            print("Error occured:", str(e))

        if not contains_all_keywords:
            try:
                os.remove(pdf_path)
            except Exception as e:
                print("Error occured:", str(e))
                break
        count += 1


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file',
            default = None,
            help='<optional>Path to file containing comma seperated urls of pdf files.')
    parser.add_argument('-y', '--years',
            nargs='+',
            default=None,
            required=False,
            help='Years in which to search for.')
    parser.add_argument('-k', '--keywords',
            nargs='+',
            required=True,
            help='Keywords to search for.')

    args = parser.parse_args()
    keywords = args.keywords
    print("searching for", keywords)

    urls = []


    # TODO: Getting years here for the file prefix. find a better way to get prefix.
    if args.years is None:
        years = input("Enter the years to scrape from (comma seperated): ").split(",")
    else:
        years = args.years
    print("scrapping", years)

    if args.file is not None:
        print('reading urls from', args.file)
        with open(args.file, 'r') as f:
            urls = f.read().split(',')
    else:

        urls = get_case_pdf_links(years)

        with open('_'.join(years) + '.txt', "w+") as f:
            f.write(','.join(urls))

    os.makedirs('pdfs', exist_ok=True)
    download_pdfs(urls, keywords, '_'.join(years) + '_'.join(keywords))

