# -*- coding: utf-8 -*-
"""
Created on Mon Aug 12 12:24:36 2019

@author: Sandy Sun
"""

import pandas as pd
opportunity = pd.read_csv('SalesForce_Opportunity.csv',encoding='ISO-8859-1')


'''Question 1'''
#1-1 Is there a geographic location within the US that most of our individual donors come from? 

cleaned_donor = pd.ExcelFile('cleaned_contact_original_1.xlsx').parse(0) # cleaned contact df with 51 states
all_donor = cleaned_donor[(cleaned_donor.Donor__c == 1)].reset_index(drop=True)  #choose donor == 1 from contact


#1-2 distribution: Are there areas in the country we don't see any donors from?
distribute = all_donor.groupby(['MailingState','Donor_Type__c'])['Donor__c'].count().reset_index(name = 'counts')
distribute.to_excel('geographic distribution with different donor types.xlsx',index = False)

#1-3 marketing hit: Do our social media posts or fundraisers calling for donations hit these areas with little to no donors? 
# Since all states are with donors, so this question can be translated as [donors who are from social media hit/fundraiser calling /all donors who participated in activities (leadsource != null)]

#1. marketing hit (social media posts/fundraiser calling)
''' Method - based on contact'''
list_social_fundraiser = ['Donation due to Media Coverage','Phone','Web']
social_and_fundraiser = opportunity[opportunity.LeadSource.isin(list_social_fundraiser)].reset_index(drop=True) 

s_f_donor = all_donor[all_donor.Id.isin(list(social_and_fundraiser['npsp__Primary_Contact__c']))] #find out all donors that from social media/fundraiser 
numerator =  s_f_donor.groupby('MailingState')['Donor__c'].count().reset_index(name = 'counts')  #number of donor from social media/fundraiser = absolute number

all_leadsource = opportunity[(opportunity.LeadSource.isnull()==False) & (opportunity.Amount.isnull()==False)].reset_index(drop=True)
leadsource_donor = all_donor[all_donor.Id.isin(list(all_leadsource.npsp__Primary_Contact__c))]  #find out all donors that from all leadsource
denominator = leadsource_donor.groupby(['MailingState'])['Id'].count().reset_index(name = 'counts') #number of donor from each state
numerator['ratios'] = numerator.counts/denominator.counts
numerator.to_excel('makrting hitting_new.xlsx',index = False) 

#1-4 conversion rate - donors with donation behavior/donors from social media/fundraiser

'''Method - Amount != 0 '''
conversion = social_and_fundraiser[social_and_fundraiser.Amount != 0]
conversion = all_donor[all_donor.Id.isin(list(conversion['npsp__Primary_Contact__c']))]
conversion = conversion.groupby('MailingState').Id.count().reset_index(name = 'counts')
conversion['conversion rate'] = conversion['counts']/numerator['counts']                         
conversion.to_excel('conversion rate_amount_new.xlsx',index = False) 


contact = pd.read_csv('SalesForce_Contact.csv',encoding='ISO-8859-1')
account = pd.read_csv('SalesForce_Account.csv',encoding='ISO-8859-1')

'''Question 2'''
# ** Do we have an average lifespan of a monthly donor? 
monthly_donor = contact[(contact.Recurring_Donor_Frequency__c == 'Monthly') & (contact.Donor__c == 1)]
account_wo_date = account.dropna(subset=['npe01__LastDonationDate__c','npe01__FirstDonationDate__c'])
account_wo_date['lifespan'] =pd.to_datetime(account_wo_date["npe01__LastDonationDate__c"])-pd.to_datetime(account_wo_date["npe01__FirstDonationDate__c"])
monthly_lifespan = monthly_donor.merge(account_wo_date,how = "left", left_on = "AccountId",right_on = "Id")
monthly_lifespan_donor = account[account.OwnerId.isin(list(monthly_donor.Id))].reset_index(drop=True) 

# avg lifespan
avg_monthly_donor = monthly_lifespan['lifespan'].mean().days  # extract only days 567 days
monthly_lifespan['lifespan'].max() # 3089 days
monthly_lifespan['lifespan'].min() # 0 days
monthly_lifespan['lifespan_days'] = monthly_lifespan['lifespan'].apply(lambda x:x.days)
monthly_lifespan['l_year'] = pd.to_datetime(monthly_lifespan["npe01__LastDonationDate__c"]).apply(lambda x:x.year)
monthly_lifespan['s_year'] = pd.to_datetime(monthly_lifespan["npe01__FirstDonationDate__c"]).apply(lambda x:x.year)
monthly_lifespan[['npe01__FirstDonationDate__c','npe01__LastDonationDate__c','l_year','s_year']].to_excel('monthly_donor.xlsx',index = False) 

# ** Do our monthly donors give for a year and then lapse, or do they give over the course of a few years? 
# over one year donor
def over_one_year(data):
    for index, row in data.iterrows():
        if data.loc[index,'lifespan'].days > 365:
            continue
        else:
            data = data.drop(index,axis=0)
    return data          
over_oneyr_monthly_donor = over_one_year(monthly_lifespan).reset_index(drop=True)
over_oneyr_monthly_donor.shape[0]/monthly_lifespan.shape[0] #0.694

# ** Do our monthly donors who give more than one year increase their gift amount year over year?
over_oneyr_monthly_donor['growth_rate']=(over_oneyr_monthly_donor['npo02__OppAmountLastYear__c'] - over_oneyr_monthly_donor['npo02__OppAmount2YearsAgo__c'])/over_oneyr_monthly_donor['npo02__OppAmount2YearsAgo__c']
over_oneyr_monthly_donor.to_excel('over 1 year monthly_donor.xlsx',index = False) 


