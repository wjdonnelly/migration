#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:     bdonnelly
#
# Created:     02/01/2015
# Copyright:   (c) 
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import csv
import os
import sys
import json
import requests
import time
import datetime


class seoInput():

    def __init__(self, filePath, activeAccountIds):
        self.filePath = filePath
        self.accountFile = 'B_TACCOUNT.CSV'
        self.contactFile = 'B_TCONTACT.CSV'
        self.employeeFile = "B_TEMPLOYEE.CSV"
        self.activeAccountIds = activeAccountIds

        #employeeStatusID = 42D7FE70946540359C5EC837F79B9859 (active)
        self.agreementsFile = "B_TVISIT.CSV"
        #self.accountToContactFile = 'B_TACCOUNTCONTACTLINK'
        self.accountToServiceContactLink = 'DEFAULTSERVICECONTACTID'
        self.accountToBillingContactLink = 'DEFAULTBILLINGCONTACTID'
        
        self.locationFile = 'B_TLOCATION.CSV'
        self.accountToAddressLink = 'DEFAULTSERVICELOCATIONID'
        self.fileList = [self.accountFile, self.contactFile, self.locationFile]
        
    def parseFile(self):
        self.dict = {} 
        defaultsErrorCount = 1
        inactiveAccountCount = 1
        activeAccountCount = 1
        for file in self.fileList:
            sourceFile = self.filePath + file
            key = file.lower()
            key = key.replace(".csv", "")
            
            if os.path.exists(sourceFile) == False:
                print('Source file (' + sourceFile +  ' not found - quitting')
                sys.exit()
            else:
                print('Opening main test script file: ' + sourceFile)
    
           
            subStruct = []
            
            with open(sourceFile, mode='r') as infile:
                dictReader = csv.DictReader(infile)
                for row in dictReader:
                    
                    if file == "B_TACCOUNT.CSV":
                        
                        if row["ACCOUNTSTATUSID"] == "75390639FE7A4D6FAC73B85265B55F05" or row["ACCOUNTSTATUSID"] == "8FA220CD96AD45009035EDBF3F66BB47":
                            activeAccountCount += 1
                            if row["DEFAULTSERVICELOCATIONID"] <> "NULL" and row["DEFAULTSERVICECONTACTID"] <> "NULL"  \
                            and row["DEFAULTBILLINGLOCATIONID"] <> "NULL" and row["DEFAULTBILLINGCONTACTID"] <> "NULL":
                            
                                subStruct.append(row)
                            else:
                                defaultsErrorCount += 1
                                pass
                        else:
                            inactiveAccountCount += 1
                            pass
                            
                    else:
                        subStruct.append(row)
                        
                self.dict[key] = subStruct
        
        print("")
        print("active account count = " + str(activeAccountCount))
        print("inactive account count = " + str(inactiveAccountCount))
        print("missing defaults = " + str(defaultsErrorCount)) 
        print("")
        
        return()
    
    def joinFiles(self):
        
        self.accounts = []
        self.agreements = []
        
        self.accountsCount = 0
        for account in self.dict['b_taccount']:
            self.dscid = account["DEFAULTSERVICECONTACTID"]
            
            self.dslid = account["DEFAULTSERVICELOCATIONID"]
            
            self.dbcid = account["DEFAULTBILLINGCONTACTID"]
            
            self.dblid = account["DEFAULTBILLINGLOCATIONID"]
           
            self.accountName = account["ACCOUNTNAME"].rstrip()
             
            joinServiceContact = self.search_dict("CONTACTID", self.dscid, self.dict["b_tcontact"])
            joinServiceLocation = self.search_dict("LOCATIONID", self.dslid, self.dict["b_tlocation"])
            
            joinBillingContact = self.search_dict("CONTACTID", self.dbcid, self.dict["b_tcontact"])
            joinBillingLocation = self.search_dict("LOCATIONID", self.dblid, self.dict["b_tlocation"])
           
           
            
            sc = joinServiceContact[0]
            self.sc = sc
            sl = joinServiceLocation[0]
            
            bc = joinBillingContact[0]
            self.bc = bc
            bl = joinBillingLocation[0]
            
            stateName = self.stateLookup(sl["ADDRESS_STATE"])
            
            #scrub data for address 
            if sl["ADDRESS_STATE"] == "NULL" or sl["ADDRESS_CITY"] == "NULL" or sl["ADDRESS_POSTALCODE"] == "NULL":
                print(self.accountName + ": skipped for bad address")
                continue
            # pull out the required fields from the row. 
            #make the billing and service name field
            
            if sc["NAME_MIDDLE"] == "NULL":
                
                serviceContactName = sc["NAME_FIRST"] + " " + sc["NAME_LAST"]
            else:
                serviceContactName = sc["NAME_FIRST"] + " " + sc["NAME_MIDDLE"] + " " + sc["NAME_LAST"]
            
            if bc["NAME_MIDDLE"] == "NULL":
                
                billingContactName = bc["NAME_FIRST"] + " " + bc["NAME_LAST"]
            else:
                billingContactName = bc["NAME_FIRST"] + " " + bc["NAME_MIDDLE"] + " " + bc["NAME_LAST"]
            
            
            if sl["ADDRESS_ADDRESS2"] == "NULL":
                sl["ADDRESS_ADDRESS2"] = ""
            
            if bl["ADDRESS_ADDRESS2"] == "NULL":
                bl["ADDRESS_ADDRESS2"] = ""
                
            slAddressArray = [sl["ADDRESS_ADDRESS1"],sl["ADDRESS_ADDRESS2"], sl['ADDRESS_CITY'],  stateName, \
                            sl["ADDRESS_STATE"], sl["ADDRESS_POSTALCODE"], "US", sl["ADDRESS_LATITUDE"], sl["ADDRESS_LONGITUDE"]]
                                           
            self.slAddress = self.address(slAddressArray)
            
            blAddressArray = [bl["ADDRESS_ADDRESS1"],bl["ADDRESS_ADDRESS2"], bl['ADDRESS_CITY'], stateName, \
                            bl["ADDRESS_STATE"], bl["ADDRESS_POSTALCODE"], "US", bl["ADDRESS_LATITUDE"], bl["ADDRESS_LONGITUDE"]]
            
            self.blAddress = self.address(slAddressArray)
            
            phoneList = ["TELEPHONE_MAIN", "TELEPHONE_MOBILE", "TELEPHONE_HOME", "TELEPHONE_WORK", "TELEPHONE_FAX", "TELEPHONE_OTHER"]
            
            
            serviceContactInfo = False
            self.serviceContact = {}
            self.serviceContact["Name"] = serviceContactName
            self.serviceContact["ContactType"] = "Service"
            self.serviceContact["Emails"] = []
            if sc["EMAIL"] <> "NULL":
                serviceContactInfo = True
                scemailDict = {} 
                scemailDict["name"] = "Work"
                scemailDict["contactValue"] = sc["EMAIL"]
                scemailDict["preferred"] = 'false'
                self.serviceContact["Emails"].append(scemailDict)
            
            self.billingContact = {}
            self.billingContact["Name"] = billingContactName
            self.billingContact["ContactType"] = "Billing"
            self.billingContact["Emails"] = []
            if bc["EMAIL"] <> "NULL":
                bcemailDict = {} 
                bcemailDict["name"] = "Work"
                bcemailDict["contactValue"] = bc["EMAIL"]
                bcemailDict["preferred"] = 'false'
                self.billingContact["Emails"].append(bcemailDict)
            
           
            self.serviceContact["Phones"] = []
            for servicePhone in phoneList:
                
                sflag = 0
                if sc[servicePhone] <> "NULL":
                    serviceContactInfo = True
                    tphone = sc[servicePhone].replace("(", "")
                    label = servicePhone.replace("TELEPHONE_", "")
                    tphone = tphone.replace(") ", "-")
                    tphone = tphone.replace(")-", "-")
                    
                    scphoneDict = {}
                    scphoneDict["name"] = label.title()
                    scphoneDict["contactValue"] = tphone
                    if sflag == 0:
                        scphoneDict["preferred"] = 'true'
                        sflag = 1
                    else:
                        scphoneDict["preferred"] = 'true'
                        
                    self.serviceContact["Phones"].append(scphoneDict)
            
           
            self.billingContact["Phones"] = []
            for billingPhone in phoneList:
                
                bflag = 0
                if bc[billingPhone] <> "NULL":
                    tphone = bc[billingPhone].replace("(", "")
                    label = billingPhone.replace("TELEPHONE_", "")
                    tphone = tphone.replace(") ", "-")
                    tphone = tphone.replace(")-", "-")
                    
                    bcphoneDict = {}
                
                    bcphoneDict["name"] = label.title()
                    bcphoneDict["contactValue"] = tphone
                    if bflag == 0:
                        bcphoneDict["preferred"] = 'true'
                        bflag = 1
                    else:
                        bcphoneDict["preferred"] = 'false'
                        
                    self.billingContact["Phones"].append(bcphoneDict)
                 
            #scrub for email and phone info
           
                                                    
            if serviceContactInfo == False:
                print(self.accountName + ": skipped for 0 contact methods")
                continue
            
            self.accountsCount += 1
            
        #tsv flat data for debug
             
            #===================================================================
            # outline = account['ACCOUNTNAME'] + '\t' +  sc[0]["NAME_FIRST"] + '\t' + sc[0]["NAME_LAST"]  + '\t'  \
            # + sc[0]["EMAIL"] + '\t' + sc[0]["TELEPHONE_MAIN"] + '\t' + sc[0]["TELEPHONE_WORK"] + '\t' \
            # + sc[0]["TELEPHONE_FAX"] + '\t' + sc[0]["TELEPHONE_MOBILE"] + '\t' + sc[0]["TELEPHONE_OTHER"] + '\t' \
            # + sl["ADDRESS_ADDRESS1"]  + '\t' + sl["ADDRESS_ADDRESS2"]  + '\t' \
            # + sl["ADDRESS_CITY"]   + '\t' + sl["ADDRESS_COUNTRY"] + '\t' \
            # + sl["ADDRESS_STATE"]   + '\t' + sl["ADDRESS_POSTALCODE"] + '\t' \
            # + joinBillingContact[0]["NAME_FIRST"] + '\t' + joinBillingContact[0]["NAME_LAST"]  + '\t'  \
            # + joinBillingContact[0]["EMAIL"] + '\t' + joinBillingContact[0]["TELEPHONE_MAIN"] + '\t' + joinBillingContact[0]["TELEPHONE_WORK"] + '\t' \
            # + joinBillingContact[0]["TELEPHONE_FAX"] + '\t' + joinBillingContact[0]["TELEPHONE_MOBILE"] + '\t' + joinBillingContact[0]["TELEPHONE_OTHER"] + '\t' \
            # + joinBillingLocation[0]["ADDRESS_ADDRESS1"]  + '\t' + joinBillingLocation[0]["ADDRESS_ADDRESS2"]  + '\t' \
            # + joinBillingLocation[0]["ADDRESS_CITY"]   + '\t' + joinBillingLocation[0]["ADDRESS_COUNTRY"] + '\t' \
            # + joinBillingLocation[0]["ADDRESS_STATE"]   + '\t' + joinBillingLocation[0]["ADDRESS_POSTALCODE"] +  '\t' \
            # + serviceContactName + '\t' + sc[0]["EMAIL"] + '\t' + serviceContact + '\t' + slGeoInput + '\t' \
            # + billingContactName +  '\t' + joinBillingContact[0]["EMAIL"] + '\t' + billingContact + '\t' + blGeoInput + \
            # + sl["ADDRESS_LATITUDE"] + '\t' + sl["ADDRESS_LONGITUDE"] + '\n'
            # 
            #===================================================================
            
        
            self.accounts.append(self.accountToDict())
    
        return()
            
    def search_dict(self, key, value, list_of_dictionaries):
        return [element for element in list_of_dictionaries if element[key] == value]
    
    def fixPhone(self, row):
        pass
        #if row["TELEPHONE_MAIN"] <> "NULL"
    
    
    
    
    def address(self, address):
        #"parse address array to odyssey dict
        
        addressDict = {}
        addressDict["LineOne"] = address[0] 
        addressDict["LineTwo"] = address[1]
        addressDict["City"] = address[2]
        addressDict["State"] = address[3] 
        addressDict["StateAbbreviation"] = address[4]
        addressDict["PostalCode"] = address[5]
        addressDict["Country"] = address[6]
        addressDict["Latitude"] = address[7]
        addressDict["Longitude"] = address[8]
        
        return(addressDict)
    
    def stateLookup(self, stateAbbrev):
        states = {}
        states["NJ"] = "New Jersey"
        states["NY"] = "New York"
        states["PA"] = "Pennsylvania"
        states["MA"] = "Massachusetts"
        states["CT"] = "Connecticut"
        states["NULL"] = "Null"
        states["CA"] = "California"
        
        return states[stateAbbrev]
    
        
        
    def accountToDict(self):
        acctDict = {}
        contact = []
       
        acctDict["Name"] = self.accountName
        acctDict["DefaultServiceLocation"] = {}
        acctDict["DefaultServiceLocation"]["address"] = self.slAddress
        acctDict["DefaultBillingAddress"] = self.blAddress
        
        acctDict["Contact"] = []
        acctDict["Contact"].append(self.serviceContact)
        acctDict["Contact"].append(self.billingContact)
        return(acctDict)
        
    def getAccounts(self):
        pass
        
        
    def agreementToDict(self, accountNumber, scid, preferredContactMethod, preferredMethodId):
        
        
        today_date = datetime.date.today()
        initialCommitmentWindowStart = datetime.datetime.now()
        initialCommitmentWindowEnd = datetime.datetime.now()
        initialCommitmentWindowStart_iso = ''
        initialCommitmentWindowEnd_iso = ''
        
        initialCommitmentWindowStart_iso = initialCommitmentWindowStart.strftime("%Y-%m-%dT00:15:00")
        initialCommitmentWindowEnd_iso = initialCommitmentWindowEnd.strftime("%Y-%m-%dT23:45:00")

        todayDateFormatted = today_date.strftime("%Y-%m-%d")
        countOfAgreements = 0
        
        agreementDict = {}
        agreementDict["accountId"] = accountNumber
        agreementDict["billingAddress"] = self.slAddress
        agreementDict["effectiveDate"] = todayDateFormatted
        agreementDict["initialCommitmentTech"] = "technicians/1"
        agreementDict["initialCommitmentWindowEnd"] = initialCommitmentWindowEnd_iso
        agreementDict["initialCommitmentWindowStart"] = initialCommitmentWindowStart_iso
        agreementDict["invoiceSchedule"] = 0
        agreementDict["issue"] = ""
        agreementDict["name"] = self.accountName
        agreementDict["preferredEndTime"] = "23:59:59"
        agreementDict["preferredStartTime"] = "00:00:00"
        agreementDict["serviceLocation"] = {}
        agreementDict["serviceLocation"]["address"] = self.slAddress
        
        
        agreementDict["contact"] = []
        
        self.serviceContact["id"] = scid
        self.billingContact["id"] = scid
        
        if preferredContactMethod == "phone":
            self.serviceContact["Phones"][0]["id"] = preferredMethodId
            self.billingContact["Phones"][0]["id"] = preferredMethodId
        else:
            self.serviceContact["Emails"][0]["id"] = preferredMethodId
            self.billingContact["Emails"][0]["id"] = preferredMethodId
            
        
        
    
        
        agreementDict["contact"].append(self.serviceContact)
        agreementDict["contact"].append(self.billingContact)
        
        
        
        servicesDict = {}
        servicesDict["services"] = []
       
        offerDict = {}
        offerDict["duration"] = 1
        
       
        offerDict["offeringId"] = "b05f451a-f6df-4334-a4ac-a46b632db5fa"
        
        offerDict["price"] = 0.00
        agreementDict["services"] = []
        agreementDict["services"].append(offerDict)
        
        
        
        taxDict = {}
        taxDict["citySalesTax"] =  0
        taxDict["cityTaxCode"] = "2"
        taxDict["cityUseTax"] = 0
        taxDict["countySalesTax"] = 0.019999999552965
        taxDict["countyTaxCode"] = "2"
        taxDict["countyUseTax"] = 0.019999999552965
        taxDict["districtSalesTax"] = 0
        taxDict["districtUseTax"] = 0
        taxDict["geoCity"] = "MIDDLE CITY EAST"
        taxDict["geoCounty"] = "PHILADELPHIA"
        taxDict["geoPostalCode"] = "19102"
        taxDict["geoState"] = "PA"
        taxDict["stateSalesTax"] = 0.059999998658895
        taxDict["stateUseTax"] = 0.059999998658895
        taxDict["taxSales"] = 0.079999998211861
        taxDict["taxUse"] = 0.079999998211861
        taxDict["txbFreight"] = "Y"
        taxDict["txbService"] = "Y"
        

        agreementDict["taxRates"] = taxDict
        agreementDict["InvoiceSchedule"] = 0
        
        return(agreementDict)
         
                            
                          
                        
         
    def accountToAgreement(self, account, offeringID, taxDict):
        
        
        today_date = datetime.date.today()
        initialCommitmentWindowStart = datetime.datetime.now()
        initialCommitmentWindowEnd = datetime.datetime.now()
        initialCommitmentWindowStart_iso = ''
        initialCommitmentWindowEnd_iso = ''
        
        initialCommitmentWindowStart_iso = initialCommitmentWindowStart.strftime("%Y-%m-%dT00:15:00")
        initialCommitmentWindowEnd_iso = initialCommitmentWindowEnd.strftime("%Y-%m-%dT23:45:00")

        todayDateFormatted = today_date.strftime("%Y-%m-%d")
        countOfAgreements = 0
        
        agreementDict = {}
        agreementDict["accountId"] = str(account["account"]["id"])
        agreementDict["billingAddress"] = account["account"]["defaultBillingAddress"]
        agreementDict["effectiveDate"] = todayDateFormatted
        agreementDict["initialCommitmentTech"] = "technicians/1"
        agreementDict["initialCommitmentWindowEnd"] = initialCommitmentWindowEnd_iso
        agreementDict["initialCommitmentWindowStart"] = initialCommitmentWindowStart_iso
        agreementDict["invoiceSchedule"] = 0
        agreementDict["issue"] = ""
        agreementDict["name"] = str(account["account"]["name"])
        agreementDict["preferredEndTime"] = "23:59:59"
        agreementDict["preferredStartTime"] = "00:00:00"
        agreementDict["serviceLocation"] = {}
        agreementDict["serviceLocation"] = account["account"]['defaultServiceLocation']
        
        agreementDict["contact"] = []
        
        
        if account["contacts"][0]["preferredMethodType"] == "Phones":
            preferredMethod = "phone"
        else:
            preferredMethod = "email"

        serviceContact = {}
        billingContact = {}
        
        serviceContact["contactType"] = "service"
        billingContact["contactType"] = "billing"
        serviceContact["Phones"] = []
        billingContact["Phones"] = []
        serviceContact["Emails"] = []
        billingContact["Emails"] = []
        
        
        serviceContact["id"] = str(account["contacts"][0]["id"])
        billingContact["id"] = str(account["contacts"][0]["id"])
        
        serviceContact["name"] = str(account["contacts"][0]["name"])
        billingContact["name"] = str(account["contacts"][0]["name"])
       
        if len(account["contacts"][0]["phones"]) > 0:
            scDict = {}
            bcDict = {}
            scDict["name"] = account["contacts"][0]["phones"][0]["name"]
            bcDict["name"] = account["contacts"][0]["phones"][0]["name"]
            scDict["contactValue"] = account["contacts"][0]["phones"][0]["contactValue"]
            bcDict["contactValue"] = account["contacts"][0]["phones"][0]["contactValue"]
            scDict["id"] = account["contacts"][0]["phones"][0]["id"]
            bcDict["id"] = account["contacts"][0]["phones"][0]["id"]
             
            if preferredMethod == "phone":
          
                scDict["preferred"] = "true"
                bcDict["preferred"] = "true"
            else:
                scDict["preferred"] = "false"
                bcDict["preferred"] = "false"
            
            serviceContact["Phones"].append(scDict)
            billingContact["Phones"].append(bcDict)
        
         
         #######################
         
        if len(account["contacts"][0]["emails"]) > 0:
            scDict = {}
            bcDict = {}
            scDict["name"] = account["contacts"][0]["emails"][0]["name"]
            bcDict["name"] = account["contacts"][0]["emails"][0]["name"]
            scDict["contactValue"] = account["contacts"][0]["emails"][0]["contactValue"]
            bcDict["contactValue"] = account["contacts"][0]["emails"][0]["contactValue"]
            scDict["id"] = account["contacts"][0]["emails"][0]["id"]
            bcDict["id"] = account["contacts"][0]["emails"][0]["id"]
             
            if preferredMethod == "email":
          
                scDict["preferred"] = "true"
                bcDict["preferred"] = "true"
            else:
                scDict["preferred"] = "false"
                bcDict["preferred"] = "false"
            
            serviceContact["Emails"].append(scDict)
            billingContact["Emails"].append(bcDict)
        
         
        agreementDict["contact"].append(serviceContact)
        agreementDict["contact"].append(billingContact)
         
        
        
        servicesDict = {}
        servicesDict["services"] = []
       
        offerDict = {}
        offerDict["duration"] = 1
        
      
        offerDict["offeringId"] = offeringID
        
        offerDict["price"] = 0.00
        agreementDict["services"] = []
        agreementDict["services"].append(offerDict)
        
        agreementDict["taxRates"] = taxDict
        agreementDict["InvoiceSchedule"] = 0
        
        return(agreementDict)
         
                            
        
