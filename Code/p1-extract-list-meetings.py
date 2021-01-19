import urllib.request
import re
from bs4 import BeautifulSoup
from dateutil.parser import parse
from urllib.request import urlopen, Request
import csv


#Dictionary of the months
month = {'January':1,'February':2,'March':3,'April':4,'May':5,'June':6,'July':7,'August':8,'September':9,'October':10,'November':11,'December':12}

def extract_date(sdate):
    """ Extracts a date from a given string by returning a tuple of int (day,month,year). """
    if(extract_number(sdate) == None ):
        return sdate
    
    m = re.findall('\d{4}|\d{2}|January|February|March|April|May|June|July|August|September|October|November|December|\d{1}',sdate)

    if(len(m)==0):
        d=0
    if(len(m)==5):
        d = (int(m[0]),month[m[1]],int(m[len(m)-1]))
    if(len(m)==4):
        d = (int(m[0]),month[m[2]],int(m[len(m)-1]))
    if(len(m)==3):
        if(m[0] in month.keys()):
            d=(m[1],month[m[0]],m[2])
        else :
            d = (m[0],month[m[1]],m[2])
    
    if(len(str(d[1])) == 1):
        mo = "0"+str(d[1])
    else:
        mo = str(d[1])
    if(len(str(d[0]))==1):
        day = "0"+str(d[0])
    else:
        day = str(d[0])

    d_str = str(d[2])+"-"+mo+"-"+day
    
    return d_str

def extract_number(sname):
    """"Extract digit from a given string and return an int."""
    for i in sname.split():

        if i.isdigit():
            return int(i) 

def compute_list(list_string):
    """ Help to compose and order the list. Returns an ordered, by date, list who contains all the meetings in list_string with their attributes. """
    list_cop = []

    for s in list_string:
        l = s.split('|')
        list_cop.append((extract_number(l[0]),extract_date(l[1]),l[2]))
        
    list_cop.sort(key=lambda a: a[0], reverse=False)

    return list_cop

def extract_details_meetings(soup, meeting_type):
    """ Extract for one meeting_type, all the corresponding issues. For each issue extract the issue number, the date, the html link. """
    detail_meetings = []
    meeting_num = 1
    for row in soup.find_all("tr"):
        for col in row.find_all('td'):
        
            #Detect a new meeting 
            if("Issue" in col.string):
                
                a = row.find_previous_sibling('tr')
                b= a.find_next('th')
                detail = []
                # Variable to help to detect the first issue 
                issue_start = 0
                # and not("BIS" in str(b))
                if("</h3>"+meeting_type in str(b)):
                    
                    date_td = col.find_next_sibling('td')
                    
                    while( "<a name=" not in str(date_td.find_next('tr'))):              
                
                        #extract issue number
                        issue = int(re.findall('\d+',col.string)[0])
                        
                        # define the issue type
                        if(issue - issue_start>1):
                            issue_type = 'First'
                        else:
                            issue_type = 'Issue'
                        
                        pdf_td = date_td.find_next_sibling('td')
                        
                        # extract html link
                        html_td = pdf_td.find_next_sibling('td')
                        html = 'https://enb.iisd.org'+html_td.find('a',href=True)['href']
                    
                        # extract date
                        s = date_td.string
                        date = extract_date(s)    
                        
                        #Check if at the end of the webpage and return the final 
                        #list otherwise continue to find new issues
                        if(pdf_td.find_next('tr') == None):
                            break
                        else:
                            col = pdf_td.find_next('tr').find_next('td')
                            date_td = col.find_next_sibling('td')
                            issue_start = issue
                       
                        # add the issue into the list
                        detail.append((issue,date,html,issue_type))
                    
                    # Handle case when we are at the end of the COP and we have the summary
                    if( "<a name=" in str(date_td.find_next('tr'))): 
                    #extract issue number
                        issue = int(re.findall('\d+',col.string)[0])
                        
                        pdf_td = date_td.find_next_sibling('td')
                    #extract html link
                        html_td = pdf_td.find_next_sibling('td')
                        html = 'https://enb.iisd.org'+html_td.find('a',href=True)['href']
                    
                    #extract date
                        s = date_td.string
                        date = extract_date(s)
                        detail.append((issue,date,html,'Summary'))
                    
                    if(pdf_td.find_next('tr') == None):
                            detail.append((issue,date,html,'Summary'))
                            detail_meetings.append(detail)
                            return detail_meetings
                    
                     
                    detail_meetings.append(detail)
                    meeting_num = meeting_num +1
    return detail_meetings

