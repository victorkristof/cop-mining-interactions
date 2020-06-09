import urllib.request
import re
from bs4 import BeautifulSoup
from dateutil.parser import parse
import csv
import pandas as pd
import requests
import nltk
from nltk import sent_tokenize
from itertools import combinations  
import itertools
from nltk import word_tokenize
from nltk.tag import StanfordNERTagger
from nltk.tokenize import MWETokenizer
from p2_extract_text_issue import extract_paragraphes_from_issue, extract_sentences
from p3_extract_interventions import extract_from_csv_list_issues
import argparse
import collections
from collections import Counter
import itertools
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')


def tokenize_sentence(sentence, country):
    """Split the sentence in a way that the entities are together and will be able to be detected."""
    # Extract list entities
    list_entities = ENTITIES
    list_entities = [s.replace('class="textstory"','') for s in list_entities]
    
    tokens_entities = [l.split(' ') for l in list_entities]
    if(country):
        tokens_entities.append(['on','behalf','of'])
        
        tokens_entities.append(['for'])
        tokens_entities.append(['US','$'])
        tokens_entities.append(['speaking','for'])
    else :
        tokens_entities.append(['speaking','for','the'])
        tokens_entities.append(['concerns', 'of', 'the'])
        tokens_entities.append(['concerns', 'of'])
        tokens_entities.append(['speaking','for'])
        tokens_entities.append(['on','behalf','of','the'])
        tokens_entities.append(['spoke','with'])
        tokens_entities.append(['on','behalf','of'])
        tokens_entities.append(['for','the'])
        tokens_entities.append(['US','$'])
    tokens_entities.append(['for', 'a', 'number','of', 'members' ,'of' ,'the'])
    tokens_entities.append(['for', 'several'])
    tokens_entities.append(['speaking','on','behalf', 'of', 'the'])  
    tokens_entities.append(['supported','by'])
    tokens_entities.append(['opposed','by'])
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
    tokens = [clean_tp(token) for token in tokens]

    return tokens

def clean_tp(sentence):
    """ Clean the sentence by removing special char."""
    s = sentence.replace("\r\n\s\s+"," ")
    s = s.replace("\r\n"," ")
    s = s.replace('\t','')
    s = s.replace("\s\s+"," ")
    s = s.replace("\\."," ")
    s = s.replace("\\r\\n"," ")
    p = re.compile(r'<.*?>')
    return p.sub('', s)

def make_title(entities):
    """ Function that write entities in title case. """
    new_entities = []
    for e in entities:
        e = e.replace('\n','')
        splited = e.split(' ')
        
        if(len(splited) == 1 or len(splited) == 2):
            new_entities.append(e.title())
        else:

            s =''
            for i in range(len(splited)):
                if(splited[i] == 'AND' or splited[i] == 'OF' or splited[i] == 'THE'):
                    s += splited[i].lower() + ' '
                else:
                    s += splited[i].title() + ' '

            s = s[:-1]

            new_entities.append(s)
    return new_entities

def extract_s2e_issue_number(issue_number):
    """ Extract all the sentence with at least one party inside. """
    #List sentences
    #paragraphes = c1.extract_paragraphes_from_issue(number)
    p = extract_paragraphes_from_issue(issue_number)
    sentences = extract_sentences(p, False, issue_number)
    #Create list that wil contain all the sentences with at least two entities
    sentences_s2 = []

    for i, s in enumerate(sentences):
    #Split line into words with tokenizer to detect entity
        tokens = tokenize_sentence(s,False)

        if(len(set(tokens).intersection(set(ENTITIES)))> 1):
            sentences_s2.append(s)
    return sentences_s2

def find_pos_tagged_s2e(list_s2e):
    """ Use NLTK to pos_tag all the sentences from list_s2e and return a list of all the sentences pos_tagged"""
    pos_tagged = []
    for s in list_s2e:
        s = s.replace('\\t','')
        s = re.sub(r'\([^)]*\)', '', s)
        tokens = tokenize_sentence(s, False)

        pos_tagged.append(nltk.pos_tag(tokens))  
   
    return pos_tagged

def find_patterns(pos_tagged, list_tags):  
    """ Find all the pattern in list_tags needed in sentences pos_tagged. """
    groups = [x[0] for x in pos_tagged[0] if x[1] in list_tags]

    return groups