class odyssey():
    def __init__(self, env, tenantAdminEmail, tenantUserName):


    #read the config file and set the config variables

        self.filePath = '//mds-fs01/pitcrew/api_testing/'
        self.logFilePath = '//mds-fs01/pitcrew/api_testing/logs/'
        
        self.voloAPIKey = 'ODYS-SEYO-DYSS-EYOD'

        if env == "production":
            self.appServerName = 'api.serviceceo.net'
            self.dbServerName = 'app.serviceceo.net'
            self.dbServerPort = '8080'
            self.dbServerURL = "http://" + self.dbServerName + ":" + self.dbServerPort
            self.appServerAdminPort = '86'
            self.appServerAPIPort = '85'


            self.logFilePathAdmin = self.filePath + "Logs/Administration/"
            self.sysAdminPassword = 'letmein123'
            self.sysAdminEmail = 'admin@marathondata.com'

        #hard code
            self.sysAdminTokenURL = 'http://' + self.appServerName + ":" + self.appServerAdminPort + '/administration/token'
            #self.tenantAdminTokenURL = 'https://' + self.appServerName + ":" + self.appServerAPIPort + '/api/token'
            self.tenantAdminTokenURL = "https://api.serviceceo.net/api/token"        
            self.tenantAdminPassword = "letmein123"
            self.adminSchedulingLicensingURL = 'http://' + self.appServerName + ":" + self.appServerAdminPort + '/administration/schedulinglicensing/'
            self.consoleVerbose = 1
    
    
            self.headers = {'content-type': 'application/json', 'Authorization' : "blankToken"}
            self.loginAsOdysseyAdmin = False
            
            self.tenantAdminEmail = tenantAdminEmail
            self.tenantUserName = tenantUserName
            self.tenantID = ""
            self.offerID = ""
    
            #define API endpoints
            self.createTenantsAPI = '/administration/tenants'
            self.apiAccountsAPI = '/api/accounts'
            self.apiAgreementsAPI = '/api/serviceAgreements'
            self.apiServiceOfferingsAPI = '/api/serviceofferings'
            self.apiServiceHoursAPI = '/api/serviceHours'
            self.apiCompanyHolidaysAPI = '/api/companyHolidays'
            self.apiServiceTerritoriesAPI = '/api/serviceTerritories'
            self.adminUsersAPI =  '/administration/users'
            self.adminTenantAdministratorsAPI = '/administration/tenantadministrator'
            self.apiTechniciansAPI = '/api/technicians'
            self.apiTeamsAPI = '/api/teams'
            self.apiSalesTax = '/api/salestax'
            self.apiAccountDetailsAPI = '/odyssey/accounts/details/Accounts/'
    
            self.createTenantsURL = 'https://' + self.appServerName + '/administration/tenants'
            self.apiAccountsURL = 'https://' + self.appServerName + '/api/accounts'
            self.apiAgreementsURL = 'https://' + self.appServerName + '/api/serviceAgreements'
            self.apiServiceOfferingsURL = 'https://' + self.appServerName +  '/api/serviceofferings'
            self.apiServiceHoursURL = 'https://' + self.appServerName +  '/api/serviceHours'
            self.apiCompanyHolidaysURL = 'https://' + self.appServerName + '/api/companyHolidays'
            self.apiServiceTerritoriesURL = 'https://' + self.appServerName  + '/api/serviceTerritories'
            self.adminUsersURL = 'https://' + self.appServerName  + '/administration/users'
            self.adminTenantAdministratorsURL = 'https://' + self.appServerName  + '/administration/tenantadministrator'
            self.apiTechniciansURL = 'https://' + self.appServerName + '/api/technicians'
            self.apiTeamsURL = 'https://' + self.appServerName + '/api/teams'
            self.apiDuplicateEmailURL = 'https://' + self.appServerName + '/api/duplicateemployees?email='
            self.apiSalesTaxURL = 'https://' + self.appServerName + '/api/serviceAgreements'
            self.apiAccountDetailsURL = 'https://' + self.appServerName + '/odyssey/accounts/details/Accounts/'
        else:
