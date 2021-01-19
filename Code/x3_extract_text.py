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
import spacy
from nltk import sent_tokenize
from nltk import word_tokenize
from nltk.tokenize import MWETokenizer
from country_list import countries_for_language
import argparse

nlp = spacy.load('en')

#Extract from "csv_file" all the html link to be able to extract all the <p> tags
def extract_from_csv_list_issues(csv_file):
    """ Extract from "csv_file" all the html link to be able to extract all the <p> tags. """
    f = open(csv_file)
    csv_f = csv.reader(f)
    list_pt = []
    return list(csv_f)[1:]

def detect_all_sentences(texte):
    about_text = (texte)
    about_doc = nlp(about_text)
    sentences = list(about_doc.sents)
    return sentences

def remove_special_char(p):
    """ Remove special char to be able to detect easier sentences. """
    tag0 = re.compile(r'<script.*?</script>')
    tag1 = re.compile(r'\s\s+')
    tag2 = re.compile(r'<.*?>')
    tag3 = re.compile(r'\n\n+')
    tag4 = re.compile(r'&.*?;')
    tag5 = re.compile(r'\\\'s')
    tag6 = re.compile("b\'.*?HIGHLIGHTS|b\'.*?IISD")

    s = tag0.sub(' ',p)
    s = tag1.sub(' ',s)
    s = tag2.sub('',s)
    s = tag3.sub('',s)
    s = tag4.sub('',s)
    s= tag5.sub("'s",s)
    s= tag6.sub("",s)


    s = s.replace(r'<script.*?</script>','')
    s = s.replace("\r"," ")
    s = s.replace(r'\x'," ")
    s = s.replace("\n"," ")
    s = s.replace("\t"," ")
    s = s.replace("\\x"," ")
    s = s.replace("\\r"," ")
    s = s.replace("\\n"," ")
    s = s.replace("\\t"," ")
    s = s.replace("\\"," ")
    
    return s

def remove_extra(sentences):
    """ Remove footer of the page with conditions. """
    k = len(sentences)
    black_list = ['IN THE CORRIDORS','THINGS TO LOOK','This issue of','BRIEF ANALYSIS OF']
    sentences = [str(p) for p in sentences if not str(p).isupper() and not str(p).isdigit()]
    for l in range(len(sentences)):
        if(black_list[0] in sentences[l] or black_list[1] in sentences[l] or black_list[2] in sentences[l] or black_list[3] in sentences[l]):
            break

    return sentences[:l]

def extract_sentences(html_link):
    """ Extract the <p> tag from a specific html link. """
    r = Request(html_link, headers={'User-Agent': 'Mozilla/5.0'})
    page = urlopen(r).read()
    ps = remove_special_char(str(page))
    sentences_with_extra = detect_all_sentences(ps)
    sentences_without_extra= remove_extra(sentences_with_extra)
    return sentences_without_extra

def extract_html_before(html_link):
    """ Extract <p> tags from link inside "html_link" for Issue# <45. """
    r = Request(html_link, headers={'User-Agent': 'Mozilla/5.0'})
    page_link = urlopen(r).read()
    #page_link = urllib.request.urlopen(html_link).read()
    soup_link = BeautifulSoup(page_link)
    paragraphes = soup_link.findAll('a',href = re.compile('\d+'))
    liste_sentences = []

    for pa in paragraphes:
        # doesn't use the link of the main page (all issues)
        if(pa['href'] != '1200000e.html'):
            html_link = 'https://enb.iisd.org/vol12/'+pa['href']
            liste_sentences += extract_sentences(html_link)

    return liste_sentences

def extract_sentences_for_one_issue(number):
    """ Extract from "csv_file" all the html link to be able to extract all the <p> tags from issue number. """
    
    list_meetings = extract_from_csv_list_issues('Files/list_meetings.csv')
    for i in range(len(list_meetings)) :
        if(int(list_meetings[i][4])== number):
            line = list_meetings[i]
            break
    
    #Extract for 0 < Issue# < 45 
    if(number < 45):
        list_sentences = extract_html_before(line[6])

    #Extract for 66 < Issue# < 775
    else:
        url = line[6]
        list_sentences = []
        request = requests.get(url)
        if(number != 175 and number != 300 and request.status_code == 200):
                list_sentences = extract_sentences(line[6])


    return list_sentences

def extract_sentences_for_all_issues():
    """ Extract from "csv_file" all issues on the ENB website """
    
    # Create a list with all issues 
    list_meetings = extract_from_csv_list_issues('Files/list_meetings.csv')
    list_issues = []
    for i in range(len(list_meetings)) :
        list_issues.append(int(list_meetings[i][4]))

    # Extract for each issue the sentences
    list_sentences = []
    for i in list_issues:
        #test to find entities only 100 issues
        if(i > 45 and i < 780): 
            print(i)
            list_sentences += extract_sentences_for_one_issue(i)
            

    return list_sentences


def write_sentences(number,list_sentences):
    """ Write sentences+number.txt file. """
    outF = open("Text/sentences-"+str(number)+".txt", "w")
    for line in list_sentences:
    # write line to output file
        outF.write(line)
        outF.write("\n")
    outF.close()

def extract_list_sentences(write, number):
    """ For a specific issue number call functions to extract the sentences."""
    list_sentences = extract_sentences_for_one_issue(number)
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
    extract_list_sentences(True, args.number)



if __name__ == "__main__":
    main()
