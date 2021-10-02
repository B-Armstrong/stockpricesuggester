# -*- coding: utf-8 -*-
"""
Created on Fri Jan 29 2021

@author: Ben Armstrong

site used to learn try and except for error handling:
https://www.techbeamers.com/use-try-except-python/

site used to learn about dataframe manipulation:
https://pandas.pydata.org/docs/reference/api/pandas.DataFrame

LEGEND: Meaning of Variables
r2bcopied = rows to be copied
r2scopying = row to start copying
stvolatil = short term volatility
totrows = total rows
colmatchcnt = column match count
pdaysclose = previous days close
sfile = stock file (holds the suggested prices in text file)
pctarray = percentage array
sd = stock data
hcpctsr = high-close percent short range
lcpctsr = low-close percent short range
hcavgsr = high-close average short range
lcavgsr = low-close average short range

"""
import numpy as np
#import matplotlib.pyplot as plt
from datetime import date,timedelta
from yahoo_fin.stock_info import get_data
from requests import ConnectionError
#variables:
today = date.today()
startdate = today - timedelta(50)
r2bcopied = 19
r2scopying = 0
stvolatil  = 13
totrows = 0
colmatchcnt = 0
pdaysclose = 0
#lists:
pctlose = [.99,.985,.98,.97,.94,.93]
pctgain = [1.01,1.015,1.02,1.03,1.06,1.07]
pctarray = [10,25,40,50,60,75]
# example: stocksymbols = ['SPLG','QQQ','DIA','IWM']
stocksymbols = ['splg','spmd','dgro','fidu']
#dictionaries:
stockdata = {}
sd = {}
hcpctsr = {} 
lcpctsr = {}
hcavgsr = {}
lcavgsr = {}
# function that checks status of file and closes it if open.
def checkfilestatus():
    if sfile.closed == False:
        sfile.close()
try:
# create/open a text file to hold price suggestions of stocks analyzed
    sfile=open("suggestedstockprices.txt",'w')    
# store historical stock data of the stocksymbols list into stockdata dictionary
    for symbols in stocksymbols:
        stockdata[symbols] = get_data(symbols,start_date= startdate, end_date =
                                      today)

# sanity check to make sure the data has the correct columns and enoough rows to
# analyze the data.    
    for col in stockdata[symbols].columns:
        if col == 'low' or col == 'high' or col == 'close':
            colmatchcnt = colmatchcnt + 1
    if colmatchcnt == 3 and stockdata[symbols].shape[0] >= r2bcopied:

