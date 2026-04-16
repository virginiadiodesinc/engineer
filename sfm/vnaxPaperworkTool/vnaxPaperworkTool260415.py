#Creates VNAX Folders and populates.
#inputs: SN1, SN2, and WO name.
#creates folders nested in "V:\\Production\\Ship&Receive\\Shipped User Guide\\25_VNA extenders\\"
#This fodler name is SN + SN + WO Name
#copies VNAX PM from "V:\production\Ship&Receive\Shipped Product Manuals\VNAX Manual\VDI-707.1 VNAX Product Manual.pdf"
#one copy in each folder
#next I'll copy in the test port power files, but I want to make sure this works first.

#there's no exception handling for files that are open!


import os
import sys
sys.path.append(r'W:\Python3\vdi_ssp')
import numpy as np
import pandas as pd
import math
import shutil
from util.functions import readFile # type: ignore
#import wx
#import time
#from pathlib import Path
#import threading
#import datetime
#import platform
#from operator import attrgetter
#import pickle
from util.functions import getUniqueFilename, archiveFile, addHeader, getTestSpecs, makeif, timeRemaining, dayString, readFile, ri_to_lin, lin_to_db, dfs_to_excel, getWorkOrderLinks

#Instantiate my Variables
inputCheck=0
#defaultDatasheetLoc = "C:\\Production\\Ship&Receive\\Shipped User Guide\\25_VNA extenders\\"
ProdManloc="C:/Users/smancone/Desktop/FakeNetwork/v/production/Ship&Receive/Shipped Product Manuals/VNAX Manual/VDI-707.1 VNAX Product Manual.pdf"
#approvedDSLoc=

#VNAX Product Manual
#These can be set by user for specific downloads folder and output location, if we dont wantto save diretly to network yet
#maybe could save locally, engineer still has to review files and paste into correct network locations.
localDownloads="C:/Users/smancone/Desktop/FakeNetwork/c/Users/smancone/Downloads/"
#vnaxTppPath="C:/Users/smancone/Desktop/FakeNetwork/v/production/ship&receive/Shipped User Guide/25_VNA extenders/" #andDatasheetPath
woGood=False
global datasheetLocation
datasheetLocation = "N/A"
global c25path
c25path = 'C:/Users/smancone/Desktop/FakeNetwork/v/production/Ship&Receive/Shipped User Guide/25_VNA extenders/'

def datasheetMover1(vnax1sn,woNamePass,testSet):
    origDataSheetName="testset_VNAX%20" +vnax1sn+"_None_"+testSet+".png"
    shutil.move(localDownloads+origDataSheetName, c25path+vnax1sn+" "+woNamePass+".png")
    datasheetLocation=c25path+vnax1sn+" " +woNamePass +".png"
    print("Datasheet Moved to : " + datasheetLocation)
    return datasheetLocation 

def datasheetMover2(vnax1sn,vnax2sn, woNamePass,testSet):
    origDataSheetName="testset_VNAX%20" +vnax1sn+"_VNAX%20"+vnax2sn+"_"+testSet+".png"
    shutil.move(localDownloads+origDataSheetName, c25path+vnax1sn+" "+vnax2sn+" "+woNamePass+".png")        
    datasheetLocation=c25path+vnax1sn+" " +vnax2sn+" " +woNamePass +".png"
    print("Datasheet Moved to : " + datasheetLocation)
    return datasheetLocation

def binaryChecker(input):
    while True:
        try:
            value = int(input)
            if value in [0, 1]:
                return value
            else:
                print("Invalid input. Please enter 0 or 1.")
                input = input("Enter 0 or 1: ")
        except ValueError:
            print("Invalid input. Please enter a number (0 or 1).")
            input = input("Enter 0 or 1: ")