# COP 

def extract_list_cops(soup):
    """Extract the list of all the COPs from a webpage and return a list containing all the COPs with their number, date and place. """
    
    # find all the different COPs (not named the same way)
    
    #Case 1 :1, 2, 3, 4, 5, 6, 7, 8, 9
    list = soup.find_all(string=re.compile("COP"+"\s"+"\d"+"\s"+"."+"\s"))

    #Case 2 :10, 23, 24, 25
    list += soup.find_all(string=re.compile("COP"+"\s"+"[1-2][0-9]"+"\s"+"."+"\s"+"\d"))
    
    #Case 3 :11, 12, 13, 14, 15, 16, 20, 21 , 22
    list_2 = soup.find_all(string=re.compile("COP"+"\s"+"[1-2][0-9]"+"\s"+"."+"\s"+"CMP"+"\s"+"\d+"+"\s"))

    # Case 4 : 17, 18, 19
    list_3 = soup.find_all(string=re.compile("COP"+"\s"+"[1-2][0-9]"+"\s"+"."+"\s"+"CMP"+"\d+"+"\s"))

    # Case 4 : BIS 
    list_4 = [soup.find_all(string=re.compile("COP"+"\s"+"\d+"+"\s"+"BIS"))[0]]
    # Clean the lists to have all the same structure
    # Clean list_2
    for i in range(len(list_2)) :
        list_2[i] =  re.sub("- CMP"+"\s"+"."+".", '', list_2[i])

    # Clean list_3
    for i in range(len(list_3)) :
        list_3[i] =  re.sub("- CMP"+".", '', list_3[i])

    # Clean list_4
    for i in range(len(list_4)) :
        list_4[i] =  re.sub(" BIS"+".2", '', list_4[i])

    #combine all the lists
    list += list_2
    list += list_3
    list += list_4
   
    return compute_list(list)

# INC

def extract_list_incs(soup):
    """ Extract of all the INC meetings from a webpage and return a list containing all of them with their number, date and place """
    
    #Case 1 : 11 
    list = soup.find_all(string=re.compile("INC"+"\s"+"\d+"+"\s"))

    return compute_list(list)

# SB

def extract_list_sbs(soup):
    """Extract of all the SB meetings from a webpage and return a list containing all of them with their number, date and place."""
    

    #Case 1 : 1, 3, 7, 8, 10, 12, 13, 18, 20 ,22, 24, 26, 28, 30, 34, 36, 38, 40, 42, 44, 46, 48, 48-2, 50
    list_1 = soup.find_all(string=re.compile("SB"+"\s"+"\d+"+"\s"+"."+"\s"+"\d+"))
    
    #Case 2 : 4, 6
    list_2 = soup.find_all(string=re.compile("SB"+"\s"+"\d+"+"\s"+"-"+"\s"+"AG"+"."+"."+"\s"+"\d"+"...\d+"))
    
    #Case 3 : 5
    list_3 = soup.find_all(string=re.compile("SB"+"\s"+"\d+"+"\s"+"-"+"\s"+"AG"+".."+"\s"+"\d"+"............\d"))
    
    #Case 4 : 50 
    list_4 = soup.find_all(string=re.compile("SB"+"-..."))
    
    #Case 5 : 32
    list_5 = soup.find_all(string=re.compile("SB"+"\s"+"\d+"+"\s"+"- AWG..."))

    #Case 6 : 48-2
    list_6 = soup.find_all(string=re.compile("SB \d+-\d ....."))

    # Clean list_2
    for i in range(len(list_2)) :
        list_2[i] =  re.sub("- AG\d+ \d ", '', list_2[i])
    
    for i in range(len(list_3)) :
        list_3[i] =  re.sub("- AGBM \d . AG....", '', list_3[i])
    
    for i in range(len(list_4)) :
        list_4[i] =  re.sub("-", ' ', list_4[i])
    
    for i in range(len(list_5)) :
        list_5[i] =  re.sub(" . AWGs", '', list_5[i])
    
    for i in range(len(list_6)) :
        list_6[i] =  re.sub("SB 48-2", 'SB 48', list_6[i])

    list = list_1+list_2+list_3+list_4+list_5+list_6

    return compute_list(list)   

# IPCC

