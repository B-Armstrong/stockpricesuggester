# -*- coding: utf-8 -*-
"""
Created on Fri Jan 29 2021
Updated on Th Oct 7 2021

@author: Ben Armstrong

site used to learn try and except for error handling:
https://www.techbeamers.com/use-try-except-python/

site used to learn about dataframe manipulation:
https://pandas.pydata.org/docs/reference/api/pandas.DataFrame

LEGEND: Meaning of Variables
pctarray = percentage array
sd = stock data 2B Analyzed

"""
import numpy as np
from datetime import date,timedelta
from yahoo_fin.stock_info import get_data
from requests import ConnectionError
#variables:
today = date.today()
startdate = today - timedelta(50)
rows2bcopied = 19
rows2startcopying = 0
shorttermvolatility  = 13
totalrows = 0
columnmatchcount = 0
previousdaysclose = 0
#lists:
pctlose = [.99,.985,.98,.97,.94,.93]
pctgain = [1.01,1.015,1.02,1.03,1.06,1.07]
pctarray = [10,25,40,50,60,75]
# example: stocksymbols = ['SPLG','QQQ','DIA','IWM']
stocksymbols = ['DIA']
#dictionaries:
stockdata = {}
stock2banalyzed = {}
high_closepctshortrange = {} 
low_closepctshortrange = {}
high_closeavgshortrange = {}
low_closeavgshortrange = {}
# function that checks status of file and closes it if open.
def checkfilestatus():
    if stockfile.closed == False:
        stockfile.close()
try:
# create/open a text file to hold price suggestions of stocks analyzed
    stockfile=open("suggestedstockprices.txt",'w')    
# store historical stock data of the stocksymbols list into stockdata dictionary
    for symbols in stocksymbols:
        stockdata[symbols] = get_data(symbols,start_date= startdate, end_date =
                                      today)

# sanity check to make sure the data has the correct columns and enoough rows to
# analyze the data.    
    for col in stockdata[symbols].columns:
        if col == 'low' or col == 'high' or col == 'close':
            columnmatchcount = columnmatchcount + 1
    if columnmatchcount == 3 and stockdata[symbols].shape[0] >= rows2bcopied:

# routine to retreive the last x days of stock prices based on. 
# constant 'rows2bcopied' variable. Calculates difference of total rows
# in file - rows2bcopied to determine which row to start copying from.   
        totalrows = stockdata[symbols].shape[0]
        rows2startcopying = totalrows - rows2bcopied
  
    #seperate the data to be analyzed from initial dataset   
        for symbols in stocksymbols:
            stock2banalyzed[symbols]=stockdata[symbols][['high','low','close']][
                            rows2startcopying:(rows2startcopying + rows2bcopied)]
        
        #add two new columns that indicate volatility percentage per index between
        # high to close and low to close. these values are used to find the 30 day
        # and 14 day volatility used to base recommended buy and sell points of
        # stock being analyzed
            stock2banalyzed[symbols].insert(3,'hiclpct',(1-(stock2banalyzed[symbols].close/stock2banalyzed[symbols].high)))
            stock2banalyzed[symbols].insert(4,'lclpct',(1-(stock2banalyzed[symbols].close/stock2banalyzed[symbols].low)))
            
        # establish quartile rankings of 14 day volatility for both high asmnd low
        # compared to close this information is used to recommend buy and sell 
        # points of stock being analyzed
            high_closepctshortrange[symbols] = np.percentile(
                    stock2banalyzed[symbols]['hiclpct'][(stock2banalyzed[symbols].hiclpct.count()-shorttermvolatility):
                    stock2banalyzed[symbols].hiclpct.count()],pctarray)
            low_closepctshortrange[symbols] = np.percentile(
                    stock2banalyzed[symbols]['lclpct'][(stock2banalyzed[symbols].lclpct.count()-shorttermvolatility):
                    stock2banalyzed[symbols].lclpct.count()],pctarray) 
            
        # this function allows me to show the average buy and sell points over
        # the time frame selected.  basically I am averageing the selected
        # data to determine what percentile the average falls in, this is also 
        # useful for price direction indication.
            high_closeavgshortrange[symbols] = np.average(
                    stock2banalyzed[symbols]['hiclpct'][(stock2banalyzed[symbols].hiclpct.count()-shorttermvolatility):
                    stock2banalyzed[symbols].hiclpct.count()],)
            low_closeavgshortrange[symbols] = np.average(
                    stock2banalyzed[symbols]['lclpct'][(stock2banalyzed[symbols].lclpct.count()-shorttermvolatility):
                    stock2banalyzed[symbols].lclpct.count()],)
            
        # add the average highclose daily volatility over the period and add it to
        # the end of the high quartile rankings
            high_closepctshortrange[symbols] = np.append(high_closepctshortrange[symbols],high_closeavgshortrange[symbols])
        
        # add the average lowclose daily volatility over the period and add it to
        # the end of the low quartile rankings
            low_closepctshortrange[symbols] = np.append(low_closepctshortrange[symbols],low_closeavgshortrange[symbols])
            
        # calculate buy-sell prices based on expected volatility along the high-
        # low range around the previous days close and store in a list.
            previousdaysclose = round(float(stock2banalyzed[symbols]['close'][-1:]),2)
            ticker = symbols
            sellprices = []
            for i in range(0,7):
                sprice = round(previousdaysclose + (previousdaysclose*high_closepctshortrange[symbols][i]),2)
                sellprices.append(sprice)
            buyprices = []
            for i in range(0,7):
                bprice = round(previousdaysclose + (previousdaysclose*low_closepctshortrange[symbols][i]),2)
                buyprices.append(bprice)
            incpctprice = []
            for i in range(0,6):
                incprice = round(previousdaysclose * pctgain[i],2)
                incpctprice.append(incprice)
            decpctprice = []
            for i in range(0,6):
                decprice = round(previousdaysclose * pctlose[i],2)
                decpctprice.append(decprice)    
            smatwenty = round(stock2banalyzed[symbols].close.mean(),2)
            xtremeday = sellprices[5] - buyprices[0]
            xtremesplitppct = round(1-(previousdaysclose/sellprices[5]),3)
            xtremesplitnpct = round(1-(buyprices[0]/previousdaysclose),3)
            avgpospct = round(1-(previousdaysclose/sellprices[6]),3)
            avgnegpct = round(1-(buyprices[6]/previousdaysclose),3)
            xtremepos = previousdaysclose+xtremeday
            xtremeneg = previousdaysclose-xtremeday
            xtremepospct = round(1-(previousdaysclose/xtremepos),3)
            xtremenegpct = round(1-(xtremeneg/previousdaysclose),3)
            #print the suggested buy and sell points of the analyzed stock
            print("Ticker:" + ticker + "\tSMA20: " + str(smatwenty) + 
                  "\tYesterday's Close: " + str(previousdaysclose))
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
            stockfile.write("Ticker:" + ticker + "\tSMA20: " + str(smatwenty) + 
                  "\tYesterday's Close: " + str(previousdaysclose) + '\n')
            stockfile.write("\tSugggested prices\n")
            stockfile.write("Percentile Rank:\tbuy:\tsell:\n")
            stockfile.write("\t75%:\t\t{0:.2f}\t{1:.2f}\n".
                        format(buyprices[5],sellprices[0]))
            stockfile.write("\t60%:\t\t{0:.2f}\t{1:.2f}\n".
                        format(buyprices[4],sellprices[1]))
            stockfile.write("\t50%:\t\t{0:.2f}\t{1:.2f}\n".
                        format(buyprices[3],sellprices[2]))
            stockfile.write("\t40%:\t\t{0:.2f}\t{1:.2f}\n".
                        format(buyprices[2],sellprices[3]))
            stockfile.write("\t25%:\t\t{0:.2f}\t{1:.2f}\n".
                        format(buyprices[1],sellprices[4]))
            stockfile.write("\t10%:\t\t{0:.2f}\t{1:.2f}\n".
                        format(buyprices[0],sellprices[5]))
            stockfile.write("\tAVG%:\t\t{0:.2f}\t{1:.2f}\n".
                        format(buyprices[6],sellprices[6]))
            stockfile.write("percentage lost:\tprice:\n")
            stockfile.write("\t-/+1.0%:\t{0:.2f}\t{1:.2f}\n".
                        format(decpctprice[0],incpctprice[0]))
            stockfile.write("\t-/+1.5%:\t{0:.2f}\t{1:.2f}\n".
                        format(decpctprice[1],incpctprice[1]))
            stockfile.write("\t-/+2.0%:\t{0:.2f}\t{1:.2f}\n".
                        format(decpctprice[2],incpctprice[2]))
            stockfile.write("\t-/+3.0%:\t{0:.2f}\t{1:.2f}\n".
                        format(decpctprice[3],incpctprice[3]))
            stockfile.write("\t-/+6.0%:\t{0:.2f}\t{1:.2f}\n".
                        format(decpctprice[4],incpctprice[4]))
            stockfile.write("\t-/+7.0%:\t{0:.2f}\t{1:.2f}\n\n".
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