########################
            self.dbServerName = 'qa.serviceceo.net'
            self.appServerName = 'qa.serviceceo.net'
            self.dbServerPort = '8080'
            self.dbServerURL = "http://" + self.dbServerName + ":" + self.dbServerPort
            self.appServerAdminPort = '86'
            self.appServerAPIPort = '85'


            self.logFilePathAdmin = self.filePath + "Logs/Administration/"
            self.sysAdminPassword = 'letmein123'
            self.sysAdminEmail = 'admin@marathondata.com'

        #hard code
            self.sysAdminTokenURL = 'http://' + self.appServerName + ":" + self.appServerAdminPort + '/administration/token'
            #self.tenantAdminTokenURL = 'https://' + self.appServerName + ":" + self.appServerAPIPort + '/api/token'
            self.tenantAdminTokenURL = "http://qa.serviceceo.net" + ":" + self.appServerAPIPort + "/api/token"        
            self.tenantAdminPassword = "letmein123"
            self.adminSchedulingLicensingURL = 'http://' + self.appServerName + ":" + self.appServerAdminPort + '/administration/schedulinglicensing/'
            self.consoleVerbose = 1
    
    
            self.headers = {'content-type': 'application/json; charset=US-ASCII', 'Accept-Charset' : "US-ASCII", 'Authorization' : "blankToken"}
            self.loginAsOdysseyAdmin = False
            
            self.tenantAdminEmail = tenantAdminEmail
            self.tenantUserName = tenantUserName
            self.tenantID = tenantId
            self.offerID = ""
            #define API endpoints
            self.createTenantsAPI = '/administration/tenants'
            self.apiAccountsAPI = '/api/accounts'
            self.apiAgreementsAPI = '/api/serviceAgreements'
            self.apiServiceOfferingsAPI = '/api/serviceofferings'
            self.apiServiceHoursAPI = '/api/serviceHours'
            self.apiCompanyHolidaysAPI = '/api/companyHolidays'
            self.apiServiceTerritoriesAPI = '/api/serviceTerritories'
            self.adminUsersAPI =  '/administration/users'
            self.adminTenantAdministratorsAPI = '/administration/tenantadministrator'
            self.apiTechniciansAPI = '/api/technicians'
            self.apiTeamsAPI = '/api/teams'
            self.apiSalesTax = '/api/salestax'
            self.apiAccountDetailsAPI = '/odyssey/accounts/details/Accounts/'
    
            self.createTenantsURL = 'http://' + self.appServerName + ':' + self.appServerAdminPort + '/administration/tenants'
            self.apiAccountsURL = 'http://' + self.appServerName + ':' + self.appServerAPIPort + '/api/accounts'
            self.apiAgreementsURL = 'http://' + self.appServerName + ':' + self.appServerAPIPort + '/api/serviceAgreements'
            self.apiServiceOfferingsURL = 'http://' + self.appServerName + ':' + self.appServerAPIPort + '/api/serviceofferings'
            self.apiServiceHoursURL = 'http://' + self.appServerName + ':' + self.appServerAPIPort + '/api/serviceHours'
            self.apiCompanyHolidaysURL = 'http://' + self.appServerName + ':' + self.appServerAPIPort + '/api/companyHolidays'
            self.apiServiceTerritoriesURL = 'http://' + self.appServerName + ':' + self.appServerAPIPort + '/api/serviceTerritories'
            self.adminUsersURL = 'http://' + self.appServerName + ':' + self.appServerAdminPort + '/administration/users'
            self.adminTenantAdministratorsURL = 'http://' + self.appServerName + ':' + self.appServerAdminPort + '/administration/tenantadministrator'
            self.apiTechniciansURL = 'http://' + self.appServerName + ':' + self.appServerAPIPort + '/api/technicians'
            self.apiTeamsURL = 'http://' + self.appServerName + ':' + self.appServerAPIPort + '/api/teams'
            self.apiDuplicateEmailURL = 'http://' + self.appServerName + ':' + self.appServerAPIPort + '/api/duplicateemployees?email='
            self.apiSalesTaxURL = 'http://' + self.appServerName + ':' + self.appServerAPIPort + '/api/serviceAgreements'
            self.apiAccountDetailsURL = 'http://' + self.appServerName + ':' + self.appServerAPIPort + '/odyssey/accounts/details/Accounts/'

    
    #def __connect__(self):

##        try:
##            requests.get("http://" + self.appServerName)
##        except:
##            print("Network Error reaching " + self.appServerName)
##            sys.exit("Network Error reaching " + self.appServerName)
##
##        response = requests.get("http://" + self.appServerName)
##        if response.status_code > 204:
##            print("Network Error reaching " + self.appServerName + " Status Code = " + str(response.status_code))
##            sys.exit("Error reaching " + self.appServerName + " Status Code = " + str(response.status_code))



    def validate(self):
        tenantSourceFile = self.filePath + 'tenants/' + self.scriptFile

        if os.path.exists(tenantSourceFile) == False:
            print('Source file (' + tenantSourceFile +  ' not found - quitting')
            sys.exit()
        else:
            print('Opening main test script file: ' + tenantSourceFile)

        self.scriptDict = []
        with open(tenantSourceFile, mode='r') as infile:
            dictReader = csv.DictReader(infile)
            for row in dictReader:
                self.scriptDict.append(row)

        emailDomain = '@mds.mds'