def extract_list_ipccs(soup):
    """ Extract of all the IPCC meetings from a webpage and return a list containing all of them with their number, date and place. """
    
    #Case 1 : 17, 18, 22, 24, 25, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 52
    list1 = soup.find_all(string=re.compile("IPCC-\d+ . "))

    for i in range(len(list1)) :
        list1[i] =  re.sub("-", ' ', list1[i])
    
    list2 = soup.find_all(string=re.compile("IPCC WG...."))
    
    for i in range(len(list2)) :

        list2[i] =  re.sub("WGIII", '3', list2[i])
        list2[i] =  re.sub("WGII", '2', list2[i])
        list2[i] =  re.sub("WGI", '1', list2[i])

    l = list1 + list2
    return compute_list(list1+list2)

# AGMB

def extract_list_agbms(soup):
    """ Extract of all the AGMB meetings from a webpage and return a list containing all of them with their number, date and place. """
  
    #Case 1 : 1, 2, 3, 6, 7
    list = soup.find_all(string=re.compile("AGBM \d+ . \d+")) 

    return compute_list(list)

# UNFCCC WS

def extract_list_unfcccs_ws(soup):
    """ Extract of all the UNFCC WS meetings from a webpage and return a list containing all of them with their number, date and place. """
    
    list = soup.find_all(string=re.compile("UNFCCC\sWS\s[A-Z]+\s.\s\d+"))
    list += soup.find_all(string=re.compile("UNFCCC\sWS\s[A-Z]+\s[A-Z]+\s.\s\d+"))
    list += soup.find_all(string=re.compile("UNFCCC\sWS\s\d+.*?\s.\s\d"))
    list += soup.find_all(string=re.compile("UNFCCC WS V&A.*?\s.\s\d+"))
    list += soup.find_all(string=re.compile("17-19 October 2005 . B"))

    separated = []   
    k = 1
    for l in list:
        sep = l.split("|")
        sep[0] = k
        sep[1] = extract_date(sep[1])
        k += 1
        separated.append(sep)

    return separated

def extract_list_unfcccs_tt(soup):
    """ Extract of all the UNFCC TT meetings from a webpage and return a list containing all of them with their number, date and place. """
    
    list = soup.find_all(string=re.compile("UNFCCC\sTT+\s[A-Z]+\s.\s\d+"))

    separated = []   
    k = 1
    for l in list:
        sep = l.split("|")
        sep[0] = k
        sep[1] = extract_date(sep[1])
        k += 1
        separated.append(sep)
    return separated

def extract_list_unfcccs_bppm(soup):
    """ Extract of all the UNFCC BPPM meetings from a webpage and return a list containing all of them with their number, date and place. """
    
    list = soup.find_all(string=re.compile("UNFCCC\s[A-Z]+\s.\s\d+"))

    separated = []   
    k = 1
    for l in list:
        sep = l.split("|")
        sep[0] = k
        sep[1] = extract_date(sep[1])
        k += 1
        separated.append(sep)
    return separated


def extract_list_unfcccs_syn(soup):
    """ Extract of all the UNFCC BPPM meetings from a webpage and return a list containing all of them with their number, date and place. """
    
    list = soup.find_all(string=re.compile("UNFCCC SYN-COOP WS\s.\s"))

    separated = []   
    k = 1
    for l in list:
        sep = l.split("|")
        sep[0] = k
        sep[1] = extract_date(sep[1])
        k += 1
        separated.append(sep)
    return separated

# ADP

def extract_list_adps(soup):
    """ Extract of all the ADP meetings from a webpage and return a list containing all of them with their number, date and place. """
    #Case 1 : 2, 2-10, 2-11, 2-4, 2-6, 2-8
    list = soup.find_all(string=re.compile("ADP \d......"))
    
    separated = []
    for l in list:
        sep = l.split("|")
        sep[0] = re.sub("ADP", '', sep[0])  
        sep[1] = extract_date(sep[1])
        separated.append(sep)
    return separated

# AWG

def extract_list_awgs_t1(soup):
    """ Extract of all the AWGs CCWG meetings from a webpage and return a list containing all of them with their number, date and place. """
    
    #Case 1 : 1, 7, 9, 11, 12, 14, 16, 17i
    list = soup.find_all(string=re.compile("AWGs CCWG\d..."))
    
    separated = []
    for l in list:
        sep = l.split("|") 
        sep[0] = re.sub("AWGs CCWG", '', sep[0]) 
        sep[1] = extract_date(sep[1])
        separated.append(sep)
    return separated