def find_1g(groups): 
    """ Find all the entities in the groups. Return a list of entities"""
    groups = [g.replace(',','') for g in groups]
    entities = set(groups).intersection(set(ENTITIES))
    return list(entities)

def find_2g(groups, opp):
    """ Find all the entities for each groups. Return two lists of entities"""

    index = groups.index(opp)

    g1 = find_1g(groups[:index])
    g2 = find_1g(groups[index +1:])

    return g1, g2

def detect_groups_cooperations(groups):
    """ Return one or two groups with only entities and the original sentence. Return a list with one or two list"""

    # Case 1 : Opposition between two groups
    if(set(OPPOSITION_LINKS).intersection(set(groups)) != set()):
        opp = list(set(OPPOSITION_LINKS).intersection(set(groups)))[0]
        
        g1, g2 = find_2g(groups, opp)
        return [g1, g2], [opp]

    # Case 2 : Only support
    else:
        g1 = find_1g(groups)
        return [g1], []

def find_coalitions(groups, sentence, opposition_index):
    """ Remove all the parties in groups that speak for a coalition, return list group updated if the case. """
    group_updates = []

    new_tokens = []

    for group in groups: 
        set_group = set(group)

        truples_c = []
        token =tokenize_sentence(sentence,False)

        links = ['for the','for several','on behalf of the','speaking for the','on behalf of','for','speaking for','for a number of members of the', 'speaking on behalf of the']

        if(set(token).intersection(set(links)) != set()):

            for i in range(len(token)-2):

                if(token[i] in group and token[i+1] in links and token[i+2] in PARTY_GROUPINGS):

                    set_group.remove(token[i])

                    if(len(opposition_index) !=0):
                        s = sentence[:opposition_index[0]]
                        v = sentence[opposition_index[0]:]
                        s = s.replace(token[i+1],'').replace(token[i],'')
                        u = ' '
                        sentence = u.join([s,v])
                    else:
                        sentence = sentence.replace(token[i+1],'').replace(token[i],'')
                        

        group_updates.append(list(set_group))
        #print(group_updates)
    return group_updates, sentence

def rSubset(arr, cop): 
    """ function that return all the tuples needed for the interactions. """
    l = list(set(list(itertools.product(arr, arr))))

    return [(c1.upper(),c2.upper(),cop) for c1,c2 in l if c1 != c2]

def remove_from_concern_of(groups, sentence):
    """ Filter that remove all entities when they are mentioned with the pattern from or concern of. """
    group_updates = []

    for group in groups: 
        truples_c = []
        token =tokenize_sentence(sentence,False)

        links = ['from','from the','concerns of the','concern of']


        if(set(token).intersection(set(links)) != set()):
            
            for i in range(len(token)-2):
                if((token[i+1] in PARTIES or token[i+1] in PARTY_GROUPINGS) and token[i] in links):
                    if(token[i+2] in PARTIES or token[i+2] in PARTY_GROUPINGS):
                        
                        group = [g for g in group if g != token[i+2]]
                        sentence = sentence.replace(token[i+2],'')
                    group = [g for g in group if g != token[i+1]]

                    sentence = sentence.replace(token[i+1],'')

        group_updates.append(group)
        
    
    return group_updates, sentence

def behalf_of(sentence, group_cooperation, link):
    """Function that find all the interaction of type "behalf". """
    token =tokenize_sentence(sentence, True)
    index = token.index(list(link)[0])

    country_A = set(token[:index]).intersection(set(group_cooperation))

    countries_B = set(group_cooperation).difference(set(country_A))
    tuples = []  
    for x in countries_B:

        tuples.append((list(country_A)[0].upper(),x,['behalf','cooperation']))
        
    tuples += rSubset(list(countries_B),['agreement','cooperation'])

    return sorted(tuples)

def supported_by(sentence, group_cooperation, link ):
    """Function that find all the interaction of type "support". """
    token =tokenize_sentence(sentence, True)
    index = token.index(list(link)[0])

    country_A = set(token[:index]).intersection(set(group_cooperation))
    countries_B = set(group_cooperation).difference(set(country_A))
    tuples = []  

    for x in countries_B:
        
        tuples.append((x,list(country_A)[0].upper(),['support','cooperation']))
        
    tuples += rSubset(list(countries_B),['agreement','cooperation'])

    return sorted(tuples)