while(int(inputCheck)==0):
    print()
    #datasheetLocation="N/A"
    usageSummaryLink="N/A"

    #woNumCheck
    if(woGood==False):
        
        woNum=str(input("enter WO num: ")).upper()
        print(str(woNum))
        #need to check for the first 6 are numbers and the last is a character, the last character needs to be capitalized if not.
        #if not (woNum[:6].isdigit() and len(woNum) == 7 and woNum[6].isalpha() and woNum[6].isupper()):
        #    print("WO number must be 6 digits followed by a capital letter. Please try again.")
        #    continue


        #The WO getter needs to be the check for a proper order.
        try:
            testWoAr=getWorkOrderLinks(woNum)                 #this just returns a null.
            print(str(testWoAr))
            woNetworkString=os.path.abspath(testWoAr[0].path) #this is the line that can break because it tries to return a path from a null.
            woGood=True
        except:
            print("WO link could not be obatined. Check WO number, location, and entered WO#, including the letter.")
            continue

    #woNetworkString=os.path.abspath(testWoAr[0].path)
    
    #print("WO String : " + str(woNetworkString))
    #woDir=woNetworkString[0:woNetworkString.rfind("\\")]
    #print("WO Directory : " + str(woDir))

    numVNAX=int(input("How many VNAX on this order? (1 or 2) : "))

    #there might be a way to check for the number of VNAX on an order, but we'll ask for now
    #I should probably make these functions that can accept 1 or two variables so i dont have to do an if loop every time..
    #okay this miht actually be more complicated than I thought to make single because of the naming convention of the folders, which uses both SNs
    #and if I remove one I'm left with "VNAX"
    #okay i can make substrings that contain both SNS and insert that... I think that solves some problems
    #pairOrSingle=int(input("1 or 2 VNAX?"))

    if numVNAX==1:
        while int(inputCheck)!=1:        
            
            print()
            

            woNetworkStringLen=len(woNetworkString)
            vnax1=str(input("VNAX SN 1 (Just #): "))
            
            #remove this section when its on network
            #local prestring: C:\Users\smancone\Desktop\FakeNetwork\v
            woNetworkString="C:/Users/smancone/Desktop/FakeNetwork/v" + woNetworkString[2:woNetworkStringLen]
            #woName=woNetworkString.split("/")[-1]
            woNetworkDir=woNetworkString[0:woNetworkString.rfind("\\")+1]
            print("WO Network Dir : " + str(woNetworkDir))
            woName=woNetworkString[woNetworkString.find(woNum):len(woNetworkString)-5]
            print("WO Name : " + str(woName))
            print("WO String for Fake Network : " + str(woNetworkString))
        

            print("VNAX1 SN : VNAX " + vnax1)
            tppYN = int(input("is TPP in DL folder? 0 or 1 : "))
            datasheetYN = int(input("is datasheet in DL folder? 0 or 1 : "))
            usageSummaryYN=int(input("is usage summary in DL folder? 0 or 1 : "))
            testSetRev=str(input("Test Set Revision Letter: "))

            print("~~~~Please Confirm~~~~")
            print("WO#: "+woNum)
            print("WO String : " + str(woNetworkString))
            print("# VNAX : " + str(numVNAX))
            print("VNAX1 SN : VNAX " + vnax1)
            if numVNAX==2:
                print("VNAX2 SN : VNAX " + vnax2)
            

            inputCheck = int(input("Does Everything Look Correct? Enter 0 to reenter or 1 to start processing : "))
            if inputCheck == 0:
                woGood = False
                numVNAX=0


        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")

        #folder_path = 'C:/Users/smancone/Desktop/FakeNetwork/v/production/Ship&Receive/Shipped User Guide/25_VNA extenders/VNAX '+vnax1+' '+vnax2+' '+woName

        #testFolderName = vnax1+' '+vnax2+' '+woName

        #Create Order Folder 
        folder_path = 'C:/Users/smancone/Desktop/FakeNetwork/v/production/Ship&Receive/Shipped User Guide/25_VNA extenders/'+vnax1+' '+woName
        shippedUSBFolder='C:/Users/smancone/Desktop/FakeNetwork/v/production/Ship&Receive/Shipped User Guide/25_VNA extenders/'+vnax1+' '+woName

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"Shipped USB Folder :  '{folder_path}' ")
        else:
            print(f"Nested folders '{folder_path}' already exist.")

        tppFileError=False
        datasheetFileError=False
        usageSummaryError=False

        #Create VNAX 1 Folder 
        #move in VNAX PM
        #move in TPP files
        folder_path = 'C:/Users/smancone/Desktop/FakeNetwork/v/production/Ship&Receive/Shipped User Guide/25_VNA extenders/'+vnax1+' '+woName+'/'+'VNAX '+vnax1
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"Nested folders '{folder_path}' created.")

            shutil.copy(ProdManloc, folder_path+'/'+'VDI-707.1 VNAX Product Manual.pdf')
            #moveTPP files:
            if tppYN==1:
                try:
                    shutil.copy(localDownloads+"VNAX "+vnax1+" Test Port Power.csv", folder_path+'/'+"VNAX "+vnax1+" Test Port Power.csv")
                except FileNotFoundError:
                    print(f"File not found: {localDownloads+'VNAX '+vnax1+' Test Port Power.csv'}")
                    tppFileError=True
                try:
                    shutil.copy(localDownloads+"VNAX "+vnax1+" Test Port Power.prn", folder_path+'/'+"VNAX "+vnax1+" Test Port Power.prn")
                except FileNotFoundError:
                    print(f"File not found: {localDownloads+'VNAX '+vnax1+' Test Port Power.prn'}")
                    tppFileError=True
            if datasheetYN==1:
                try:
                    #shutil.copy(localDownloads+vnax1+" "+ woName +".pdf", c25path)
                    #datasheetLocation=c25path+vnax1+" " + woName +".pdf"
                    #origDataSheetName="testset_VNAX%20" +vnax1+"_VNAX%20"+vnax2+".png"
                    #shutil.move(localDownloads+origDataSheetName, c25path+vnax1+" "+vnax2+" "+woName+".png")
                    datasheetLocation = datasheetMover1(vnax1,woName,testSetRev)    
                    #datasheetLocation=c25path+vnax1+" " +woName +".png"
                except FileNotFoundError:
                    print(f"File not found: {localDownloads+vnax1+' ' + woName +'.pdf'}")
                    datasheetLocation="N/A"
                    datasheetFileError=True
        else:
            print(f"Nested folders '{folder_path}' already exist.")
            
            shutil.copy(ProdManloc, folder_path+'/'+'VDI-707.1 VNAX Product Manual.pdf')
            #moveTPP files:
            if tppYN==1:
                try:
                    shutil.copy(localDownloads+"VNAX "+vnax1+" Test Port Power.csv", folder_path+'/'+"VNAX "+vnax1+" Test Port Power.csv")
                except FileNotFoundError:
                    print(f"File not found: {localDownloads+'VNAX '+vnax1+' Test Port Power.csv'}")
                    tppFileError=True
                try:
                    shutil.copy(localDownloads+"VNAX "+vnax1+" Test Port Power.prn", folder_path+'/'+"VNAX "+vnax1+" Test Port Power.prn")
                except FileNotFoundError:
                    print(f"File not found: {localDownloads+'VNAX '+vnax1+' Test Port Power.prn'}")
                    tppFileError=True
            if datasheetYN==1:
                try:
                    #shutil.copy(localDownloads+vnax1+" " + woName +".pdf", c25path)
                    #datasheetLocation=c25path+vnax1+" " + woName +".pdf"
                    datasheetLocation = datasheetMover1(vnax1,woName,testSetRev)
                except FileNotFoundError:
                    print(f"File not found: {localDownloads+vnax1+' ' + woName +'.pdf'}")
                    datasheetLocation="N/A"
                    datasheetFileError=True


    if(numVNAX==2):
        while int(inputCheck)!=1:

            print()
            print("~~~~Please Confirm~~~~")
            print("WO#: "+woNum)
            print("WO String : " + str(woNetworkString))
            woNetworkStringLen=len(woNetworkString)
            vnax1=str(input("VNAX SN 1 (Just #): "))
            #if(pairOrSingle==2):
            #    vnax2=str(input("VNAX SN 2 (Just #): "))
            vnax2=str(input("VNAX SN 2 (Just #): "))

            #remove this section when its on network
            #local prestring: C:\Users\smancone\Desktop\FakeNetwork\v
            woNetworkString="C:/Users/smancone/Desktop/FakeNetwork/v" + woNetworkString[2:woNetworkStringLen]
            #woName=woNetworkString.split("/")[-1]
            woNetworkDir=woNetworkString[0:woNetworkString.rfind("\\")+1]
            print("WO Network Dir : " + str(woNetworkDir))
            woName=woNetworkString[woNetworkString.find(woNum):len(woNetworkString)-5]
            print("WO Name : " + str(woName))
            print("WO String for FAke Network : " + str(woNetworkString))
        

            print("VNAX1 SN : VNAX " + vnax1)
            print("VNAX2 SN : VNAX " + vnax2)
            tppYN = int(input("is TPP in DL folder? 0 or 1 : "))
            datasheetYN = int(input("is datasheet in DL folder? 0 or 1 : "))
            usageSummaryYN=int(input("is usage summary in DL folder? 0 or 1 : "))
            testSetRev=str(input("Test Set Revision Letter: "))


            inputCheck = int(input("Does Everything Look Correct? Enter 0 to reenter or 1 to start processing : "))
            if inputCheck == 0:
                woGood = False
                numVNAX=0
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")

        #folder_path = 'C:/Users/smancone/Desktop/FakeNetwork/v/production/Ship&Receive/Shipped User Guide/25_VNA extenders/VNAX '+vnax1+' '+vnax2+' '+woName

        #testFolderName = vnax1+' '+vnax2+' '+woName

        #Create Order Folder 
        folder_path = 'C:/Users/smancone/Desktop/FakeNetwork/v/production/Ship&Receive/Shipped User Guide/25_VNA extenders/'+vnax1+' '+vnax2+' '+woName
        shippedUSBFolder='C:/Users/smancone/Desktop/FakeNetwork/v/production/Ship&Receive/Shipped User Guide/25_VNA extenders/'+vnax1+' '+vnax2+' '+woName
        c25path = 'C:/Users/smancone/Desktop/FakeNetwork/v/production/Ship&Receive/Shipped User Guide/25_VNA extenders/'
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"Shipped USB Folder :  '{folder_path}' ")
        else:
            print(f"Nested folders '{folder_path}' already exist.")

        tppFileError=False
        datasheetFileError=False
        usageSummaryError=False

        #Create VNAX 1 Folder 
        #move in VNAX PM
        #move in TPP files
        folder_path = 'C:/Users/smancone/Desktop/FakeNetwork/v/production/Ship&Receive/Shipped User Guide/25_VNA extenders/'+vnax1+' '+vnax2+' '+woName+'/'+'VNAX '+vnax1
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"Nested folders '{folder_path}' created.")

            shutil.copy(ProdManloc, folder_path+'/'+'VDI-707.1 VNAX Product Manual.pdf')
            #moveTPP files:
            if tppYN==1:
                try:
                    shutil.copy(localDownloads+"VNAX "+vnax1+" Test Port Power.csv", folder_path+'/'+"VNAX "+vnax1+" Test Port Power.csv")
                except FileNotFoundError:
                    print(f"File not found: {localDownloads+'VNAX '+vnax1+' Test Port Power.csv'}")
                    tppFileError=True
                try:
                    shutil.copy(localDownloads+"VNAX "+vnax1+" Test Port Power.prn", folder_path+'/'+"VNAX "+vnax1+" Test Port Power.prn")
                except FileNotFoundError:
                    print(f"File not found: {localDownloads+'VNAX '+vnax1+' Test Port Power.prn'}")
                    tppFileError=True
            if datasheetYN==1:
                try:
                    #shutil.copy(localDownloads+vnax1+" " + vnax2+" " + woName +".pdf", c25path)
                    #datasheetLocation=c25path+vnax1+" " + vnax2+" " + woName +".pdf"
                    datasheetLocation = datasheetMover2(vnax1,vnax2,woName,testSetRev)
                except FileNotFoundError:
                    print(f"File not found: {localDownloads+vnax1+' ' + vnax2+' ' + woName +'.pdf'}")
                    datasheetFileError=True
        else:
            print(f"Nested folders '{folder_path}' already exist.")
            
            shutil.copy(ProdManloc, folder_path+'/'+'VDI-707.1 VNAX Product Manual.pdf')
            #moveTPP files:
            if tppYN==1:
                try:
                    shutil.copy(localDownloads+"VNAX "+vnax1+" Test Port Power.csv", folder_path+'/'+"VNAX "+vnax1+" Test Port Power.csv")
                except FileNotFoundError:
                    print(f"File not found: {localDownloads+'VNAX '+vnax1+' Test Port Power.csv'}")
                    tppFileError=True
                try:
                    shutil.copy(localDownloads+"VNAX "+vnax1+" Test Port Power.prn", folder_path+'/'+"VNAX "+vnax1+" Test Port Power.prn")
                except FileNotFoundError:
                    print(f"File not found: {localDownloads+'VNAX '+vnax1+' Test Port Power.prn'}")
                    tppFileError=True
            if datasheetYN==1:
                try:
                    datasheetLocation = datasheetMover2(vnax1,vnax2,woName,testSetRev)
                except FileNotFoundError:
                    print(f"File not found: {localDownloads+vnax1+' ' + vnax2+' ' + woName +'.pdf'}")
                    datasheetFileError=True
                    datasheetLocation="N/A"


        #Create VNAX 2 Folder
        #'C:/Users/smancone/Desktop/FakeNetwork/
        folder_path = 'C:/Users/smancone/Desktop/FakeNetwork/v/production/Ship&Receive/Shipped User Guide/25_VNA extenders/'+vnax1+' '+vnax2+' '+woName+'/'+'VNAX '+vnax2
        #C:\Users\smancone\Downloads
        #folder_path = 'C:/Users/smancone/Desktop/FakeNetwork/c/Users/smancone/Downloads'
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"Nested folders '{folder_path}' created.")
            shutil.copy(ProdManloc, folder_path+'/'+'VDI-707.1 VNAX Product Manual.pdf')
            #moveTPP files:
            if tppYN==1:
                try:
                    shutil.copy(localDownloads+"VNAX "+vnax2+" Test Port Power.csv", folder_path+'/'+"VNAX "+vnax2+" Test Port Power.csv")
                except FileNotFoundError:
                    print(f"File not found: {localDownloads+'VNAX '+vnax2+' Test Port Power.csv'}")
                    tppFileError=True
                try:
                    shutil.copy(localDownloads+"VNAX "+vnax2+" Test Port Power.prn", folder_path+'/'+"VNAX "+vnax2+" Test Port Power.prn")
                except FileNotFoundError:
                    print(f"File not found: {localDownloads+'VNAX '+vnax2+' Test Port Power.prn'}")
                    tppFileError=True
            #No datasheet. one only datasheet per order and this is done on the first VNAX file creation.
        else:
            print(f"Nested folders '{folder_path}' already exist.")

            shutil.copy(ProdManloc, folder_path+'/'+'VDI-707.1 VNAX Product Manual.pdf')
            #moveTPP files:
            if tppYN==1:
                try:
                    shutil.copy(localDownloads+"VNAX "+vnax2+" Test Port Power.csv", folder_path+'/'+"VNAX "+vnax2+" Test Port Power.csv")
                except FileNotFoundError:
                    print(f"File not found: {localDownloads+'VNAX '+vnax2+' Test Port Power.csv'}")
                    tppFileError=True
                try:
                    shutil.copy(localDownloads+"VNAX "+vnax2+" Test Port Power.prn", folder_path+'/'+"VNAX "+vnax2+" Test Port Power.prn")
                except FileNotFoundError:
                    print(f"File not found: {localDownloads+'VNAX '+vnax2+' Test Port Power.prn'}")
                    tppFileError=True