def extract_list_awgs_t2(soup):
    """ Extract of all the AWGs RCCWG meetings from a webpage and return a list containing all of them with their number, date and place. """
    #Case 1 : 7
    list = soup.find_all(string=re.compile("AWGs RCCWG\d ..."))
    separated = []
    for l in list:
        sep = l.split("|") 
        sep[0] = re.sub("AWGs RCCWG", '', sep[0])
        sep[1] = extract_date(sep[1])
        separated.append(sep)
    return separated

def extract_list_awgs_t3(soup):
    """ Extract of all the AWGLCA meetings from a webpage and return a list containing all of them with their number, date and place. """

    #Case 1 : 1, 2, 5
    list = soup.find_all(string=re.compile("AWGLCA \d ..."))
    
    separated = []
    for l in list:
        sep = l.split("|") 
        sep[0] = re.sub("AWGLCA", '', sep[0])
        sep[1] = extract_date(sep[1])
        separated.append(sep)
    return separated

def extract_list_awgs_t4(soup):
    """ Extract of all the AWGLCA meetings from a webpage and return a list containing all of them with their number, date and place. """
    #Case 1 : 4   
    list = soup.find_all(string=re.compile("AWG-\d..."))

    separated = []
    for l in list:
        sep = l.split("|") 
        sep[0] = re.sub("AWG-", '', sep[0])
        sep[1] = extract_date(sep[1])
        separated.append(sep)

    return separated

# TECHWork

def extract_list_tech_work(soup):
    """ Extract of all the Tech-Work meetings from a webpage and return a list containing all of them with their number, date and place. """
    #Case 1 :    
    list = soup.find_all(string=re.compile("Tech-Work\s.\s\d+"))

    separated = []
    k=1
    for l in list:
        sep = l.split("|") 
        sep[0] = re.sub("Tech-Work", str(k), sep[0])
        k +=1
        sep[1] = extract_date(sep[1])
        separated.append(sep)

    return separated

# LULUCF

def extract_list_lulucf(soup):
    """ Extract of all the LULUCF meetings from a webpage and return a list containing all of them with their number, date and place. """
    #Case 1 :    
    list = soup.find_all(string=re.compile("LULUCF\s.\s\d+"))

    separated = []
    k=1
    for l in list:
        sep = l.split("|")
        sep[0] = re.sub("LULUCF", str(k), sep[0])
        k +=1
        sep[1] = extract_date(sep[1])
        separated.append(sep)

    return separated

# SOGE

def extract_list_soge(soup):
    """ Extract of all the SOGE meetings from a webpage and return a list containing all of them with their number, date and place. """
    #Case 1 :    
    list = soup.find_all(string=re.compile("SOGE\s.\s\d+"))

    separated = []
    k=1
    for l in list:
        sep = l.split("|")
        sep[0] = re.sub("SOGE", str(k), sep[0])
        k +=1
        sep[1] = extract_date(sep[1])
        separated.append(sep)

    return separated

# CCOM

def extract_list_ccom(soup):
    """ Extract of all the CCOM meetings from a webpage and return a list containing all of them with their number, date and place. """
    #Case 1 :    
    list = soup.find_all(string=re.compile("CCOM\d\s.\s\d+"))

    separated = []
    k=1
    for l in list:
        sep = l.split("|")
        sep[0] = re.sub("CCOM", str(k), sep[0])
        k +=1
        sep[1] = extract_date(sep[1])
        separated.append(sep)

    return separated


# INTER-REGIONAL WS

def extract_list_inter(soup):
    """ Extract of all the INTER-REGIONAL WS meetings from a webpage and return a list containing all of them with their number, date and place. """
    #Case 1 :    
    list = soup.find_all(string=re.compile("INTER-REGIONAL WS\s.\s\d+"))

    separated = []
    k=1
    for l in list:
        sep = l.split("|")
        sep[0] = re.sub("INTER-REGIONAL WS", str(k), sep[0])
        k +=1
        sep[1] = extract_date(sep[1])
        separated.append(sep)

    return separated

# CGE WS

def extract_list_cge_ws(soup):
    """ Extract of all the CGE WS meetings from a webpage and return a list containing all of them with their number, date and place. """
    #Case 1 :    
    list = soup.find_all(string=re.compile("CGE WS\s.\s\d+"))

    separated = []
    k=1
    for l in list:
        sep = l.split("|")
        sep[0] = re.sub("CGE WS", str(k), sep[0])
        k +=1
        sep[1] = extract_date(sep[1])
        separated.append(sep)

    return separated


# TECH WS