def check_link(link, sentence, group_cooperation):
    """Verify that there is entities in both sides of the link"""
    token =tokenize_sentence(sentence, True)

    index = token.index(list(link)[0])
    country_A = set(token[:index]).intersection(set(group_cooperation))
    country_B = set(token[index:]).intersection(set(group_cooperation))
    return country_A != set() and country_B != set()

def coop(sentence, group_cooperation):
    """Function that find all the interaction of type "cooperation" and classify them. """
    
    token =tokenize_sentence(sentence, True)

    behalf = ['speaking for','on behalf of']
    behalf = set(token).intersection(set(behalf))

    support = ['supported by','supported by the']
    support = set(token).intersection(set(support))


    tuples = []
    cooperation = []
    if(behalf != set()and check_link(behalf, sentence, group_cooperation)):
        return behalf_of(sentence, group_cooperation, behalf)
    else: 
        if(support != set() and  check_link(support, sentence, group_cooperation)):
            return supported_by(sentence, group_cooperation, support)

        else :
            return rSubset(group_cooperation,['agreement','cooperation'])

def opposed_by(sentence, group_cooperation, link):
    """ Function that find all the interactions of type "opposition" ."""
    token =tokenize_sentence(sentence, True)
    index = token.index(list(link)[0])
    countries_A = group_cooperation[0]
    countries_B = group_cooperation[1]

    # Create tuples for the opposition
    tuples = list(itertools.product(countries_A, countries_B))

    tuples = [(c2.upper(),c1.upper(),['opposition']) for c1,c2 in tuples] 



    #Add cooperation between both groups
    splited = sentence.split(list(link)[0])
    if(len(countries_A)!=1):
        tuples_A = coop([splited[0]], countries_A)
        tuples += tuples_A
    
    if(len(countries_B)!=1):
        tuples_B = coop([splited[1]], countries_B)
        tuples += tuples_B
    
    return tuples

def criticized_by(sentence, group_cooperation, link):
    """ Function that find all the interactions of type "criticism" ."""
    token =tokenize_sentence(sentence, True)
    index = token.index(list(link)[0])
    countries_A = list(set(group_cooperation[0]).intersection(set(token[:index])))
    countries_B = list(set(group_cooperation[0]).intersection(set(token[index+1:])))
    
    # Create tuples for the opposition
    tuples = list(itertools.product(countries_A, countries_B))
    tuples = [(c1.upper(),c2.upper(),['criticism']) for c1,c2 in tuples]

    #Add cooperation between both groups
    splited = sentence[0].split(list(link)[0])
    
    if(len(countries_A)!=1):
        tuples_A = coop(splited[0], countries_A)
        tuples += tuples_A
    
    if(len(countries_B)!=1):
        tuples_B = coop(splited[1], countries_B)
        tuples += tuples_B
    
    return tuples 

def remove_double_s(sentences):
    """ Filter that try to find if one sentence contain two entities but they are not related. """
    tags_wanted = ['VBD','MD']
    words_wanted = ['and']
    s2 = []
    sentences_filtered = []
    s_to_filter = []
    s_filtered = []
    set_sentences = set(sentences)
    for s in sentences:
        pos_tagged = find_pos_tagged_s2e([s])

        
        
        filtered = [x for x in pos_tagged[0] if x[0] in ENTITIES or x[0] in words_wanted or x[1] in tags_wanted]
        filtered_only_VBD = [x for x in pos_tagged[0] if x[0] in PARTIES or x[0] in words_wanted or x[1]== 'VBD']


        if(len(filtered_only_VBD)>= 5):
            for i in range(len(filtered_only_VBD)-4):
                if( filtered_only_VBD[i][0] in ENTITIES and filtered_only_VBD[i+1][1]=='VBD' and filtered_only_VBD[i+2][0] == 'and' and  filtered_only_VBD[i+3][0] in PARTIES and  filtered_only_VBD[i+4][1]in tags_wanted and s in set_sentences):

                    s_to_filter.append((s,filtered_only_VBD[i+1]))
                    set_sentences.remove(s)

        if(len(filtered)>= 5):
            for i in range(len(filtered)-4):
                if( filtered[i][0] in ENTITIES and filtered[i+1][1] in tags_wanted and filtered[i+2][0] == 'and' and  filtered[i+3][0] in ENTITIES and  filtered[i+4][1]in tags_wanted and s in set_sentences):

                    s_to_filter.append((s,filtered[i+1]))
                    set_sentences.remove(s)

    sentences = list(set_sentences) 
    for s in s_to_filter:

        index = s[0].index(s[1][0])
        s1 = s[0][:index]
        s2 = s[0][index+1:]
        sentences.append(s1)
        sentences.append(s2)
    
    return list(set(sentences))