#move usage summary
if(usageSummaryYN==1):
    #update website to name it properly and change hard-code or rename it properly here
    #proper usage summary is just woNAme.pdf but it is currently woNum - Usage Summary.pdf
    try:
        shutil.copy(localDownloads+woNum+" - Usage Summary.pdf", woNetworkDir+woName+".pdf") #this is shutil not copy not move
        usageSummaryLink=woNetworkDir+woName+".pdf"
    except FileNotFoundError:
        print(f"File not found: {localDownloads+woNum+' - Usage Summary.pdf'}")
        usageSummaryLink="N/A"
        usageSummaryError=True


print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
print("~~~~~~~~~~~~~~~File Locations~~~~~~~~~~~~~~ ")
print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
print("Datasheet : ")
print(datasheetLocation)
if(datasheetFileError==True):
    print("Datasheet was not found in the expected location and was not copied. Please check the error message above for details and rerun as needed.")
print("")
print("Shipped USB Folder : ")
print(shippedUSBFolder)
if(tppFileError==True):
    print("One or more TPP files were not found in the expected location and were not copied. Please check the error messages above for details and rerun as needed.")
print("")
print("Usage Summary : ")
print(usageSummaryLink)
if(usageSummaryError==True):
    print("Usage Summary was not found in the expected location and was not copied. Please check the error message above for details and rerun as needed.")
print("")
print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")


#shutil.copy(ProdManloc, 'C:/Users/smancone/Desktop/FakeNetwork/v/production/Ship&Receive/Shipped User Guide/25_VNA extenders/'+vnax1+' '+vnax2+' '+woName+'/'+' VNAX '+vnax1+'/'+'VDI-707.1 VNAX Product Manual.pdf')
#c:\users\smancone\downloads

    


