# -*- coding: utf-8 -*-
"""
Created on Sat Nov  5 07:32:51 2016

@author: Binay Prasai
Find Fraud transaction

"""
import pandas as pd
import numpy as np
import sys
import os

#Getting file names from arguments
arg_list = list(sys.argv)
input_batch = arg_list[1]
input_stream = arg_list[2]
outFile1 = arg_list[3]
outFile2 = arg_list[4]
outFile3 = arg_list[5]
outDir = 'paymo_output/' 
inDir = 'paymo_input/'

if os.path.exists(outDir)==0:
    os.mkdir(outDir)

'''
Getting information from batch_payment.csv. This is used to 
verify the status of a transaction.
'''
print('collecting history')
print('Reading file :',input_batch)
f = open(input_batch,'rb')
o = open('temp.txt','w') #I am temporarily writing a new file to avoid memory usage

#I couldnot directly read in a dataframe because all the rows are not data, some texts
for file in f:
    file = file.decode('utf-8')
    a = [int(s.strip()) for s in file.split(',') if s.strip().isdigit()]
    b = ','.join([np.str(x) for x in a])
    o.write(b+'\n')
f.close()       
o.close()

df_past = pd.read_csv('temp.txt',header=None,usecols=[0,1])  
df_past = df_past.drop_duplicates()
df_past = df_past.dropna(axis=0)
df_past = df_past.astype(int)
df_past.columns =[' id1',' id2']
                    
     
print('end collecting history')
#all the batch_payment information is put in a dataframe

#This module checks a degree of friendship between two ids
def check_link(a,b):
    #print(a,b)
    a_first_neighbors1 = set(list(df_past[' id2'][df_past[' id1']==a]))
    a_first_neighbors2 = set(list(df_past[' id1'][df_past[' id2']==a]))
    a_first_neighbors = a_first_neighbors1 | a_first_neighbors2
    if len(a_first_neighbors)==0: return 'beyond'
    
    
    #check feature 1 i.e. first degree friend
    #print(a_first_neighbors)
    if b in a_first_neighbors:
        return 'first'

    #if not first degree friend then check further : feature 2
    b_first_neighbors1 = set(list(df_past[' id2'][df_past[' id1']==b]))  #set helps removing duplicate ids
    b_first_neighbors2 = set(list(df_past[' id1'][df_past[' id2']==b]))
    b_first_neighbors = b_first_neighbors1 | b_first_neighbors2
    
    #check for second neighbors
    # a and b have level 2 link if a intersect b is non-zero
    a_fn_intersect_b_fn = a_first_neighbors & b_first_neighbors
    if len(a_fn_intersect_b_fn)!=0:
        return 'second'

    
    #if not second degree friend check for fourth :feature 3
    #2nd neighbors
    a_sec_neighbors = []
    for afn in a_first_neighbors:
        neighbors_of_afn1 = set(list(df_past[' id2'][df_past[' id1']==afn]))
        neighbors_of_afn2 = set(list(df_past[' id1'][df_past[' id2']==afn]))
        neighbors_of_afn = neighbors_of_afn1 | neighbors_of_afn2
        for i in neighbors_of_afn:
            a_sec_neighbors.append(i)
        #print(a_sec_neighbors)
    b_sec_neighbors = []
    for bfn in b_first_neighbors:
        neighbors_of_bfn1 = set(list(df_past[' id2'][df_past[' id1']==bfn]))
        neighbors_of_bfn2 = set(list(df_past[' id1'][df_past[' id2']==bfn]))
        neighbors_of_bfn = neighbors_of_bfn1 | neighbors_of_bfn2
        for i in neighbors_of_bfn:
            b_sec_neighbors.append(i)
    #print(set(a_sec_neighbors))  
    
    #Third degree friend : this could also be a case and still should be included in feature 3
    #print(b_sec_neighbors)
    a_sec_neighbors = set(a_sec_neighbors)
    b_sec_neighbors = set(b_sec_neighbors)
    a_sn_intersect_b_fn = a_sec_neighbors & b_first_neighbors
    if len(a_sn_intersect_b_fn)!=0: return 'third'
    a_fn_intersect_b_sn = a_first_neighbors & b_sec_neighbors
    if len(a_fn_intersect_b_sn)!=0: return 'third'
    
    #Fourth level link
    a_sn_intersect_b_sn = a_sec_neighbors & b_sec_neighbors
    if len(a_sn_intersect_b_sn) != 0: return 'fourth'
    
    # if none of the aboove case is satisfied the transaction is unverified ; beyond fourth degree friend
    return 'beyond'


#open 3 files for outputs
out1 = open(outFile1,'w')
out2 = open(outFile2,'w')
out3 = open(outFile3,'w')

    
#open stream_payment file to verify transaction
#this process is sequential and takes a lot of time
print('Checking transaction')
print('Reading file : ',input_stream)
fin = open(input_stream,'rb')   
fin.readline() #header

for line in fin:
    if len(line) > 0:    #check for emptylines
        line=line.decode('utf-8')
        line = line.strip().split(',') #to list
        line = [x.strip() for x in line]  #remove extraspace on list members
        #print(line)
        if len(line) > 2: #make sure we have transactions
            if line[1].isdigit() and line[2].isdigit():  #id1 and id2 to int
                x,y = int(line[1]),int(line[2]) 
                status = check_link(x,y)
                #print(x,y,status)
                if status=='first':
                    out1.write('trusted\n')
                    out2.write('trusted\n')
                    out3.write('trusted\n')
                elif status=='second':
                    out1.write('unverified\n')
                    out2.write('trusted\n')
                    out3.write('trusted\n')
                elif status=='third' or status=='fourth':
                    out1.write('unverified\n')
                    out2.write('unverified\n')
                    out3.write('trusted\n')
                else:
                    out1.write('unverified\n')
                    out2.write('unverified\n')
                    out3.write('unverified\n')
            
out1.close()    
out2.close()
out3.close()

print('End of the job')