#        csvFileValidator = csv.DictReader(open(tenantSourceFile))

        for row in self.scriptDict:
            print('Validating source file...')
            print row["companyName"]
            try:
                companyName = str(row["companyName"])
                adminName = str(row["name"])
                adminEmail = str(row["emailAddress"])
                licenses = int(row["licenses"])
                workOrderNumberSeed = int(row["workOrderNumberSeed"])
                invoiceNumberSeed = int(row["invoiceNumberSeed"])
                emailDomain = str(row["Email_Domain"])

                companyHoursFile = str(row["Hours"])
                companyHolidaysFile = str(row["Holidays"])
                companyTerritory = str(row["Territories"])
                employeesList = str(row["Employees"])
                servicesList = str(row["Services"])
                teamsList = str(row["Teams"])
                accountsList = str(row["Accounts"])
                #accountswithAgreements = str(row["AccountswithAgreements"])
                agreementsPerDay = int(row["AgreementsPerDay"])
                agreementsDelay = int(row["AgreementDelayinSeconds"])
            except:
                print('Source file incomplete, check all rows against format of template.csv')
                sys.exit()

            if os.path.isfile(self.filePath + 'companyhours/' + companyHoursFile) == True:
                print('Processing company hours from: ' + companyHoursFile)
            else:
                print('Using default file! Company hours file (' + self.filePath + companyHoursFile + ') not found.')
                print('')
                sys.exit()

            if os.path.isfile(self.filePath + 'holidays/' + companyHolidaysFile) == True:
                print('Processing company holidays from: ' + companyHolidaysFile)
            else:
                print('Using default file! Company holidays file (' + self.filePath + companyHolidaysFile + ') not found.')
                companyHolidaysFile = "_default"
                sys.exit()

            if os.path.isfile(self.filePath + 'territories/' + companyTerritory) == True:
                print('Processing territories file from: ' + companyTerritory)
            else:
                print('Using default file! Company territories file (' + self.filePath + companyTerritory + ') not found.')
                print('Quitting script')
                sys.exit()

            if os.path.isfile(self.filePath + 'employees/' + employeesList) == True:
                print('Processing employees from: ' + employeesList)
            else:
                print('Using default file! Company employees file (' + self.filePath + employeesList + ') not found.')


            if os.path.isfile(self.filePath + 'services/' + servicesList) == True:
                print('Processing services from: '  + servicesList)
            else:
                print('Using default file! Company services file (' + self.filePath + servicesList + ') not found.')


            if os.path.isfile(self.filePath + 'teams/' + teamsList) == True:
                print('Processing teams from: '  + teamsList)
            else:
                print('Using default file! Company teams file (' + self.filePath + teamsList + ') not found.')


            if accountsList == 'None' or accountsList == '':
                print('No accounts-only file to import, step will be skipped')
            else:
                if os.path.isfile(self.filePath + 'accounts/' + accountsList) == True:
                    print('Processing accounts list from: '  + accountsList)
                else:
                    print('Accounts file (' + self.filePath + accountsList + ') not found.')


            if agreementsPerDay == '0':
                print('No accounts with agreements file to import, step will be skipped')
            else:
                print("Accounts will be created with " + str(agreementsPerDay) + " agreements per day.")
#                 if os.path.exists(self.filePath + 'accounts/' + accountswithAgreements) == True:
#                     print('Company accounts with agreements file exists for: ' + companyName)
#                 else:
#                     print('Company accounts with agreements file does not exist for: ' + companyName)
#                     print('Quitting script')
#                     sys.exit()
            print('Import file is valid')

    def createOneTenant(self):
        pass

    def createTenants(self, createAll = True, finish = True, createAccounts = True, overWrite = True):
        #createAll will create all tenants in the input file - False will create 1 tenant
        #finish will set up holidays, hours, etc - False will not
        #createAccounts will create the accounts in the csv - False will not
        #overWrite will overWrite existing tenants - False will create a new tenant admin email to create a new tenant

        tenantSourceFile = self.filePath + 'tenants/' + self.scriptFile

        if os.path.exists(tenantSourceFile) == False:
            print('Source file does not exist - quitting')
            sys.exit()
        else:
            print('Source File Found')

        csvFileReader = csv.DictReader(open(tenantSourceFile))
        i = 0
        for row in csvFileReader:
            i = i+1
            self.loginAsOdysseyAdmin = True
            companyName = str(row["companyName"])
            tenantAdminName = str(row["name"])
            tenantAdminEmail = str(row["emailAddress"])
            licenses = int(row["licenses"])
            workOrderNumberSeed = int(row["workOrderNumberSeed"])
            invoiceNumberSeed = int(row["invoiceNumberSeed"])
            self.emailDomain = str(row["Email_Domain"])
            companyHoursFile = str(row["Hours"])
            companyHolidaysFile = str(row["Holidays"])
            companyTerritory = str(row["Territories"])
            employeesList = str(row["Employees"])
            servicesList = str(row["Services"])
            teamsList = str(row["Teams"])
            accountsList = str(row["Accounts"])
            #accountswithAgreements = str(row["AccountswithAgreements"])
            agreementsPerDay = int(row["AgreementsPerDay"])
            agreementsDelay = int(row["AgreementDelayinSeconds"])

            #__odysseyAdminSession__ = __odysseyAdmin__()
            #__odysseyAdminSession__.setAdminEnvironmentURLs('QA')
            tenant = self.createTenant(tenantAdminName, companyName, tenantAdminEmail, 5, 1000, 1000)

            #__finishTenant__ = odysseyAccounts()
           # __finishTenant__.setEnvironmentURLs("QA")
#             while len(str(__getToken__(self.tenantAdminURL, tenantAdminEmail, self.tenantAdminPassword))) <= 100:
#                 print ('Unable to authenticate user, waiting 5 seconds...')
            time.sleep(5)

            # Allow this to be none
            self.loginAsOdysseyAdmin = False
            if finish:
                self.setCompanyHours(companyHoursFile)
                self.setCompanyHolidays(companyHolidaysFile)        # Allow this to be none
                self.setCompanyTerritory(companyTerritory)
                #self.populateEmployees(employeesList)
                self.populateServices(servicesList)
                self.populateTeams(teamsList)

            if createAccounts:
                if accountsList == 'None' or accountsList == '':
                    print ('No accounts-only file to import, step will be skipped')
                else:
                    if self.consoleVerbose >= 1: print("Adding accounts from " + accountsList)
                    self.__createAccounts__(accountsList)
#             if agreementsPerDay == '25':
#                 print ('No accounts with agreements file to import, step will be skipped')
#             else:
#                 self.createAgreements('KearnyJerseyCity.csv', agreementsPerDay, agreementsDelay, True)
#
#             #finish tenant creation
#             #setAdminAndTenantID(tenantAdminEmail)
            #emailDomain = emailDomain


            if i==1 and createAll == False:
                break




#class __odysseyAdminSession__():
#     Username = self.adminUserName
#     Password = 'letmein123'
#     logFilePathAdmin = "//mds-fs01/pitcrew/api_testing/Logs/Administration/"

