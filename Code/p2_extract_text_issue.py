import urllib
from urllib.request import urlopen, Request
import re
from bs4 import BeautifulSoup
from dateutil.parser import parse
import csv
import numpy as np
import requests
import html5lib
import urllib.request, urllib.error
import pandas as pd
import requests
import functools 
import nltk
from nltk import sent_tokenize
import argparse

# Paragraphes

def remove_unwanted_p(paragraphes):
    """ Remove all the text into paragraphes that is no needed."""
    paragraphes = [p.replace('<p align="justify">','') for p in paragraphes]
    paragraphes = [p.replace('<p align="CENTER">','') for p in paragraphes] 
    #paragraphes = [re.sub('<strong>.+</strong>',' ',str(p)) for p in paragraphes]
    paragraphes = [re.sub('<p align="justify" class="ENB-Body">','',p) for p in paragraphes]
    paragraphes = [re.sub('<font face="Verdana" size="2">','',p) for p in paragraphes]
    paragraphes = [re.sub(r'<font.*?>','',p) for p in paragraphes]
    paragraphes = [re.sub(r'<a.*?>','',p) for p in paragraphes]
    paragraphes = [re.sub(r'<.*?>','',p) for p in paragraphes]
    #paragraphes = [p for p in paragraphes if not p.isupper()] 
    return paragraphes

def find_bad_html(page_string):
    """Find page with bad HTML structure. """
    paragraphes = re.split(r'<p>|</p>|<b>|</b>|<p ',page_string)
    start = "<p>"
    end = "</p>"
    page_string = [start+ p+ end for p in paragraphes]
    return page_string

def clean_page_to_parse(page_string):
    """ Remove comment at the beginning of the hml and also put the <html> tag in lowercase and <b> tags to be able to collect all paragraphes. """
    page_string = find_bad_html(str(page_string))
    page_string = re.sub('<!-- WWW Designer Jeff Anderson janderson@iisd.ca --!>','',str(page_string))
    page_string = re.sub('<!-- WWW Designer Jeff Anderson janderson@iisd.ca --!>','',str(page_string))
    page_string = re.sub('<!-- WWW design Jeff Anderson janderson@iisd.ca ---!>','',str(page_string))
    page_string = re.sub("<!--.*?<html", '<html', page_string, flags=re.MULTILINE)

    page_string = re.sub(r'<HTML>',r'<html>',str(page_string))
    page_string = re.sub(r'</HTML>',r'</html>',str(page_string))

    return bytes(page_string,'utf-8')

def remove_special_char(p):
    """ Remove special char to be able to detect easier sentences. """
    s = p.replace("\r"," ")
    s = s.replace(r'\x'," ")
    s = s.replace("\n"," ")
    s = s.replace("\t"," ")
    s = s.replace("\\x"," ")
    s = s.replace("\\r"," ")
    s = s.replace("\\n"," ")
    s = s.replace("\\t"," ")
    s = s.replace("\\"," ")
    q = re.compile('\s\s+')
    p = re.compile('\n\n+')
    s = q.sub(' ',s)
    s = p.sub(' ',s)

    return s

def remove_footer(paragraphes):
    """ Remove footer of the page with conditions. """
    k = len(paragraphes)
    for i in range(len(paragraphes)):
        if('IN THE CORRIDORS' in paragraphes[i] or 'THINGS TO LOOK'  in paragraphes[i] or 'This issue of' in paragraphes[i]  or 'BRIEF ANALYSIS OF' in paragraphes[i]):
             k=i
             break

    return paragraphes[:k]


def extract_p_tags(html_link):
    """ Extract the <p> tag from a specific html link. """
    #Parse the page 
    r = Request(html_link, headers={'User-Agent': 'Mozilla/5.0'})
    page = urlopen(r).read()
    page = clean_page_to_parse(page)
    soup = soup = BeautifulSoup(page, 'html.parser')

    list_tp = soup.find_all('p',recursive=False)
    if(len(list_tp) == 0):

        x = "."
        list_tp = list(soup.find_all('p'))
    #Extract all the text and remove undesired paragraphes
    list_tp2 = []
    for p in list_tp:
        list_tp2 += re.split('<p>',remove_special_char(str(p)))
    
    list_tp = remove_footer(list_tp2)
    
    # Remove titles and sentences all in uppercase
    list_tp = remove_unwanted_p(list_tp)
    
    return list_tp