def remove_on_99s_from_programme(sentences):
    """ Filter that remove entities that are related to some patterns that are not interactions. """
    set_sentences = set(sentences)
    s_to_filter = []
    s_filtered = []
    note = ['92s','Programme','proposed by the','proposed by']
    for s in sentences:

        pos_tagged = find_pos_tagged_s2e([s])[0]

      
        for i in range(len(pos_tagged)-1):

            if(pos_tagged[i][0] == 'on' and pos_tagged[i+1][0] in ENTITIES and s in set_sentences):

                s_to_filter.append((s,pos_tagged[i+1][0]))
                set_sentences.remove(s)

            if((pos_tagged[i+1][0] == '92s' or pos_tagged[i+1][0] == 'Programme') and pos_tagged[i][0] in ENTITIES and s in set_sentences):

                s_to_filter.append((s,pos_tagged[i][0]))
                set_sentences.remove(s)
            
            if((pos_tagged[i][0] == 'proposed by the' or pos_tagged[i+1][0] == 'proposed by') and pos_tagged[i+1][0] in ENTITIES and s in set_sentences):
  
                s_to_filter.append((s.replace (pos_tagged[i+1][0],''),pos_tagged[i+1][0]))
                set_sentences.remove(s)


    x = ' '
    for s in s_to_filter:
        token = tokenize_sentence(s[0],False)
        tokens = []
        for i in range(len(token)-1):
            if(token[i] not in note and  not (token[i+1]==s[1])):
                tokens.append(token[i])

        #s_f = s[0].replace(s[1],'')
        s_f = x.join(tokens)
        s_filtered.append(s_f)

 
    s_filtered += list(set_sentences)
    
    return list(set(s_filtered))

def check_interaction(group_cooperation):
    """ Function that return if there is or not an interaction. """
    return len(group_cooperation) == 2 or len(group_cooperation[0])>1

def check_doubles(sentence, group_cooperation):
    """ Filter that find if one entity is mentioned twice in two different manner and we should not count and interaction between them. """
    gc_new = []
    
    for g in group_cooperation:

        g_upper = [e.upper() for e in g]
        g_title = [e.title() for e in g]
        if(len(set(g_upper)) != len(g)):
            gc_new.append(list(set(g).difference(set(g_title))))
            removed = list(set(g).intersection(set(g_title)))
            for r in removed:
                sentence = sentence.replace(r,'')
        else:
            gc_new.append(g)
    return gc_new, sentence

def find_inversions(sentences):
    """ Filter tht try to detect sentence that have been inverted (verb - entity - entity) and change it to be able to detect the interaction. """
    set_sentences = set(sentences)

    s_to_filter = []
    s_filtered = []
    verbs_int =['Supported','Opposed']
    for s in sentences:

        pos_tagged = find_pos_tagged_s2e([s])[0]

        for i in range(len(pos_tagged)-3):

            if(pos_tagged[i][0] in verbs_int and pos_tagged[i+1][0] == 'by' and pos_tagged[i+2][0] in ENTITIES and pos_tagged[i+3][0] in ENTITIES):

                s_to_filter.append((s,pos_tagged[i][0],pos_tagged[i+1][0],pos_tagged[i+2][0],pos_tagged[i+3][0]))

                set_sentences.remove(s)
        
        ## The EU ...
        for i in range(len(pos_tagged)-4):

            if(pos_tagged[i][0] in verbs_int and pos_tagged[i+1][0] == 'by' and pos_tagged[i+2][0] == 'the' and pos_tagged[i+3][0] in ENTITIES and pos_tagged[i+4][0] in ENTITIES):

                s_to_filter.append((s,pos_tagged[i][0],pos_tagged[i+1][0],pos_tagged[i+3][0],pos_tagged[i+4][0]))
                set_sentences.remove(s)
        
    
    for s in s_to_filter:
    
        sentence = s[0]

        verb = s[1]
        by = s[2]
        c_a = s[3]
        c_b = s[4]
        s_f =sentence.replace(by,'').replace(c_a,'').replace(c_b,'').replace(verb,'')
        s_f = c_b + " "+ verb.lower() + " " + by + " " + c_a + " " + s_f
        s_filtered.append(s_f)

 
    s_filtered += list(set_sentences)

    return list(set(s_filtered))