#     def __setAdminEnvironment__(self, env):
#         if env.lower() == 'qa':
#             self.appServerName = 'ngp-qa-web'
#             self.appServerAdminPort = '86'
#             self.appServerAPIPort = '85'
#         if env.lower() == 'localhost':
#             self.appServerName = 'localhost'
#             self.appServerAdminPort = '86'
#             self.appServerAPIPort = '85'
#         self.adminTokenURL = 'http://' + self.appServerName + ':' + self.appServerAdminPort + '/administration/token'
#         self.adminTenantsURL = 'http://' + self.appServerName + ':' + self.appServerAdminPort + '/administration/tenants'
#         self.adminSchedulingLicensingURL = 'http://' + self.appServerName + ':' + self.appServerAdminPort + '/administration/schedulinglicensing/'

    def createTenant(self, tenantAdminName, CompanyName, tenantAdminEmail, LicenseCount, wordOrderNSeedumber, invoiceNumberSeed, TenantType):
        logFileName = self.__createAdminLogFileName__()

        post_body_tenant = { \
            'name': tenantAdminName, \
            'companyName': CompanyName, \
            'emailAddress': tenantAdminEmail, \
            'licenses': LicenseCount, \
            'type': TenantType, \
            'active': True, \
            'isNew': True, \
            'workOrderNumberSeed': wordOrderNSeedumber, \
            'invoiceNumberSeed': invoiceNumberSeed, \
            }


        self.tenantAdminEmail = tenantAdminEmail
        createTenantsURL = 'http://' + self.appServerName + ':' + self.appServerAdminPort + '/administration/tenants'
        tenantPayload = json.dumps(post_body_tenant)
        tenantResults = {}
        tenantResults = self.__postAPI__(self.createTenantsURL, tenantPayload, logFileName)



        if tenantResults["statusCode"] == 200:

            pass

        elif tenantResults["statusCode"] == 409:
            self.getDBID()
            if self.consoleVerbose >= 1: print("Tenant already exists with tenantID: " + self.tenantID)

        else:
            print("Error: " + tenantResults["content"])
            return()


        post_body_scheduling = { \
        'id': '00000000-0000-0000-0000-000000000000', \
        'voloAPIKey': self.voloAPIKey, \
        'schedulingType': 0 }

        schedulingPayload = json.dumps(post_body_scheduling)
        schedulingLicensingFullURL = self.adminSchedulingLicensingURL + str(tenantResults["id"])
        SchedulingConfigResults = self.__postAPI__(schedulingLicensingFullURL, schedulingPayload, logFileName)

    def __createAdminLogFileName__(self):
        i = datetime.datetime.now()
        dt = i.strftime('%Y%m%d-%H%M%S')
        logFileCalc = 'Administration' + "_" + dt + ".tsv"
        fullLogFileName = self.logFilePathAdmin + logFileCalc

        return fullLogFileName




    def __postAPI__(self, url, payload, logFileName):

        results = {}
        output = requests.post(url, data=json.dumps(payload), headers=self.headers)
        (str(output.status_code))
        
        if output.status_code == 401: # or output.status_code == 500:
            if self.consoleVerbose >= 1: print("Got a " + str(output.status_code) + " from " + url)
            token = self.__getToken__()
            if self.consoleVerbose >= 1: print("got a new token: " + token)
            self.headers = {'content-type': 'application/json', 'Authorization' : token}
            output = requests.post(url, payload, headers=self.headers)

        if output.status_code == 200:
            jsonResponse = output.json()
            results["id"] = jsonResponse["id"].encode("ascii")
        else:
            results["id"] = ""

        results["content"] = output.content
        results["statusCode"] = output.status_code

        log_output = url + "\t" + str(output.status_code) +  "\t" + str(output.elapsed) + "\t" + str(payload) + "\t" + results["id"]  + '\n'

        try:
            logFile = open(logFileName, 'a')
        except:
            print("Failed to open to log file")
        try:
            logFile.write(log_output)
        except:
            print("Failed to write to log file")
        if self.consoleVerbose >= 2: print('Logging API post: ' + log_output)

        return(results);

    def __getAPI__(self, url, params):

        results = {}
        output = requests.get(url, params=params, headers=self.headers)
        if output.status_code == 401: #or output.status_code == 500:
            if self.consoleVerbose >= 1: print("Got a " + str(output.status_code) + " from " + url)
            token = self.__getToken__()
            if self.consoleVerbose >= 1: print("got a new token: " + token)
            self.headers = {'content-type': 'application/json', 'Authorization' : token}
            output = requests.get(url, params=params, headers=self.headers)
            #print(str(output.status_code))

        if output.status_code == 200:
            jsonResponse = output.json()
            try:
                results["id"] = jsonResponse["id"].encode("ascii")
            except:
                results["id"] = ""

        results["content"] = output.content
        results["statusCode"] = output.status_code
        return(results)

    def getAccounts(self):

        results = {}
        params = ''
        output = requests.get(self.apiAccountsURL , params=params, headers=self.headers)
        print(str(output.status_code))
        if output.status_code == 401 or output.status_code == 500:
            if self.consoleVerbose >=1: print("Got a " + str(output.status_code) + " from " + self.apiAccountsURL)
            token = self.__getToken__()
            if self.consoleVerbose >= 1: print("got a new token: " + token)
            self.headers = {'content-type': 'application/json', 'Authorization' : token}
            output = requests.get(self.apiAccountsURL, params=params, headers=self.headers)
            print(str(output.status_code))

        if output.status_code == 200:
            jsonResponse = output.json()
            self.accountList =  jsonResponse
        else:
            self.accountList =  ""


    def getAccountDetails(self,accountNumber):

        results = {}
        params = ''
        accountNumber = str(accountNumber)
        output = requests.get(self.apiAccountDetailsURL + accountNumber , params=params, headers=self.headers)
        print(str(output.status_code))
        if output.status_code == 401 or output.status_code == 500:
            if self.consoleVerbose >=1: print("Got a " + str(output.status_code) + " from " + self.apiAccountsURL)
            token = self.__getToken__()
            if self.consoleVerbose >= 1: print("got a new token: " + token)
            self.headers = {'content-type': 'application/json', 'Authorization' : token}
            output = requests.get(self.apiAccountDetailsURL + accountNumber, params=params, headers=self.headers)
            print(str(output.status_code))

        if output.status_code == 200:
            jsonResponse = output.json()
            self.accountDetails =  jsonResponse
            return(jsonResponse)
        elif output.status_code == 500:
             self.accountDetails =  {}
             return()
        else:
            self.accountDetails =  ""



    def __setAdminAndTenantID__(self, email):
        postHeaders = {}
        postPayload = "grant_type=password&username=" + email + "&password=letmein123&scope=marathon_odyssey"
        response = requests.post(self.apiTokenURL, postPayload, headers=postHeaders)
        try:
            self.tenantID = response.json()['tenantId']
            self.AdminEmail = email
            result = 'Success'
        except:
            result = 'Failure'
        return(result);

    def __createLogFileName__(self, functionCalling):
        i = datetime.datetime.now()
        dt = i.strftime('%Y%m%d-%H%M%S')
        logFolderName = self.tenantAdminEmail
        logFolderName = logFolderName.replace('@', '_')
        logFolderName = logFolderName.replace('-', '_')
        logFolderName = logFolderName.replace('.', '_')
        if os.path.exists(self.logFilePath + logFolderName) == False:
            os.mkdir(self.logFilePath + logFolderName)
        logFileCalc = functionCalling + "_" + dt + ".tsv"
        fullLogFileName = self.logFilePath + logFolderName + '/' + logFileCalc

        return fullLogFileName;

    def __getToken__(self):
        if self.loginAsOdysseyAdmin:
            userName = self.sysAdminEmail
            authURL = self.sysAdminTokenURL
            scope = "&scope=marathon_admin"
            password = self.sysAdminPassword
        else:
            userName = self.tenantAdminEmail
            authURL = self.tenantAdminTokenURL
            scope = "&scope=marathon_odyssey"
            password = self.tenantAdminPassword

        postPayload = "grant_type=password&username=" + userName + "&password=" + password + scope

        response = requests.post(authURL, postPayload, headers=self.headers)
        
        
        time.sleep(20)
        
        try:
            accessToken = str(response.json()["access_token"])
            fullAccessToken = "Bearer " + accessToken
        except:
            fullAccessToken = ''
        return(fullAccessToken);
    pass



    def setCompanyHours(self, companyHoursInJSON):
        if self.consoleVerbose >= 1: print("Setup the Hours")
        if self.consoleVerbose >= 1: print("Creating Tenants is" + str(self.loginAsOdysseyAdmin))
        logFileName = self.__createLogFileName__('setCompanyHours')
        companyHoursSourceFile = self.filePath + 'CompanyHours/' + companyHoursInJSON
        jsonCompanyHours = open(companyHoursSourceFile, 'rb')
        payloadCompanyHours = jsonCompanyHours.read()

        companyHoursResults = self.__postAPI__(self.apiServiceHoursURL, payloadCompanyHours, logFileName);


    def setCompanyHolidays(self, CompanyHolidaysInJSON):
        if self.consoleVerbose >= 1: print("Setup the Holidays")
        logFileName = self.__createLogFileName__('setHolidays')
        holidaysSourceFile = self.filePath + 'Holidays/' + CompanyHolidaysInJSON
        jsonHolidays = open(holidaysSourceFile, 'rb')
        payloadHolidays = jsonHolidays.read()

        companyHolidaysResults = self.__postAPI__(self.apiCompanyHolidaysURL, payloadHolidays, logFileName);



    def setCompanyTerritory(self, companyTerritoryInJSON):
        if self.consoleVerbose >= 1: print("Setup the Territory")
        logFileName = self.__createLogFileName__('setTerritory')
        territorySourceFile = self.filePath + 'Territories/' + companyTerritoryInJSON
        jsonTerritory = open(territorySourceFile, 'rb')
        payloadTerritory = jsonTerritory.read()

        companyTerritoryResults = self.__postAPI__(self.apiServiceTerritoriesURL, payloadTerritory, logFileName);

    def populateServices(self, csvFile):
        if self.consoleVerbose >= 1: print("Setup the Services")
        logFileName = self.__createLogFileName__('CreateServices')
        serviceSourceFile = self.filePath + 'Services/' + csvFile
        csvFileReader = csv.DictReader(open(serviceSourceFile))

        for row in csvFileReader:
            intFrequency = 0

            if str(row["Frequency"]) == 'One Time':
                intFrequency = 0
            if str(row["Frequency"]) == 'Weekly':
                intFrequency = 1
            if str(row["Frequency"]) == 'Monthly':
                intFrequency = 2
            if str(row["Frequency"]) == 'Quarterly':
                intFrequency = 3

            post_body_service = { \
                'Name': str(row["Name"]), \
                'Duration': int(row["Duration (Minutes)"]) * 60000, \
                'Frequency': intFrequency ,\
                'Price': int(row["Price"]),\
                }


            servicePayload = json.dumps(post_body_service)

            serviceResults = self.__postAPI__(self.apiServiceOfferingsURL, servicePayload, logFileName);




    def populateEmployees(self, csvFile):
        if self.consoleVerbose >= 1: print("Setup the Employees")
        employeeSourceFile = self.filePath + 'Employees/' + csvFile
        csvFileReader = csv.DictReader(open(employeeSourceFile))
        logFileName = self.__createLogFileName__('CreateEmployees')

        for row in csvFileReader:
            userIDfromResponse = ''
            post_body_admin = ''
            post_body_technician = ''

            post_body_user = { \
            'email': str(row["First Name"]) + str(row["Last Name"]) + self.emailDomain, \
            'name': str(row["First Name"]) + ' ' + str(row["Last Name"]), \
            'password': str(row["Password"]), \
            "imageUrl": str(row["avatarURL"]), \
            'tenantId': self.tenantID}

            userPayload = json.dumps(post_body_user)
            jsonResponseFromEmployee = self.__postAPI__(self.adminUsersURL, userPayload, logFileName)

            if str(row["Role"]) == 'Administrator':
                post_body_admin = {'userID': str(jsonResponseFromEmployee['id'])}

                adminPayload = json.dumps(post_body_admin)
                jsonResponseFromAdmin = self.__postAPI__(self.adminTenantAdministratorsURL, adminPayload, logFileName)

            if str(row["Role"]) == 'Technician':
                post_body_technician = { \
                'callsign': str(row["CallSign"]), \
                'endingAddress': \
                    {'lineOne': str(row["EndingAddress.LineOne"]), \
                    'city': str(row["EndingAddress.City"]), \
                    'state': str(row["EndingAddress.State"]), \
                    'stateAbbreviation': str(row["EndingAddress.StateAbbreviation"]), \
                    'postalCode': str(row["EndingAddress.postalCode"]), \
                    'country': str(row["EndingAddress.Country"]), \
                    'latitude': float(row["EndingAddress.Latitude"]), \
                    'longitude': float(row["EndingAddress.Longitude"]),\
                    },\
                'startingAddress': \
                    {'lineOne': str(row["StartingAddress.LineOne"]), \
                    'city': str(row["StartingAddress.City"]), \
                    'state': str(row["StartingAddress.State"]), \
                    'stateAbbreviation': str(row["StartingAddress.StateAbbreviation"]), \
                    'postalCode': str(row["StartingAddress.postalCode"]), \
                    'country': str(row["StartingAddress.Country"]), \
                    'latitude': float(row["StartingAddress.Latitude"]), \
                    'longitude': float(row["StartingAddress.Longitude"]),\
                    },\
                'name': str(row["First Name"]) + ' ' + str(row["Last Name"]), \
                "imageUrl": str(row["avatarURL"]), \
                "color": { \
                    "hue": float(row["hue"]), \
                    "saturation": float(row["saturation"]), \
                    "luminance": float(row["luminance"]) \
                    }, \
                'userID': str(jsonResponseFromEmployee['id'])}

                technicianPayload = json.dumps(post_body_technician)
                jsonResponseFromTechnician = self.__postAPI__(self.apiTechniciansURL, technicianPayload, logFileName);
    pass

    def populateTeams(self, csvFile):
        teamSourceFile = self.filePath + 'Teams/' + csvFile
        csvFileReader = csv.DictReader(open(teamSourceFile))
        logFileName = self.__createLogFileName__('CreateTeams')

        for row in csvFileReader:
            post_body_team = { \
                'callsign': str(row["CallSign"]), \
                'isNew': str(True), \
                'name': str(row["Team Name"]),\
                'technicians': [] , \
                'endingAddress': \
                    {'lineOne': str(row["EndingAddress.LineOne"]), \
                    'city': str(row["EndingAddress.City"]), \
                    'state': str(row["EndingAddress.State"]), \
                    'stateAbbreviation': str(row["EndingAddress.StateAbbreviation"]), \
                    'postalCode': str(row["EndingAddress.postalCode"]), \
                    'country': str(row["EndingAddress.Country"]), \
                    'latitude': float(row["EndingAddress.Latitude"]), \
                    'longitude': float(row["EndingAddress.Longitude"]),\
                    },\
                'startingAddress': \
                    {'lineOne': str(row["StartingAddress.LineOne"]), \
                    'city': str(row["StartingAddress.City"]), \
                    'state': str(row["StartingAddress.State"]), \
                    'stateAbbreviation': str(row["StartingAddress.StateAbbreviation"]), \
                    'postalCode': str(row["StartingAddress.postalCode"]), \
                    'country': str(row["StartingAddress.Country"]), \
                    'latitude': float(row["StartingAddress.Latitude"]), \
                    'longitude': float(row["StartingAddress.Longitude"])}, \
                }

            teamPayload = json.dumps(post_body_team)
            teamResults = self.__postAPI__(self.apiTeamsURL, teamPayload, logFileName);
        pass

    def createAgreements(self, csvFile, agreementsPerDay , delayBetweenAccountCreationinSeconds, AssertAgreements):
            #accountSourceFile = self.filePath + 'Accounts/' + csvFile
            #csvFileReader = csv.DictReader(open(accountSourceFile))
            today_date = datetime.date.today()
            initialCommitmentWindowStart = datetime.datetime.now()
            initialCommitmentWindowEnd = datetime.datetime.now()
            initialCommitmentWindowStart_iso = ''
            initialCommitmentWindowEnd_iso = ''
            countOfAgreements = 0
            logFileName = self.__createLogFileName__('CreateAccountsWithAgreements')

            requestServices = requests.get(self.apiServiceOfferingsURL, headers=self.headers)
            services = requestServices.json()

            #get accounts list from the api
            accounts = self.getAccounts()
            #from account in accounts
                #get accountID
                #get addressID
                #get contactID
                #get contact Name

            for account in accounts:
        #             post_body_account = { \
        #                 'address': { \
        #                     'lineOne': str(row["Address 1"]), \
        #                     'city': str(row["City"]), \
        #                     'state': str(row["State"]), \
        #                     'stateAbbreviation': str(row["State Abbreviation"]), \
        #                     'postalCode': str(row["Zip"]), \
        #                     'country': str(row["Country"]), \
        #                     'latitude': str(row["Latitude"]), \
        #                     'longitude': str(row["Longitude"])\
        #                     }, \
        #                 'contact': { \
        #                     'name': str(row["Contact Name"]) \
        #                 },
        #                 'isNew': True, \
        #                 'name': str(row["Company Name"])\
        #             }
        #
        #             accountPayload = json.dumps(post_body_account)
        #             accountResults = self.__postAPI__(self.apiAccountsURL, accountPayload, logFileName)

                initialCommitmentWindowStart_iso = initialCommitmentWindowStart.strftime("%Y-%m-%dT00:15:00")
                initialCommitmentWindowEnd_iso = initialCommitmentWindowEnd.strftime("%Y-%m-%dT23:45:00")

                todayDateFormatted = today_date.strftime("%Y-%m-%d")

                post_body_agreement = {
                    "accountId" : str(accountResults['id']), \
                        "billingAddress" : { 'city': str(row["City"]), \
                              "country" : str(row["Country"]), \
                              "id" : str(accountResults['address']['id']),\
                              'latitude': str(row["Latitude"]), \
                              'lineOne': str(row["Address 1"]), \
                              "lineTwo" : "",\
                              'longitude': str(row["Longitude"]),\
                              'postalCode': str(row["Zip"]), \
                              'state': str(row["State"]), \
                        'stateAbbreviation': str(row["State Abbreviation"]) \
                            },\
                      "contact" : { "email" : "",\
                          "id" : str(accountResults['contact']['id']),\
                          "name" : str(accountResults['contact']['name']),\
                          "phone" : ""\
                        },\
                      "effectiveDate" : todayDateFormatted,\
                      "initialCommitmentTech" : "technicians/1",\
                      "initialCommitmentWindowEnd" : initialCommitmentWindowEnd_iso,\
                      "initialCommitmentWindowStart" : initialCommitmentWindowStart_iso,\
                      "invoiceSchedule" : 0,\
                      "issue" : "",\
                      "name" : str(row["Company Name"]),\
                      "preferredEndTime" : "23:59:59",\
                      "preferredStartTime" : "00:00:00",\
                      "serviceAddress" : { 'city': str(row["City"]), \
                          "country" : str(row["Country"]), \
                          "id" : str(accountResults['address']['id']), \
                          "latitude" : str(row["Latitude"]), \
                          "lineOne" : str(row["Address 1"]), \
                          "lineTwo" : "",\
                          "longitude" : str(row["Longitude"]),\
                          "postalCode" : str(row["Zip"]), \
                          "state" : str(row["State"]), \
                          "stateAbbreviation" : str(row["State Abbreviation"]) \
                        },\
                      "services" : [ { "duration" : int(services [0]['duration']),\
                            "offeringId" : str(services [0]['id']),\
                            "price" : int(services [0]['price'])\
                          } ],\
                      "zipTaxGeoData" : { "citySalesTax" : 0,\
                          "cityTaxCode" : "2",\
                          "cityUseTax" : 0,\
                          "countySalesTax" : 0.019999999552965,\
                          "countyTaxCode" : "2",\
                          "countyUseTax" : 0.019999999552965,\
                          "districtSalesTax" : 0,\
                          "districtUseTax" : 0,\
                          "geoCity" : "MIDDLE CITY EAST",\
                          "geoCounty" : "PHILADELPHIA",\
                          "geoPostalCode" : "19102",\
                          "geoState" : "PA",\
                          "stateSalesTax" : 0.059999998658895,\
                          "stateUseTax" : 0.059999998658895,\
                          "taxSales" : 0.079999998211861,\
                          "taxUse" : 0.079999998211861,\
                          "txbFreight" : "Y",\
                          "txbService" : "Y"\
                        }\
                    }

                agreementPayload = json.dumps(post_body_agreement)
                agreementResults = self.__postAPI__(self.apiAgreementsURL, agreementPayload, logFileName)


                countOfAgreements += 1

                if countOfAgreements >= agreementsPerDay:
                    print ("Advancing Day")
                    countOfAgreements = 0
                    initialCommitmentWindowStart = initialCommitmentWindowStart + datetime.timedelta(days=1)
                    initialCommitmentWindowEnd = initialCommitmentWindowEnd + datetime.timedelta(days=1)
                time.sleep(delayBetweenAccountCreationinSeconds)

                if AssertAgreements == True:
                    self.logAgreementAssertion(self.tenantID, str(accountResults['id']), str(row["Company Name"]), str(initialCommitmentWindowStart.strftime("%Y-%m-%d")), self.dbServer, self.appServerName)

                if self.consoleVerbose  >= 1: print('Count Of Agreements: ' + str(countOfAgreements) + '\n')


    def __createAccounts__(self, csvFile):
        accountSourceFile = self.filePath + 'Accounts/' + csvFile
        csvFileReader = csv.DictReader(open(accountSourceFile))
        logFileName = self.__createLogFileName__('CreateAccounts')

        for row in csvFileReader:
            post_body_account = { \
                    'address': { \
                        'lineOne': str(row["Address 1"]), \
                        'city': str(row["City"]), \
                        'state': str(row["State"]), \
                        'stateAbbreviation': str(row["State Abbreviation"]), \
                        'postalCode': str(row["Zip"]), \
                        'country': str(row["Country"]), \
                        'latitude': str(row["Latitude"]), \
                        'longitude': str(row["Longitude"])\
                        }, \
                    'contact': { \
                        'name': str(row["Contact Name"]) \
                    },
                    'isNew': True, \
                    'name': str(row["Company Name"])\
                }

            accountPayload = json.dumps(post_body_account)

            accountResults = self.__postAPI__(self.apiAccountsURL, accountPayload, logFileName)


    pass

    def logAgreementAssertion(self, tenant, accountId, accountName, serviceDate, dbServer, apiServer):
        assertionLogFilePath = self.filePath + 'Assertions/Agreements_' + str(datetime.datetime.now().strftime("%Y%m%d")) + '.csv'
        log_output = tenant + ',' + accountId + ',' + accountName + ',' + serviceDate + ',' + dbServer + ','+ apiServer + '\n'
        if os.path.exists(assertionLogFilePath) == False:
            assertionLogFile = open(assertionLogFilePath, 'a')
            assertionLogFile.write('Tenant,AccountID,AccountName,ServiceDate,DatabaseServer,apiServer\n')
            assertionLogFile.close()
        try:
            assertionLogFile = open(assertionLogFilePath, 'a')
        except:
            print("Failed to open to assertion log file")
        try:
            assertionLogFile.write(log_output)
        except:
            print("Failed to write to assertion log file")
        if self.consoleVerbose >= 2: print('Logging assertion: ' + log_output)