def extract_list_tech_ws(soup):
    """ Extract of all the TECH WS meetings from a webpage and return a list containing all of them with their number, date and place. """
    #Case 1 :    
    list = soup.find_all(string=re.compile("TECH WS\s.\s\d+"))

    separated = []
    k=1
    for l in list:
        sep = l.split("|")
        sep[0] = re.sub("TECH WS", str(k), sep[0])
        k +=1
        sep[1] = extract_date(sep[1])
        separated.append(sep)

    return separated

# Combine all type of meetings

def combine_information_meetings(soup, meeting_type, extract_type):
    """Combine information for each issue of each meeting """
    list_meetings = extract_type(soup)
    print(len(list_meetings))
    #print(list_meetings)
    list_meetings_information = extract_details_meetings(soup,meeting_type)
    print(len(list_meetings_information))

    total = []

    for i in range(len(list_meetings)):

        (number,date,place) = list_meetings[i]
        list_meeting = list_meetings_information[i]
        
        for x in list_meeting:
            total.append((meeting_type,number,date,place,x[0],x[1],x[2],x[3]))
    return total

def computes_all_list_meetings(soup):
    """ Compute all combine all the lists of all the meetings with their issues. """

    list_sb = combine_information_meetings(soup,'SB', extract_list_sbs)

    list_adp = combine_information_meetings(soup,'ADP', extract_list_adps)
    list_agbm = combine_information_meetings(soup,'AGBM', extract_list_agbms)
    list_awg = combine_information_meetings(soup,'AWGs CCWG', extract_list_awgs_t1)
    list_awg += combine_information_meetings(soup,'AWGs RCCWG', extract_list_awgs_t2)
    list_awg += combine_information_meetings(soup,'AWGLCA', extract_list_awgs_t3)
    list_ipcc = combine_information_meetings(soup,'IPCC', extract_list_ipccs)
    list_awg += combine_information_meetings(soup,'AWG', extract_list_awgs_t4)
    list_tech_work = combine_information_meetings(soup,'Tech-Work', extract_list_tech_work)
    list_lulucf = combine_information_meetings(soup,'LULUCF', extract_list_lulucf)
    list_soge = combine_information_meetings(soup,'SOGE', extract_list_soge)
    list_inc = combine_information_meetings(soup,'INC', extract_list_incs)
    list_cop = combine_information_meetings(soup,'COP', extract_list_cops)
    list_unfccc_ws = combine_information_meetings(soup,'UNFCCC WS', extract_list_unfcccs_ws)
    list_unfccc_tt = combine_information_meetings(soup,'UNFCCC TT', extract_list_unfcccs_tt)
    list_unfccc_bppm = combine_information_meetings(soup,'UNFCCC BPPM', extract_list_unfcccs_bppm)
    list_unfccc_syn = combine_information_meetings(soup,'UNFCCC SYN-COOP', extract_list_unfcccs_syn)
    list_unfccc = list_unfccc_bppm+ list_unfccc_syn+ list_unfccc_tt+ list_unfccc_ws
    list_ccom = combine_information_meetings(soup,'CCOM', extract_list_ccom)
    list_inter = combine_information_meetings(soup,'INTER-REGIONAL WS', extract_list_inter)
    list_cge = combine_information_meetings(soup,'CGE WS', extract_list_cge_ws)
    list_tech_ws = combine_information_meetings(soup,'TECH WS', extract_list_tech_ws)
    
    list_m = list_unfccc+ list_inc+ list_cop+ list_sb+ list_adp+ list_agbm+ list_ipcc+ list_awg+ list_soge+ list_lulucf+ list_tech_work+ list_ccom+ list_inter+ list_cge+ list_tech_ws

    list_m.sort(key=lambda a: a[4], reverse=False)
    return list_m

def write_list_meetings(list_meetings):
    """ Generate list_meetings.csv file."""
    with open('Files/list-meetings.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        #header
        writer.writerow(('meeting_type','reference','date','location','issue_number','issue_date','html_link','issue_type'))
        #list
        writer.writerows(list_meetings)





def main():
    """ Create a list of all meetings with their informations """
    # Download the specific page to be able to extract information from it 
    r = Request('https://enb.iisd.org/enb/vol12/', headers={'User-Agent': 'Mozilla/5.0'})
    page = urlopen(r).read()
    soup = BeautifulSoup(page)
    list_meetings = computes_all_list_meetings(soup)
    write_list_meetings(list_meetings)



if __name__ == "__main__":
    main()