def remove_representent(pos_tagged):
    """ Remove all the entities mentioned when it is related to a presentant and so not a interaction. """
    entities_repr = []
    for i in range(len(pos_tagged)-2):
        if(pos_tagged[i][1] =='NNP' and pos_tagged[i][0] not in ENTITIES and pos_tagged[i+1][1] == 'IN' and pos_tagged[i+2][0] in ENTITIES):
            entities_repr.append(pos_tagged[i+2])
    return [[g for g in pos_tagged if g not in entities_repr]]

def write_line(issue_number, x):
    """ Function that help to whrite a line wit all the interactions. """
    """  'behalf'	 'support'	 'spokewith'	 'agreement'	 'delay'	 'opposition'	 'criticism'	 'cooperation'"""
    dict_interactions = {'behalf' : 0, 'support' : 0, 'agreement':0 , 'opposition':0,'criticism' :0, 'cooperation':0}
    for int in x[2]:
        dict_interactions[int] = 1
    values = list(dict_interactions.values())

    v = []
    v.append(issue_number)
    v.append(x[0])
    v.append(x[1])
    v += values
    v.append(x[3])

    #v.append(x[4])
    return  tuple(i for i in v) 

def add_point(sentences):
    """ Split special sentence where there is an sentence ta finish with ." ."""
    
    new_sentences = []
    index = -1
    for s in sentences:
        
        pos_tagged = find_pos_tagged_s2e([s])[0]

        for i in range(len(pos_tagged)-1):
            if(pos_tagged[i][0] == '”' and pos_tagged[i+1][0] in ENTITIES):

                index = pos_tagged[i+1][0]
        if(index != -1):

            splited = s.split(index)
            s1= splited[0]

            s2 = splited[1]+' ' + index

            new_sentences.append(s1)
            new_sentences.append(s2)
            index = -1
        else:
            new_sentences.append(s)
    return new_sentences  

def clean_sentence(sentence):
    """ Try to remove special character still present from the webscrapping. """

    sentence_original = re.sub('class="ENB-Body" align="justify"','',sentence)
    sentence_original = re.sub('>','',sentence_original)
    sentence_original = re.sub('class="textstory"','',sentence_original)

    return sentence_original     

def create_df(cooperations, issue_number):
    """ Combine all the information to create the dataframe. """
    cooperations = [i for i in cooperations if len(i) == 12]
    if(len(cooperations)>0):
        ca = [x[1].upper() for x in cooperations]
        cb = [x[2].upper() for x in cooperations]
        id_ca = [x[10] for x in cooperations]
        id_cb = [x[11] for x in cooperations]
        behalf = [x[3] for x in cooperations]
        support = [x[4] for x in cooperations]
        agreement =[x[5] for x in cooperations]
        opposition =[x[6] for x in cooperations]
        criticism =[x[7] for x in cooperations]
        cooperation =[x[8] for x in cooperations]
        sentences = [x[9] for x in cooperations]
        dict_issue = {'type': 'generated','issue': cooperations[0][0],'id_ca':id_ca,'id_cb':id_cb,'Country A':ca, 'Country B': cb, 'behalf':behalf,'support':support,'agreement':agreement,'opposition':opposition,'criticism':criticism,'cooperation':cooperation,'sentences': sentences}
    else:
        dict_issue = {'type': 'generated','issue': issue_number,'id_ca':1111,'id_cb':1111, 'behalf':[],'support':[],'agreement':[],'opposition':[],'criticism':[],'cooperation':[],'sentences':[]}

    df = pd.DataFrame(dict_issue)
    return df