def extract_p_tags_411(html_link):
    """ Extract the <p> tag from a specific html link. """
    #Parse the page 
    r = Request(html_link, headers={'User-Agent': 'Mozilla/5.0'})
    page = urlopen(r).read()
    page = clean_page_to_parse(page)
    soup = soup = BeautifulSoup(page, 'html.parser')

    list_tp = soup.find_all('td',recursive=False)
    if(len(list_tp) == 0):

        x = "."
        list_tp = list(soup.find_all('td'))
    #Extract all the text and remove undesired paragraphes
    list_tp2 = []
    
    for p in list_tp:
        list_tp2 += re.split(r'<br/><br/>|<br /><br />',remove_special_char(str(p)))
    list_tp = remove_footer(list_tp2)
    # Remove titles and sentences all in uppercase
    list_tp = remove_unwanted_p(list_tp)
    return list_tp

def extract_p_tags_45(html_link):
    """ Extract <p> tags from link inside "html_link" for Issue# <45. """
    r = Request(html_link, headers={'User-Agent': 'Mozilla/5.0'})
    page_link = urlopen(r).read()
    #page_link = urllib.request.urlopen(html_link).read()
    soup_link = BeautifulSoup(page_link)
    paragraphes = soup_link.findAll('a',href = re.compile('\d+'))
    list_tp = []

    for pa in paragraphes:
        # doesn't use the link of the main page (all issues)
        if(pa['href'] != '1200000e.html'):
            html_link = 'https://enb.iisd.org/vol12/'+pa['href']
            list_tp += extract_p_tags(html_link)

    return list_tp

def extract_from_csv_list_issues(csv_file):
    """ Extract from "csv_file" all the html link to be able to extract all the <p> tags. """
    f = open(csv_file)
    csv_f = csv.reader(f)
    list_pt = []
    return list(csv_f)[1:]

def extract_paragraphes_from_issue(number):
    """ Extract from "csv_file" all the html link to be able to extract all the <p> tags from issue number. """
    list_meetings = extract_from_csv_list_issues('Files/list_meetings.csv')
    for i in range(len(list_meetings)) :
        if(int(list_meetings[i][4])== number):
            line = list_meetings[i]
            break
    
    #Extract for 0 < Issue# < 45 
    if(number < 45 ):
        list_pt = extract_p_tags_45(line[6])

    #Extract for 66 < Issue# < 775
    else :
        list_pt = []
        url = line[6]
        
        request = requests.get(url)
        if(number != 175 and number != 300 and request.status_code == 200):
            if(411 <= number and number <= 420):
                list_pt = extract_p_tags_411(line[6])
            else:
                list_pt = extract_p_tags(line[6])
    
    return list(set(list_pt))


# Sentences 

def extract_from_txt_sentences(list_paragraphes):
    """ From "text_file" extract all the sentences and arrange them. Remove also the footer page (sponsors). """
    list_tp = list_paragraphes

    list_tp_cleaned = list(list_tp)
    list_tp_foot = list_tp_cleaned
    #Remove footer
   
    #Split into sentence from paragraph
    splited_sentence = []
    for s in list_tp_foot:
        splited_sentence += sent_tokenize(s)
    return [s for s in splited_sentence if not(s.isupper())]

def write_sentences(number,list_sentences):
    """ Write sentences+number.txt file. """
    outF = open("Files/sentences-"+str(number)+".txt", "w")
    for line in list_sentences:
    # write line to output file
        outF.write(line)
        outF.write("\n")
    outF.close()

def extract_sentences(list_pragraphes, write, number):
    """ For a specific issue number call functions to extract the sentences."""
    list_sentences = extract_from_txt_sentences(list_pragraphes)
    if(write):
        write_sentences(number, list_sentences)
    else:
        return list_sentences


# Main 

def main():
    """  """
    parser = argparse.ArgumentParser()
    parser.add_argument('number', metavar='n', type=int)
    args = parser.parse_args()
    paragraphes = extract_paragraphes_from_issue(args.number)
    extract_sentences(paragraphes, True, args.number)



if __name__ == "__main__":
    main()