# def main():
#     newTenantGenerator = odysseyTenantGenerator()
#     newTenantGenerator.validateTenantsImportFile('tim.csv')
#     newTenantGenerator.importTenantsFromCSV('tim.csv')
#     pass
#
# if __name__ == '__main__':
#     main()

    def getDBID(self):


        response = requests.get(self.dbServerURL)
        if response.status_code > 204:
            print("Network Error reaching " + self.dbServerURL + " Status Code = " + str(response.status_code))
            sys.exit("Error reaching " + self.dbServerURL + " Status Code = " + str(response.status_code))

        #get dbid
        apiCall = "/databases/SystemAdministration/indexes/Auto/IdentityUsers/ByUserName"
        url = self.dbServerURL + apiCall
        params = "query=UserName:" + self.tenantAdminEmail
        response = requests.get(url, params = params)
        self.results = response.json()
        self.tenantID = str(self.results["Results"][0]["Claims"][0]["ClaimValue"])

    def processHarFile(self):

        #set creating tenants to false

        #get the list of files in filepath
        listofFiles = os.listdir(self.filePath)

        for fname in listofFiles:
            pathParts = os.path.splitext(fname)
            ext = pathParts[1]
            rep_file = pathParts[0]
            if ext == '.har':


                # open the extract file for p:rocessing
                #inputFile = open(self.filePath + fname, 'r')
                har = json.loads(open(self.filePath + fname).read())
                outputFilename = self.filePath + fname + "_results.txt" #add date code to this file
                outputFile = open(outputFilename, 'w')
                #sys.stdout.write(fname + '\n')
                for i in range(len(har["log"]["entries"])):
                    if har["log"]["entries"][i]["request"]["method"] == "GET":
                        line = har["log"]["entries"][i]["request"]["url"]
                        if "http://" + self.appServerName + ":" + self.appServerAPIPort in line:
                        #check if the line is a valid execution
                            #line = line.split()[1]
                            line = line.strip('\"')
                            apiCall = line.strip('\,\"')
                            #print(apiCall)
                            params = {}
                            results = self.__getAPI__(apiCall, params)
                            #print(results["statusCode"])
                            #print(re.sub('.{8}-.{4}-.{4}-.{4}-.{12}', "0000-0000-0000", results["content"]))

                            output = apiCall + '\t' + str(results["statusCode"]) + results["content"]

                        #write the results to the file

                        # = line + '\n'
                            outputFile.write(output)

    def getOdysseyAdminAuthToken(self, email, password):
        postHeaders = {}
        postPayload = "grant_type=password&username=" + email + "&password=" + password + "&scope=marathon_admin"
        response = requests.post(self.sysAdminTokenURL, postPayload, headers=postHeaders)
        try:
            accessToken = str(response.json()["access_token"])
        except:
            accessToken = ""
        fullAccessToken = "Bearer " + accessToken

        return(fullAccessToken);


    def checkForEmailInSystem(self, email):
        isDuplicated = True
        adminToken = self.getOdysseyAdminAuthToken(self.sysAdminEmail, self.sysAdminPassword)
        headers = {'content-type': 'application/json', 'Authorization' : adminToken}
        getResponse = requests.get(self.apiDuplicateEmailURL + email, headers=headers).json()

        if getResponse == True:
            print ('A user with the email ' + email + ' already exists in the Odyssey system.')
            isDuplicated = True
        else:
            print('Email address is unique')
            isDuplicated = False
        return isDuplicated


    def hasDuplicateEmployees(self, csvFilePath, emailDomain):
        duplicateEmployeeFound = False
        csvFileReader = csv.DictReader(open(csvFilePath))

        for row in csvFileReader:
            emailAddress = str(row["First Name"]) + str(row["Last Name"]) + emailDomain
            print ('Checking if email exists for ' + emailAddress)
            duplicateRecordFound = self.checkForEmailInSystem(emailAddress)
            if duplicateRecordFound == True:
                duplicateEmployeeFound = True

        return duplicateEmployeeFound

    def getAuthorizationToken(self, email, password):
        postHeaders = {}
        postPayload = "grant_type=password&username=" + email + "&password=" + password + "&scope=marathon_odyssey"
        response = requests.post(self.tenantAdminTokenURL, postPayload, headers=postHeaders)
        try:
            accessToken = str(response.json()["access_token"])
            fullAccessToken = "Bearer " + accessToken
        except:
            fullAccessToken = ''
        return(fullAccessToken);


    def setTenantID(self, email, password):
        postHeaders = {}
        postPayload = "grant_type=password&username=" + email + "&password=" + password + "&scope=marathon_odyssey"
        response = requests.post(self.tenantAdminTokenURL, postPayload, headers=postHeaders)
        try:
            self.tenantID = response.json()['tenantId']
            result = True
        except:
            result = False
        return(result);

    def callAPIreturningJSON(self, url, headers, payload, logFileName):
            jsonResponse = ''

            output = requests.post(url, payload, headers=headers)

            if output.status_code == 401:
                return (401)

            if output.status_code == 500:       # This shouldn't be here but prod
                return (401)                    # returns 500 for some reason when
                                                # it should return 401
            if output.status_code == 200:
                jsonResponse = output.json()
                id = jsonResponse["id"].encode("ascii")
            else:
                id = output.content


            log_output = url + "\t" + str(output.status_code) +  "\t" + str(output.elapsed) + "\t" + str(payload) + "\t" + id  + '\n'
            try:
                logFile = open(logFileName, 'a')
            except:
                print("Failed to open to log file")
            try:
                logFile.write(log_output)
            except:
                print("Failed to write to log file")
            if self.consoleVerbose >= 1: print ('Logging API post: ' + log_output)

            return(jsonResponse);


    def populateAccountsWithAgreements(self, csvFile, agreementsPerDay, delayBetweenAccountCreationinSeconds, dayOffset, accountsOnly):
        accountSourceFile = self.filePath + 'Accounts/' + csvFile
        csvFileReader = csv.DictReader(open(accountSourceFile))
        today_date = datetime.date.today()

        initialCommitmentWindowStart = datetime.datetime.now()
        initialCommitmentWindowEnd = datetime.datetime.now()
        initialCommitmentWindowStart_iso = ''
        initialCommitmentWindowEnd_iso = ''

        countOfAgreementsForDay = 0
        totalCountOfAgreements = 0
        agreementSeed = 0
        invoiceScheduleSeed = 0
        maxServicesToSeed = 0

        headers = {'content-type': 'application/json', 'Authorization' : (odyssey.getAuthorizationToken(self, self.tenantAdminEmail, self.tenantAdminPassword))}
        logFileName = self.__createLogFileName__('CreateAccountsWithAgreements')

        initialCommitmentWindowStart = initialCommitmentWindowStart + datetime.timedelta(days=float(dayOffset))
        initialCommitmentWindowEnd = initialCommitmentWindowEnd + datetime.timedelta(days=float(dayOffset))

        requestServices = requests.get(self.apiServiceOfferingsURL, headers=headers)
        services = requestServices.json()
        maxServicesToSeed = len(services)

        for row in csvFileReader:
            accountBodyValid = True
            agreementBodyValid = True
            headers = {'content-type': 'application/json', 'Authorization' : (odyssey.getAuthorizationToken(self, self.tenantAdminEmail, self.tenantAdminPassword))}

            try:
                post_body_account = { \
                    "defaultServiceLocation": { \
                        "address": { \
                            'lineOne': str(row["Address 1"]), \
                            'city': str(row["City"]), \
                            'state': str(row["State"]), \
                            'stateAbbreviation': str(row["State Abbreviation"]), \
                            'postalCode': str(row["Zip"]), \
                            'country': str(row["Country"]), \
                            'latitude': str(row["Latitude"]), \
                            'longitude': str(row["Longitude"])\
                        } \
                    }, \
                    "contact": [ \
                        { \
                            "name": str(row["Contact Name"]), \
                            "emails": [ \
                                { \
                                    "name": "Main", \
                                    "contactValue": str(row["Email"]), \
                                    "preferred": True \
                                } \
                            ], \
                            "phones": [ \
                                { \
                                    "name": "Main", \
                                    "contactValue": str(row["Phone Number"]), \
                                    "preferred": False \
                                } \
                            ], \
                            "customs": [], \
                            "contactType": "Service" \
                        }, \
                        { \
                            "name": str(row["Contact Name"]), \
                            "emails": [ \
                                { \
                                    "name": "Main", \
                                    "contactValue": str(row["Email"]), \
                                    "preferred": True \
                                } \
                            ], \
                            "phones": [ \
                                { \
                                    "name": "Main", \
                                    "contactValue": str(row["Phone Number"]), \
                                    "preferred": False \
                                } \
                            ], \
                            "customs": [], \
                            "contactType": "Billing" \
                        } \
                    ], \
                    "contactAssociations": [], \
                    "isNew": True, \
                    "name": str(row["Company Name"])\
                }

            except:
                print('Failed to generate post body')
                accountBodyValid = False


            if accountBodyValid == True:
                print ('Creating account for: ' + str(row["Company Name"]))
                accountPayload = json.dumps(post_body_account)
                jsonResponseFromAccount = odyssey.callAPIreturningJSON(self, self.apiAccountsURL, headers, accountPayload, logFileName)

                if accountsOnly == False:

                    initialCommitmentWindowStart_iso = initialCommitmentWindowStart.strftime("%Y-%m-%dT00:15:00")
                    initialCommitmentWindowEnd_iso = initialCommitmentWindowEnd.strftime("%Y-%m-%dT23:45:00")

                    requestSalesTax = requests.get(self.apiSalesTaxURL + '?City=' + str(row["City"]) + '&postalCode=' + str(row["Zip"]) + '&state=' + str(row["State Abbreviation"]), headers=headers)
                    taxes = requestSalesTax.json()

                    todayDateFormatted = today_date.strftime("%Y-%m-%d")

                    try:
                        post_body_agreement = { \
                            "accountId" : str(jsonResponseFromAccount['id']), \
                            "serviceLocation": { \
                                "id": str(jsonResponseFromAccount['defaultServiceLocation']['id']), \
                                "address": { \
                                    "city" : str(jsonResponseFromAccount['defaultServiceLocation']['address']['city']), \
                                    "country" : str(jsonResponseFromAccount['defaultServiceLocation']['address']['country']), \
                                    "id" : str(jsonResponseFromAccount['defaultServiceLocation']['address']['id']), \
                                    "latitude" : str(jsonResponseFromAccount['defaultServiceLocation']['address']['latitude']), \
                                    "lineOne" : str(jsonResponseFromAccount['defaultServiceLocation']['address']['lineOne']), \
                                    "lineTwo" : str(jsonResponseFromAccount['defaultServiceLocation']['address']['lineTwo']), \
                                    "longitude" : str(jsonResponseFromAccount['defaultServiceLocation']['address']['longitude']), \
                                    "postalCode" : str(jsonResponseFromAccount['defaultServiceLocation']['address']['postalCode']), \
                                    "state" : str(jsonResponseFromAccount['defaultServiceLocation']['address']['state']), \
                                    "stateAbbreviation" : str(jsonResponseFromAccount['defaultServiceLocation']['address']['stateAbbreviation']), \
                                } \
                            }, \
                            "billingAddress": { \
                                "id": str(jsonResponseFromAccount['defaultServiceLocation']['id']), \
                                "city" : str(jsonResponseFromAccount['defaultServiceLocation']['address']['city']), \
                                "country" : str(jsonResponseFromAccount['defaultServiceLocation']['address']['country']), \
                                "latitude" : str(jsonResponseFromAccount['defaultServiceLocation']['address']['latitude']), \
                                "lineOne" : str(jsonResponseFromAccount['defaultServiceLocation']['address']['lineOne']), \
                                "longitude" : str(jsonResponseFromAccount['defaultServiceLocation']['address']['longitude']), \
                                "postalCode" : str(jsonResponseFromAccount['defaultServiceLocation']['address']['postalCode']), \
                                "state" : str(jsonResponseFromAccount['defaultServiceLocation']['address']['state']), \
                                "stateAbbreviation" : str(jsonResponseFromAccount['defaultServiceLocation']['address']['stateAbbreviation']), \
                            }, \
                            "name" : str(row["Company Name"]),\
                            "contact": [ \
                                { \
                                    "id" : str(jsonResponseFromAccount['contact'][0]['id']), \
                                    "name" : str(jsonResponseFromAccount['contact'][0]['name']), \
                                    "phones": [ \
                                        { \
                                            "id" : str(jsonResponseFromAccount['contact'][0]['phones'][0]['id']), \
                                            "name": "Main", \
                                            "contactValue": str(jsonResponseFromAccount['contact'][0]['phones'][0]['contactValue']), \
                                        } \
                                    ], \
                                    "emails": [ \
                                        { \
                                            "id" : str(jsonResponseFromAccount['contact'][0]['emails'][0]['id']), \
                                            "name": "Main", \
                                            "contactValue": str(jsonResponseFromAccount['contact'][0]['emails'][0]['contactValue']), \
                                            "preferred": True \
                                        } \
                                    ], \
                                    "customs": [], \
                                    "contactType": "Service" \
                                }, \
                                { \
                                    "id" : str(jsonResponseFromAccount['contact'][1]['id']), \
                                    "name" : str(jsonResponseFromAccount['contact'][1]['name']), \
                                    "phones": [ \
                                        { \
                                            "id" : str(jsonResponseFromAccount['contact'][1]['phones'][0]['id']), \
                                            "name": "Main", \
                                            "contactValue": str(jsonResponseFromAccount['contact'][1]['phones'][0]['contactValue']), \
                                        } \
                                    ], \
                                    "emails": [ \
                                        { \
                                            "id" : str(jsonResponseFromAccount['contact'][1]['emails'][0]['id']), \
                                            "name": "Main", \
                                            "contactValue": str(jsonResponseFromAccount['contact'][1]['emails'][0]['contactValue']), \
                                            "preferred": True \
                                        } \
                                    ], \
                                    "customs": [], \
                                    "contactType": "Billing" \
                                } \
                            ], \
                            "issue": "", \
                            "effectiveDate": todayDateFormatted,\
                            "services": [ \
                                { \
                                    "offeringId": str(services [agreementSeed]['id']),\
                                    "duration": int(services [agreementSeed]['duration']),\
                                    "price": int(services [agreementSeed]['price'])\
                                } \
                            ], \
                            "initialCommitmentWindowEnd" : initialCommitmentWindowEnd_iso,\
                            "initialCommitmentWindowStart" : initialCommitmentWindowStart_iso,\
                            "initialCommitmentTech" : "",\
                            "preferredEndTime" : "23:59:59",\
                            "preferredStartTime" : "00:00:00",\
                            "preferredDaysOfWeek": [], \
                            "invoiceSchedule" : invoiceScheduleSeed,\
                            "taxRates": { \
                                "geoPostalCode": str(taxes['results'][0]['geoPostalCode']), \
                                "geoCity": str(taxes['results'][0]['geoCity']), \
                                "geoCounty": str(taxes['results'][0]['geoCounty']), \
                                "geoState": str(taxes['results'][0]['geoState']), \
                                "taxSales": str(taxes['results'][0]['taxSales']), \
                                "taxUse": str(taxes['results'][0]['taxUse']), \
                                "txbService": str(taxes['results'][0]['txbService']), \
                                "txbFreight": str(taxes['results'][0]['txbFreight']), \
                                "stateSalesTax": str(taxes['results'][0]['stateSalesTax']), \
                                "stateUseTax": str(taxes['results'][0]['stateUseTax']), \
                                "citySalesTax": str(taxes['results'][0]['citySalesTax']), \
                                "cityUseTax": str(taxes['results'][0]['cityUseTax']), \
                                "cityTaxCode": str(taxes['results'][0]['cityTaxCode']), \
                                "countySalesTax": str(taxes['results'][0]['countySalesTax']), \
                                "countyUseTax": str(taxes['results'][0]['countyUseTax']), \
                                "countyTaxCode": str(taxes['results'][0]['countyTaxCode']), \
                                "districtSalesTax": str(taxes['results'][0]['districtSalesTax']), \
                                "districtUseTax": str(taxes['results'][0]['districtUseTax']), \
                            } \
                        } \

                    except:
                        print('Failed to generate post body')
                        #print post_body_agreement
                        agreementBodyValid = False


                    if agreementBodyValid == True:
                        print ('Creating Agreement for: ' + str(row["Company Name"]) + ' on ' + initialCommitmentWindowStart_iso + ' of type ' + str(services [agreementSeed]['name']))
                        agreementPayload = json.dumps(post_body_agreement)
                        jsonResponseFromAgreement = odyssey.callAPIreturningJSON(self, self.apiAgreementsURL, headers, agreementPayload, logFileName)

                        countOfAgreementsForDay += 1
                        totalCountOfAgreements += 1

                        if countOfAgreementsForDay > agreementsPerDay:
                            print ("Advancing Day")
                            countOfAgreementsForDay = 0
                            initialCommitmentWindowStart = initialCommitmentWindowStart + datetime.timedelta(days=1)
                            initialCommitmentWindowEnd = initialCommitmentWindowEnd + datetime.timedelta(days=1)
                        time.sleep(delayBetweenAccountCreationinSeconds)

                        print ('Count of agreements added for current day: ' + str(countOfAgreementsForDay))
                        print ('Total count of agreements added from list: ' + str(totalCountOfAgreements))

                        agreementSeed += 1
                        invoiceScheduleSeed += 1
                        if agreementSeed >= maxServicesToSeed:
                            agreementSeed = 0
                        if invoiceScheduleSeed >= 2:
                            invoiceScheduleSeed = 0


    pass


    def populateTeamsWithEmployees(self, csvFile):
        teamSourceFile = self.filePath + 'Teams/' + csvFile
        headers = {'content-type': 'application/json', 'Authorization' : (odyssey.getAuthorizationToken(self, self.tenantAdminEmail, self.tenantAdminPassword))}
        firstEmployeeSeed = 0
        secondEmployeeSeed = 1
        csvFileReader = csv.DictReader(open(teamSourceFile))
        logFileName = self.__createLogFileName__('CreateTeams')

        requestEmployees = requests.get(self.apiTechniciansURL, headers=headers)
        employeesList = requestEmployees.json()

        for row in csvFileReader:
            teamBodyValid = True
            try:
                post_body_team = { \
                    "isNew": str(True), \
                    "technicians": [ \
                        { \
                            "id": str(employeesList[firstEmployeeSeed]['id']), \
                            "name": str(employeesList[firstEmployeeSeed]['name']), \
                            "callsign": str(employeesList[firstEmployeeSeed]['callsign']), \
                            "userId": str(employeesList[firstEmployeeSeed]['userId']), \
                            "imageUrl": 'null', \
                            "color": { \
                                "hue": float(row["hue"]), \
                                "saturation": float(row["saturation"]), \
                                "luminance": float(row["luminance"]) \
                                }, \
                            "startingAddress": {}, \
                            "endingAddress": {}, \
                            "territoryId": str(employeesList[firstEmployeeSeed]['territoryId']), \
                            "vehicleId": "00000000-0000-0000-0000-000000000000", \
                            "teamId": 'null', \
                            "retired": str('False'), \
                            "_initialStartingAddress": {}, \
                            "_initialEndingAddress": {} \
                        }, \
                        { \
                            "id": str(employeesList[secondEmployeeSeed]['id']), \
                            "name": str(employeesList[secondEmployeeSeed]['name']), \
                            "callsign": str(employeesList[secondEmployeeSeed]['callsign']), \
                            "userId": str(employeesList[secondEmployeeSeed]['userId']), \
                            "imageUrl": 'null', \
                            "color": { \
                                "hue": float(row["hue"]), \
                                "saturation": float(row["saturation"]), \
                                "luminance": float(row["luminance"]) \
                                }, \
                            "startingAddress": {}, \
                            "endingAddress": {}, \
                            "territoryId": str(employeesList[secondEmployeeSeed]['territoryId']), \
                            "vehicleId": "00000000-0000-0000-0000-000000000000", \
                            "teamId": 'null', \
                            "retired": str('False'), \
                            "_initialStartingAddress": {}, \
                            "_initialEndingAddress": {} \
                        } \
                    ], \
                    "color": { \
                        "hue": float(row["hue"]), \
                        "saturation": float(row["saturation"]), \
                        "luminance": float(row["luminance"]) \
                        }, \
                    "name": str(row["Team Name"]),\
                    "imageUrl": str(row["avatarURL"]), \
                    "callsign": str(row["CallSign"]), \
                    "startingAddress": { \
                        'lineOne': str(row["StartingAddress.LineOne"]), \
                        'city': str(row["StartingAddress.City"]), \
                        'state': str(row["StartingAddress.State"]), \
                        'stateAbbreviation': str(row["StartingAddress.StateAbbreviation"]), \
                        'postalCode': str(row["StartingAddress.postalCode"]), \
                        'country': str(row["StartingAddress.Country"]), \
                        'latitude': float(row["StartingAddress.Latitude"]), \
                        'longitude': float(row["StartingAddress.Longitude"]),\
                    }, \
                    "endingAddress": { \
                        'lineOne': str(row["EndingAddress.LineOne"]), \
                        'city': str(row["EndingAddress.City"]), \
                        'state': str(row["EndingAddress.State"]), \
                        'stateAbbreviation': str(row["EndingAddress.StateAbbreviation"]), \
                        'postalCode': str(row["EndingAddress.postalCode"]), \
                        'country': str(row["EndingAddress.Country"]), \
                        'latitude': float(row["EndingAddress.Latitude"]), \
                        'longitude': float(row["EndingAddress.Longitude"]),\
                    } \
                } \

            except:
                teamBodyValid = False

            if teamBodyValid == True:
                teamPayload = json.dumps(post_body_team)
                jsonResponseFromTeams = odyssey.callAPIreturningJSON(self, self.apiTeamsURL, headers, teamPayload, logFileName)

            firstEmployeeSeed =+ 2
            secondEmployeeSeed += 2
    pass