def extract_interactions(issue_number):
    """ Function that combine all the filters to find all the interaction for one specific issue. """
    
    sentences = extract_s2e_issue_number(issue_number)
    sentences = [re.sub('class="ENB-Body" align="justify"','',x) for x in sentences]
    #print(repr(sentences[0]))
    

    # Filters to remove to pre-procss sentences to be able to detect if there is an interaction or not
    sentences = remove_double_s(sentences)

    sentences = remove_on_99s_from_programme(sentences)
    
    sentences = find_inversions(sentences)
    
    sentences = add_point(sentences)


    interactions_ = []
    sentences_int = []

    for sentence_original in set(sentences):
        
        interactions = []
        sentence_original = clean_sentence(sentence_original)

        # Use NLTK to do pos tagging the sentence and filter the tags to keep only the one wanted
        pos_tagged = find_pos_tagged_s2e([sentence_original])

        tags_filtered1 = remove_representent(pos_tagged[0])
        
        tags_filtered = find_patterns(tags_filtered1, LIST_TAGS)

        # Create the group of entities that interacts in the sentence. Use filters to keep the correct one
        group_cooperation, opp = detect_groups_cooperations(tags_filtered)

        if(len(opp)!=0):
            opposition_index = [sentence_original.index(opp[0])]
        else:
            opposition_index = []
        group_cooperation, sentence  = find_coalitions(group_cooperation, sentence_original, opposition_index)

        group_cooperation, sentence = remove_from_concern_of(group_cooperation ,sentence)
        
        
        group_cooperation, sentence = check_doubles(sentence, group_cooperation)
        
        # Check if interactions after all the filters
        interaction_bool = check_interaction(group_cooperation)

        if(interaction_bool):
    
            # Try to find an opposition link 
            token = tokenize_sentence(sentence, True)
            opposition = ['opposed by','while','opposed by the']
            opposition = set(token).intersection(set(opposition))

            # Try to find an criticism link
            criticism = ['criticized']
            criticism= set(token).intersection(set(criticism))
            

            # Check if there is an opposition in the sentence
            if(opposition != set() and len(group_cooperation) ==2):
                interactions += opposed_by(sentence, group_cooperation, opposition)
            else:
                # Check if there is a criticism in the sentence
                if(criticism != set() and check_link(criticism, sentence, group_cooperation[0])):
                    interactions += criticized_by(sentence, group_cooperation, criticism)         
                else :
                    # Find all the cooperations
                    interactions += coop(sentence, group_cooperation[0])

 
            
            # Add the interactions in the list of all the interactions and the sentence realated to it if there is at least one interaction  
            if(len(interactions)!= 0):
                s = str(sentence_original)
                sentences_int.append(sentence_original)     
                interactions = [(x[0],x[1],x[2],s) for x in interactions]
                interactions_ += interactions

    interactions_ = [ write_line(issue_number, x) for x in interactions_]
    return interactions_

def write_interactions_issue(interactions, s):
    """ Write interaction for a specific issue number. """

    with open(s, "w", newline='') as file:
        writer = csv.writer(file)
        #header
        writer.writerow(('issue_number','Country A','Country B','behalf','support','agreement','opposition','criticism','cooperation','sentence'))
        for oc in interactions:

            writer.writerow(oc)

ENTITIES = list(set([s.replace('\n','') for s in list(open('Files/entities_interactions.txt'))] + make_title(list(open('Files/entities_interactions.txt')))+ ['Saint Vincent and the Grenadines','Republic of Korea','St. Lucia']))
COALITIONS = []
SUPPORTS_LINKS = ['with','and','for the','on behalf of the','supported by','speaking for the','for several']
OPPOSITION_LINKS= ['opposed by','while','opposed by the']
LIST_TAGS = ['IN', 'CC', 'NN', 'NNP', 'JJ','NNPS','MD','VBP','VB','VBZ','VBD','RB','VBN','PRP', 'NNS']
PARTY_GROUPINGS = sorted(set([s.replace('\n','').upper() for s in list(open('Text/party_grouping_clean.txt'))] + [s.replace('\n','').title() for s in list(open('Text/party_grouping_clean.txt'))] + [s.replace('\n','') for s in list(open('Text/party_grouping_clean.txt'))]))

PARTIES = sorted(set(ENTITIES).difference(set(PARTY_GROUPINGS)))


def extract_interactions_range(list_issue):
    interactions = []
    issues_generated = issues = extract_from_csv_list_issues('Files/list_meetings.csv')
    for x in list_issue:
        if(x in issues_generated):
            interactions +=  extract_interactions(x)

        else:
            print('Issue number '+ str(x)+' not in the list of issue extracted')
    
    s = "Files/interactions-issues-"+ str(list_issue[0]) +"-" + str(list_issue[-1])+".csv"
    write_interactions_issue(interactions, s)

# Main 

def main():

    """ Extract all interactions. """
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
        extract_interactions_range(list_issues)
    else:
        s = "Files/interactions-issues-"+ str(args.unique)+".csv"
        interactions = extract_interactions(args.unique)
        write_interactions_issue(interactions, s)
    

if __name__ == "__main__":
    main()
