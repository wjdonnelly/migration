import migrationLib
import json
import os.path
import sys

#set config variables
filePath = 'c:\seoImport\scrubResClean\\'  #use full path name to folder with raw files - include trailing \\ (i.e. "c:\rawfilesfolder\\"
activeAccountIds = ["75390639FE7A4D6FAC73B85265B55F05" , "8FA220CD96AD45009035EDBF3F66BB47"] #add the active and active recurring accountstatusid values to the array

seo = migrationLib.seoInput(filePath, activeAccountIds)



seo.parseFile()
seo.joinFiles()

outputFilename = filePath + "accountdata_flat" + ".csv"

if os.path.exists(outputFilename):
    answer = raw_input("File Exists. Enter 'yes' to overwrite\n>")
    if answer == "yes":
        print("Overwriting File: " + outputFilename)
        os.remove(outputFilename)
        
    else:
        print("terminated")
        sys.exit()

print("Creating output file: " + outputFilename)

for account in  seo.accounts:

    outputFile = open(outputFilename, 'a')
    outputFile.write(json.dumps(account))
    outputFile.write('\n')