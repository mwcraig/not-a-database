from __future__ import division, print_function

import os

import numpy as np
import csv
import glob

from astropy.table import Table, Column, vstack

from astropy.coordinates import SkyCoord
from astropy import units as u
from astropy.coordinates import Angle

def __init__(self,tstuff):
	self.__stuff = tstuff

def assignID(file1,file2):
    """
    Preconditions: Expects 2 files read as astropy Tables. Files must have RA and Dec
    columns.
    Postconditions: Fills the DataNum column in the second file with the DataNum of 
    the closest RA/Dec match in the first file.
    """
    ra1 = file1['RA']
    dec1 = file1['Dec']
    
    #print(n_objects2)
    ra2 = file2['RA']
    dec2 = file2['Dec']

    #returns two catalogs comparing file2 to file 1
    c = SkyCoord(ra=ra1*u.degree, dec=dec1*u.degree)
    catalog = SkyCoord(ra=ra2*u.degree, dec=dec2*u.degree)
    idx, d2d, d3d = c.match_to_catalog_3d(catalog)
    #some of the matches are likely to be duplicates and not within a reasonable distance to be the same star

    #return an array of true's and false's where match is within specified range (2 arcsec)
    good_matches = d2d < 2*u.arcsec 

    #get all matches that are within 2 arcsec of the target
    idx2 = idx[good_matches] 

    #apply file1's dataname to file2's dataname at the indexs specified by idx2
    file2['DataNum'][idx2] = file1['DataNum'][good_matches] 
    #now have 2 files with the DataName column matching for stars whith RA/Dec close enough

    return file2

def sortFiles(files):
    """
    Preconditions: Expects a list of csv files that have not yet been read as tables
    Postconditions: Returns the longest file,list with the longest file removed. 
    All of the files have two columns added. The SourceFile column has the name of 
    the file. The DataNum column is filled for the longest file and has zeros for 
    the rest.
    """
    new_files = list(files)
    new_files2 = list(new_files) #duplicate list

    fileNames = []
    for file in new_files:
        base_name = os.path.basename(file)
        fileNames.append(base_name)
    
    ct = 0
    ind = ct
    file1 = Table.read(new_files[ct])
    #find the longest red file to use for assigning indexes
    for file in new_files:
        file2 = Table.read(file)
        if len(file2) > len(file1):
            file1 = file2
            ind = ct
        ct += 1

    #removes file1 from new_files
    new_files.pop(ind)
    new_files2.pop(ind)
    print(len(new_files))

    #imports file as numpy Table
    n_objects1 = len(file1)
    #adds a DataNum Column to the table with sequential values to be match to the rest of the files
    dataNum1_col = Column(data=range(1,n_objects1+1), name='DataNum')
    file1.add_column(dataNum1_col)
    #adds a SourceFile Column to the table
    fileName_col = Column(data=[fileNames[ind]]*n_objects1, name='SourceFile')
    file1.add_column(fileName_col)
    #print (ind)
    #print (file1['SourceFile'])
    #print (len(fileNames))
    del fileNames[ind]#remove file1 name from it's position in fileNames list
    print (len(fileNames))
    #print(n_objects1)
    
    #run through the rest of the files, adds Filename and DataNum column and assigns them DataNums concurrent with file1's
    ct = 0
    for file in new_files:
        cur_file = Table.read(file)
        #imports file as numpy Table
        file2 = Table.read(new_files2[ct])
        n_objects2 = len(file2)
        #adds a DataNum Column to the table with 0000 values to be matched to file1 values
        dataNum2_col = Column(data=[0000]*n_objects2, name='DataNum')
        cur_file.add_column(dataNum2_col)
        fileName_col = Column(data=[fileNames[ct]]*n_objects2, name='SourceFile')#
        cur_file.add_column(fileName_col)#
        
        new_files[ct] = assignID(file1,cur_file)
        ct+=1
    
    return file1,new_files

def FGroup(filename):
    """
    Preconditions: Must have the filter type letter as the last letter of the filename.
    Requires the directory location of the csv files
    Postconditions: Returns one big file with all files for each image added as rows.
    """
	
	files = glob.glob(filename)

	file1, files2 = sortFiles(files)

	#creates new csv file to pile all the new files onto
	bigFile = file1
	#and add all Rfiles to redFile 
	for file in files2:
	    #print(file.colnames) 
	    #print(bigFile.colnames)
	    bigFile = vstack([bigFile, file], join_type='exact')
	    #print(file['DataNum'])
	return bigFile


def GroupByFilter(FExt,object,filters = ['I','R','V','B'],target_dir = 'output'):
    """
    Preconditions: Must have the filter type letter as the last letter of the filename.
    Requires the directory location of the csv files and the name of the object being
    observed for naming the output file.  Can also take the filter types to look for
    as a list and the output directory to put the files in.
    Postconditions: Creates one csv file (named for observed object and filter) for each
    filter type with the csv files for each image with columns DataNum (matched by
    RA/Dec) and SourceFile.
    """
    try:
        os.mkdir(target_dir)
    except WindowsError as e:
        if 'Cannot create a file when that file already exists' in e.strerror:
            pass
        else:
            raise

	pattern = FExt + '\*{}.csv'

    # send all the files to FGroup for each filter
	for filter in filters:
		bigfile = FGroup(pattern.format(filter))

	#outputs table of located object's info in .csv format
	bigfile.write(os.path.join(target_dir,object+filter+'Filt.csv'))
