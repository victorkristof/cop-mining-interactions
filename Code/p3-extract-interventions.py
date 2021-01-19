import urllib.request
import numpy as np
import requests
import re
from bs4 import BeautifulSoup
from dateutil.parser import parse
import csv
from nltk import sent_tokenize
from nltk import word_tokenize
from nltk.tokenize import MWETokenizer
import csv
import p2_extract_text_issue
from p2_extract_text_issue import extract_paragraphes_from_issue, extract_sentences
import argparse

def write_occurrence_issue(occurences_meetings, s):
    """ Write intervention for a specific issue number. """

    with open(s, "w", newline='') as file:
        writer = csv.writer(file)
        #header
        writer.writerow(('issue_number','entity','interventions'))
        for oc in occurences_meetings:
            for x in oc:
                writer.writerow(x)
        
def open_list_meetings():
    """ Open the csv file that contain all the meetings. """
    f = open('Files/list_meetings.csv')
    return csv.reader(f)

def extract_tuple(line):
    """ Extract tuple for each row from Paula's dataset. """
    l = line.replace('"',"")
    l = l.replace('\n',"")
    l = l.split('\t')
    return l

def clean_tp(sentence):
    """ Clean the sentence by removing special char. """
    s = sentence.replace("\r\n\s\s+"," ")
    s = s.replace("\r\n"," ")
    s = s.replace("\s\s+"," ")
    s = s.replace("\\."," ")
    s = s.replace("\\r\\n"," ")
    p = re.compile(r'<.*?>')
    return p.sub('', s)

def count_occurences(list_sentences, dict_occ, tokenizer1, tokenizer2, tokenizer3, list_entities, number):
    """ Count number of time each entity in list_entities is mentioned in list_sentences. """

    for s in list_sentences:
        #Split line into words with tokenizer to detetc entity
        line = s.replace(",","")
        line_splited = word_tokenize(line)
        tokens = tokenizer1.tokenize(line_splited) 
        tokens = tokenizer2.tokenize(tokens) 
        tokens = tokenizer3.tokenize(tokens) 
        tokens = [clean_tp(token) for token in tokens]
        tokens_c = []
        for i in range(len(tokens)-1):
            if(tokens[i+1] !='.'):
                tokens_c.append(tokens[i])

        for entity in list_entities:
            #Increment value of intervention of the entity
            if(entity in tokens_c):
                dict_occ[entity] += tokens_c.count(entity)               
    rows = [(number, entity, dict_occ[entity]) for entity in dict_occ]
    return rows


def extract_occurences_issue_ENB(list_sentences, number):
    """ Extract all the occurences for each entities for a specific issue. """
    #List sentences
    sentences = list_tp = list_sentences

    # Extract list entities
    list_entities = [s.replace('\n','') for s in list(open('Files/entities_interventions.txt'))]
    list_entities = [s.replace(',','') for s in list_entities]
    list_entities = [s.replace(':','') for s in list_entities]
    
    tokens_entities = [l.split(' ') for l in list_entities]

    tokenizer1 = MWETokenizer(tokens_entities, separator=' ')
    tokenizer2 = MWETokenizer([['G-77','CHINA']], separator='/')
    tokenizer3 = MWETokenizer([['G-77/',' CHINA']], separator=' ')

    occurences_meetings = []

    dict_occurences = dict.fromkeys(list_entities, 0)
    occurences_meetings = count_occurences(sentences, dict_occurences, tokenizer1,tokenizer2,tokenizer3, list_entities, number)
    return occurences_meetings

def extract_from_csv_list_issues(csv_file):
    """ Extract from "csv_file" all the html link to be able to extract all the <p> tags. """
    f = open(csv_file)
    csv_f = csv.reader(f)
    list_pt = []
    l =list(csv_f)[1:]
    issue = []
    for x in l:
        issue.append(int(x[4]))
    return issue

def extract_intervention_range(list_issue):
    interventions = []
    issues_generated = extract_from_csv_list_issues('Files/list_meetings.csv')
   
    for x in list_issue:
        if(x in issues_generated):
            print('Issue '+str(x))
            p = extract_paragraphes_from_issue(x)
            s = extract_sentences(p, False, x)
            e = extract_occurences_issue_ENB(s, x)
            interventions.append(e)
        else:
            print('Issue number '+ str(x)+' not in the list of issue extracted')
    
    s = "Files/interventions-issues-"+ str(list_issue[0]) +"-" + str(list_issue[-1])+".csv"
    write_occurrence_issue(interventions, s)

# Main 
"""
python3 p3_extract_interventions.py --range range start(int) end(int)
python3 p3_extract_interventions.py --range unique unique(int)
"""

def main():
    """ Extract all intervention. """
    parser = argparse.ArgumentParser(prog='PROG')
    subparsers = parser.add_subparsers(help='sub-command help')

    parser.add_argument('--range',action='store_true' )
    # create the parser for the "a" command
    parser_range = subparsers.add_parser('range', help='range help')
    parser_range.add_argument('start', metavar='s', type=int)
    parser_range.add_argument('end', metavar='e', type=int)

    # create the parser for the "b" command
    parser_unique = subparsers.add_parser('unique', help='unique help')
    parser_unique.add_argument('unique', metavar='u', type=int)
    args = parser.parse_args()


    if(args.range):
        list_issues = range(args.start, args.end +1)
        extract_intervention_range(list_issues)
    else:
        
        p = extract_paragraphes_from_issue(args.unique)
        s = extract_sentences(p, False, args.unique)
        e = extract_occurences_issue_ENB(s, args.unique)
        s = "Files/intervention-issues-"+ str(args.unique)+".csv"
        write_occurrence_issue([e], s)
        





if __name__ == "__main__":
    main()
    