# routine to retreive the last x days of stock prices based on. 
# constant 'r2bcopied' variable. Calculates difference of total rows
# in file - r2bcopied to determine which row to start copying from.   
        totrows = stockdata[symbols].shape[0]
        r2scopying = totrows - r2bcopied
  
    #seperate the data to be analyzed from initial dataset   
        for symbols in stocksymbols:
            sd[symbols]=stockdata[symbols][['high','low','close']][
                            r2scopying:(r2scopying + r2bcopied)]
        
        #add two new columns that indicate volatility percentage per index between
        # high to close and low to close. these values are used to find the 30 day
        # and 14 day volatility used to base recommended buy and sell points of
        # stock being analyzed
            sd[symbols].insert(3,'hiclpct',(1-(sd[symbols].close/sd[symbols].high)))
            sd[symbols].insert(4,'lclpct',(1-(sd[symbols].close/sd[symbols].low)))
            
        # establish quartile rankings of 14 day volatility for both high asmnd low
        # compared to close this information is used to recommend buy and sell 
        # points of stock being analyzed
            hcpctsr[symbols] = np.percentile(
                    sd[symbols]['hiclpct'][(sd[symbols].hiclpct.count()-stvolatil):
                    sd[symbols].hiclpct.count()],pctarray)
            lcpctsr[symbols] = np.percentile(
                    sd[symbols]['lclpct'][(sd[symbols].lclpct.count()-stvolatil):
                    sd[symbols].lclpct.count()],pctarray) 
            
        # this function allows me to show the average buy and sell points over
        # the time frame selected.  basically I am averageing the selected
        # data to determine what percentile the average falls in, this is also 
        # useful for price direction indication.
            hcavgsr[symbols] = np.average(
                    sd[symbols]['hiclpct'][(sd[symbols].hiclpct.count()-stvolatil):
                    sd[symbols].hiclpct.count()],)
            lcavgsr[symbols] = np.average(
                    sd[symbols]['lclpct'][(sd[symbols].lclpct.count()-stvolatil):
                    sd[symbols].lclpct.count()],)
            
        # add the average highclose daily volatility over the period and add it to
        # the end of the high quartile rankings
            hcpctsr[symbols] = np.append(hcpctsr[symbols],hcavgsr[symbols])
        
        # add the average lowclose daily volatility over the period and add it to
        # the end of the low quartile rankings
            lcpctsr[symbols] = np.append(lcpctsr[symbols],lcavgsr[symbols])
            
        # calculate buy-sell prices based on expected volatility along the high-
        # low range around the previous days close and store in a list.
            pdaysclose = round(float(sd[symbols]['close'][-1:]),2)
            ticker = symbols
            sellprices = []
            for i in range(0,7):
                sprice = round(pdaysclose + (pdaysclose*hcpctsr[symbols][i]),2)
                sellprices.append(sprice)
            buyprices = []
            for i in range(0,7):
                bprice = round(pdaysclose + (pdaysclose*lcpctsr[symbols][i]),2)
                buyprices.append(bprice)
            incpctprice = []
            for i in range(0,6):
                incprice = round(pdaysclose * pctgain[i],2)
                incpctprice.append(incprice)
            decpctprice = []
            for i in range(0,6):
                decprice = round(pdaysclose * pctlose[i],2)
                decpctprice.append(decprice)    
            smatwenty = round(sd[symbols].close.mean(),2)
            xtremeday = sellprices[5] - buyprices[0]
            xtremesplitppct = round(1-(pdaysclose/sellprices[5]),3)
            xtremesplitnpct = round(1-(buyprices[0]/pdaysclose),3)
            avgpospct = round(1-(pdaysclose/sellprices[6]),3)
            avgnegpct = round(1-(buyprices[6]/pdaysclose),3)
            xtremepos = pdaysclose+xtremeday
            xtremeneg = pdaysclose-xtremeday
            xtremepospct = round(1-(pdaysclose/xtremepos),3)
            xtremenegpct = round(1-(xtremeneg/pdaysclose),3)
            #print the suggested buy and sell points of the analyzed stock
            print("Ticker:" + ticker + "\tSMA20: " + str(smatwenty) + 
                  "\tYesterday's Close: " + str(pdaysclose))
            print("\tSugggested prices")
            print("Percentile Rank:\tbuy:\tsell:\trange (%)")
            print("\t75%:\t\t{0:.2f}\t{1:.2f}".format(buyprices[5],sellprices[0]))
            print("\t60%:\t\t{0:.2f}\t{1:.2f}".format(buyprices[4],sellprices[1]))
            print("\t50%:\t\t{0:.2f}\t{1:.2f}".format(buyprices[3],sellprices[2]))
            print("\t40%:\t\t{0:.2f}\t{1:.2f}".format(buyprices[2],sellprices[3]))
            print("\t25%:\t\t{0:.2f}\t{1:.2f}".format(buyprices[1],sellprices[4]))
            print("\t10%:\t\t{0:.2f}\t{1:.2f}\t-{2:.1%} +{3:.1%}".
                  format(buyprices[0],sellprices[5],xtremesplitnpct,xtremesplitppct))
            print("\tAVG%:\t\t{0:.2f}\t{1:.2f}\t-{2:.1%} +{3:.1%}".
                  format(buyprices[6],sellprices[6],avgnegpct,avgpospct))
            print("percentage dec/inc:\tprice:")
            print("\t-/+1.0%:\t{0:.2f}\t{1:.2f}".format(decpctprice[0],incpctprice[0]))
            print("\t-/+1.5%:\t{0:.2f}\t{1:.2f}".format(decpctprice[1],incpctprice[1]))
            print("\t-/+2.0%:\t{0:.2f}\t{1:.2f}".format(decpctprice[2],incpctprice[2]))
            print("\t-/+3.0%:\t{0:.2f}\t{1:.2f}".format(decpctprice[3],incpctprice[3]))
            print("\t-/+6.0%:\t{0:.2f}\t{1:.2f}".format(decpctprice[4],incpctprice[4]))
            print("\t-/+7.0%:\t{0:.2f}\t{1:.2f}".format(decpctprice[5],incpctprice[5]))
            print("\t-{0:.1%} +{1:.1%}\t{2:.2f}\t{3:.2f}".
                  format(xtremenegpct,xtremepospct,xtremeneg,xtremepos))
            #save the suggested buy and sell points of the analyzed stock to
            #suggestedstockprices.txt in same folder as program
            sfile.write("Ticker:" + ticker + "\tSMA20: " + str(smatwenty) + 
                  "\tYesterday's Close: " + str(pdaysclose) + '\n')
            sfile.write("\tSugggested prices\n")
            sfile.write("Percentile Rank:\tbuy:\tsell:\n")
            sfile.write("\t75%:\t\t{0:.2f}\t{1:.2f}\n".
                        format(buyprices[5],sellprices[0]))
            sfile.write("\t60%:\t\t{0:.2f}\t{1:.2f}\n".
                        format(buyprices[4],sellprices[1]))
            sfile.write("\t50%:\t\t{0:.2f}\t{1:.2f}\n".
                        format(buyprices[3],sellprices[2]))
            sfile.write("\t40%:\t\t{0:.2f}\t{1:.2f}\n".
                        format(buyprices[2],sellprices[3]))
            sfile.write("\t25%:\t\t{0:.2f}\t{1:.2f}\n".
                        format(buyprices[1],sellprices[4]))
            sfile.write("\t10%:\t\t{0:.2f}\t{1:.2f}\n".
                        format(buyprices[0],sellprices[5]))
            sfile.write("\tAVG%:\t\t{0:.2f}\t{1:.2f}\n".
                        format(buyprices[6],sellprices[6]))
            sfile.write("percentage lost:\tprice:\n")
            sfile.write("\t-/+1.0%:\t{0:.2f}\t{1:.2f}\n".
                        format(decpctprice[0],incpctprice[0]))
            sfile.write("\t-/+1.5%:\t{0:.2f}\t{1:.2f}\n".
                        format(decpctprice[1],incpctprice[1]))
            sfile.write("\t-/+2.0%:\t{0:.2f}\t{1:.2f}\n".
                        format(decpctprice[2],incpctprice[2]))
            sfile.write("\t-/+3.0%:\t{0:.2f}\t{1:.2f}\n".
                        format(decpctprice[3],incpctprice[3]))
            sfile.write("\t-/+6.0%:\t{0:.2f}\t{1:.2f}\n".
                        format(decpctprice[4],incpctprice[4]))
            sfile.write("\t-/+7.0%:\t{0:.2f}\t{1:.2f}\n\n".
                        format(decpctprice[5],incpctprice[5]))
        checkfilestatus()
    else:
        print('Data does not have correct format. Please check internet' + 
              ' connection before trying again')
        checkfilestatus()
except ConnectionError:   
    print('Please check internet connection and try again')
    checkfilestatus()
except Exception as e:
    print(e)
    checkfilestatus()