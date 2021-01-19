#!/usr/bin/env python
# coding: utf-8

# In[1]:


import csv
from nltk import word_tokenize
from nltk.tag import StanfordNERTagger
from nltk.tokenize import MWETokenizer
from nltk import sent_tokenize
from itertools import combinations  
import itertools


# In[2]:


def open_dict_interaction():
    dict_entities = {}
    with open("Files/dict_inter.csv") as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            dict_entities[row[0]] = row[1].split(', ')
    return dict_entities    


# In[3]:


def create_dict():
    """Create dictionary that can map entities with an id but also map entities from the original to the generated dataset. """
    DICTIONARY = open_dict_interaction()
    n = 0
    DICTIONARY_NUM = {}
    for k in DICTIONARY:
        DICTIONARY_NUM[k] = n 
        n +=1
    NAMES = []
    for x in list(DICTIONARY.values()):
        if(len(x) == 1):
            NAMES.append(x[0])
        else:
            NAMES += [k for k in x]

    return DICTIONARY, DICTIONARY_NUM, NAMES


# In[4]:


def tokenize_sentence(sentence, country):
    """Split the sentence in a way that the entities are together and will be able to be detected."""
    # Extract list entities
    ENTITIES = [s.replace('\n','') for s in list(open('Files/entities_all.txt'))]
    tokens_entities = [l.split(' ') for l in ENTITIES]
    tokens_entities.append(['on','behalf','of'])
    tokens_entities.append(['on','behalf','of','the'])
    tokens_entities.append(['for'])
    tokens_entities.append(['for','the'])
    tokens_entities.append(['speaking','for'])
    tokens_entities.append(['speaking','for','the'])
    tokens_entities.append(['US','$'])
    tokens_entities.append(['concerns', 'of', 'the'])
    tokens_entities.append(['concerns', 'of'])
    tokens_entities.append(['spoke','with'])
    tokens_entities.append(['for', 'a', 'number','of', 'members' ,'of' ,'the'])
    tokens_entities.append(['for', 'several'])
    tokens_entities.append(['speaking','on','behalf', 'of', 'the'])  
    tokens_entities.append(['supported','by'])
    tokens_entities.append(['supported','by','the'])
    tokens_entities.append(['opposed','by'])
    tokens_entities.append(['opposed','by','the'])
    tokens_entities.append(['proposed','by','the'])
    tokens_entities.append(['proposed','by'])
    tokenizer1 = MWETokenizer(tokens_entities, separator=' ')
    tokenizer2 = MWETokenizer([['G-77','CHINA']], separator='/')
    tokenizer3 = MWETokenizer([['G-77/',' CHINA']], separator=' ')
    
    if(type(sentence) == list):
        line = sentence[0].replace(",","")
    else: 
        line = sentence.replace(",","")
    line_splited = word_tokenize(line)
    tokens = tokenizer1.tokenize(line_splited) 
    tokens = tokenizer2.tokenize(tokens) 
    tokens = tokenizer3.tokenize(tokens) 
    

    return tokens


# In[5]:


def rSubset(arr, cop): 
    """ function that return all the tuples needed for the interactions. """
    l = list(set(list(itertools.product(arr, arr))))

    return [(c1.upper(),c2.upper(),cop) for c1,c2 in l if c1 != c2]


# In[6]:


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