import pandas as pd 
opportunity = pd.read_csv('SalesForce_Opportunity.csv',encoding='ISO-8859-1')
campaign = pd.read_csv('Campaign.csv',encoding='ISO-8859-1')
contact = pd.read_csv('SalesForce_Contact.csv',encoding='ISO-8859-1')
account = pd.read_csv('SalesForce_Account.csv',encoding='ISO-8859-1')

'''Question 3'''
non_event = opportunity[(opportunity.Donation_Type__c != 'Event') & (opportunity.Donation_Type__c.isnull()==False)].reset_index(drop=True) 
event_and_null = opportunity[(opportunity.Donation_Type__c == 'Event') | (opportunity.Donation_Type__c.isnull())].reset_index(drop=True) #there is no different for shape whether we dropna(subset=['CampaignId'])

fundraiser = event_and_null[['AccountId','npsp__Primary_Contact__c','CampaignId','Donation_Type__c','Payment_Date__c','Amount']].merge(campaign[['Id','Type']],how = 'left', left_on = 'CampaignId' ,right_on = 'Id') #this merge can happen cause left join won't create more rows
fundraiser = fundraiser[fundraiser.Type == 'Fundraiser'][['AccountId','npsp__Primary_Contact__c','Payment_Date__c','Amount']]  #choose type == fundraiser 

unsolicited = pd.concat([non_event[['AccountId','npsp__Primary_Contact__c','Payment_Date__c','Amount']],fundraiser])  
unsolicited = unsolicited[unsolicited.Payment_Date__c.isnull()==False] #only choose those records with payment date
unsolicited_donor = unsolicited[unsolicited.npsp__Primary_Contact__c.isin(list(contact[contact.Donor__c==1].Id))]  #find out donors 

#3-1 What frequency do we see unsolicited (non-event or fundraiser) donors month to month? 
unsolicited_donor['Payment_Date__c'] = pd.to_datetime(unsolicited_donor.Payment_Date__c)
unsolicited_donor['year'] = unsolicited_donor.Payment_Date__c.apply(lambda x:x.year)
unsolicited_donor['month'] = unsolicited_donor.Payment_Date__c.apply(lambda x:x.month)
#unsolicited.loc[unsolicited.year<=2019,['AccountId','Payment_Date__c','year','month']].dropna(subset=['year']).groupby(['year','month']).count()
frequency = unsolicited_donor.loc[unsolicited_donor.year <= 2019,['npsp__Primary_Contact__c','AccountId','Payment_Date__c','year','month']].groupby(['year','month']).apply(lambda x:pd.Series({'num_acct':x.npsp__Primary_Contact__c.nunique()})).reset_index() #how many unique accountid donate each month
frequency.to_excel('unsolicited with all types in different month_new.xlsx',index = False)  #some accountid donate more than once a month

#3-2 Do these donors give more than once a year? - Based on opportunity
monthly_donor = contact[(contact.Recurring_Donor_Frequency__c == 'Monthly') & (contact.Donor__c == 1)]
monthly_donor = unsolicited[unsolicited.npsp__Primary_Contact__c.isin(list(monthly_donor.Id))].npsp__Primary_Contact__c.nunique() #57
quarterly_donor = contact[(contact.Recurring_Donor_Frequency__c == 'Quarterly') & (contact.Donor__c == 1)]
quarterly_donor = unsolicited[unsolicited.npsp__Primary_Contact__c.isin(list(quarterly_donor.Id))].npsp__Primary_Contact__c.nunique() #2
anuualy_donor = contact[(contact.Recurring_Donor_Frequency__c == 'Annual') & (contact.Donor__c == 1)]
anuualy_donor = unsolicited[unsolicited.npsp__Primary_Contact__c.isin(list(anuualy_donor.Id))].npsp__Primary_Contact__c.nunique() #21

yr_donation =  unsolicited_donor.groupby(['npsp__Primary_Contact__c','year'])['AccountId'].count().reset_index(name = 'counts')  #number of donor from social media/fundraiser = absolute number
yr_donation.to_excel('donor give more than once a year.xlsx',index = False)  #some accountid donate more than once a month

yr=unsolicited_donor.groupby(['npsp__Primary_Contact__c','year']).\
            apply(lambda x:pd.Series({'yr_donate':x.shape[0]})).reset_index()
len(yr_donation[yr_donation.counts>1].npsp__Primary_Contact__c.unique()) #140

#for donors who give more than once a year AT LEAST ONE YEAR = 0.1306 - 140/1072

#3-3 What is the average gift of an unsolicited individual donor? 
unsolicited_individual = unsolicited_donor[unsolicited_donor.npsp__Primary_Contact__c.isin(list(contact[contact.Donor_Type__c == 'Individual Donor'].Id))] #no need to drop dup since there are situatoions where same accountid donates more than once a day
gift_amount = account[account.Id.isin(unsolicited_individual.AccountId)] 
total_gift_avg = gift_amount[['Id','npo02__AverageAmount__c']] #Id is unique in account table (no duplicates)
total_gift_avg.to_excel('avg gift amount for individual donors.xlsx',index = False)
total_gift_avg['npo02__AverageAmount__c'].mean() #331.33

total_gift_avg = unsolicited_individual.groupby('npsp__Primary_Contact__c').Amount.mean().reset_index(name='ave')
total_gift_avg.ave.mean()
total_gift = unsolicited_individual.groupby('npsp__Primary_Contact__c').Amount.sum().reset_index(name='total')
total_gift.mean()

