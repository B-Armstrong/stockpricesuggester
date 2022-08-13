# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
"""
Accepts string, prints and saves suggested buy/sell prices. Returns None.
Created on Tu Aug 2 2022
@author: Ben Armstrong
"""

from datetime import date,timedelta
from csv import reader

from yahoo_fin.stock_info import get_data
from requests import ConnectionError
import numpy as np

class StockPriceSuggester:
  """
  This class accepts strings of stock ticker names seperated by a comma:
  'meta,aapl'
  This class prints and saves suggested buy and sell prices.
  """
  def __init__(self,stock_ticker_csv):
    self.list = stock_ticker_csv
    self.today = date.today()
    self.start_date = self.today - timedelta(50)
    self.unresolved_tickers = []
    self.entity_tickers = []
    self.entity_names = []
    self.__initialize_entity_data()
    self.app_stock_list =  self.__stock_list_to_evaluate(self.list)
    self.__get_stock_data(self.app_stock_list,self.today,self.start_date)

  def __initialize_entity_data(self):
        """
        startup function that takes an input of a csv file containing
        compnay name, type of investment and ticker symbol of company
        the function creates and sets two lists:
        entity_ticker_symbols
        entity_name
        into memory for us while application is running
        ------------------------------------------------------------------------
        input
        -----
        None

        Returns
        -------
        None
        """
        try:
          entity_ticker_symbol, entity_name = [], []
          with open('company ticker symbols.csv',newline='') as csvfile:
            entity_reader = reader(csvfile,delimiter=',')
            for row in entity_reader:
                entity_ticker_symbol.append(row[0])
                entity_name.append(row[1])
          self.__set_entity_tickers(entity_ticker_symbol)
          self.__set_entity_names(entity_name)
        except FileNotFoundError:
          print('file to initialize default entity information not found. '
                'Please contact the administrator')

  def __stock_list_to_evaluate(self, user_list):
    """
    This function accepts a csv of stock ticker symbols. this is used to
    retreive historical stock data that application analyzes to suggest
    the days best buy and sell points
    """
    #Create two global lists one to hold user requested stoocks and the
    #the second holds requested stocks the application fails to recognize.
    user_ticker_list = []
    #capitalize list for uniform formatting while analyzing
    user_list_cap = str.upper(user_list)
    #user_input is split into list of strings
    split_user_input = user_list_cap.split(',')
    #loop through user_input and evaluate for valid ticker symbol
    for i in range(0,len(split_user_input)):
      entity_symbol = split_user_input[i].strip()
      #check user_input match against default list of enitity_tickers
      #if found valid ticker gets placed in global list of stock symbols
      if entity_symbol in self.entity_tickers:
        user_ticker_list.append(entity_symbol)
      #below code allows for a correctly formatted stock ticker to be allowed.
      #this is a weak check and will allow for AssertionError
      #when attempting to retrieve stock historical prices
      #eventually check to be removed when above entity_tickers list is verified
      #to contain all US listed stocks
      elif entity_symbol.isalpha() == True and len(entity_symbol) <= 5:
        user_ticker_list.append(entity_symbol)
      #Capture any symbol that has correct characters format, but too many
      #and store them in global list.  This list will be used to inform user
      #later in the application.
      elif entity_symbol.isalpha():
        self.__set_unresolved_tickers(entity_symbol)
      #print out inform useer ticker name that is not correctly formatted.
      #The ticker is discarded by the application.
      else:
        print('stock ticker is not alphabetic! no data will be retreived for '
              + entity_symbol + '.')
    return user_ticker_list

  def __get_stock_data(self, app_stock_list, today, start_date):
    """
    """
    if app_stock_list:
      try:

        # store user stock reuested historical data retrived from server into
        #stock_data dictionary
        stock_data = {}
        for symbols in app_stock_list:
          stock_data[symbols] = get_data(symbols,
                                           start_date=start_date,
                                           end_date=today)

          #create variables used to determine how much data to snip from
          #the data retreived from the server
          rows_2b_copied = 20
          market_days  = 14
          # sanity check to make sure the data has the correct columns and
          #enoough rows to analyze the data.
          if self.__check_data_structure(stock_data[symbols],rows_2b_copied):
              #data received is good create variable to hold length of data
              totalrows = stock_data[symbols].shape[0]
              #send data for snipping and prepare for analysis
              analyze_stock = self.__data_2_analyze(stock_data,
                                             symbols,
                                             totalrows,
                                             rows_2b_copied)
              #determine quartile rankings based on daily high and close price
              stock_sell_rank = self.__price_quartiles(analyze_stock,
                                          symbols,
                                          sell_quartiles = True,
                                          days_2_rank = market_days)
              #determine quartile rankings based on daily low and close price
              stock_buy_rank = self.__price_quartiles(analyze_stock,
                                          symbols,
                                          sell_quartiles = False,
                                          days_2_rank = market_days)
              #determine average prices based on daily high and close price
              stock_sell_avg = self.__price_averages(analyze_stock,
                                          symbols,
                                          sell_averages = True,
                                          days_2_avg = market_days)
              #determine average prices based on daily low and close price
              stock_buy_avg = self.__price_averages(analyze_stock,
                                         symbols,
                                         sell_averages = False,
                                         days_2_avg = market_days)

          # add the average high close daily volatility over the period and
          # add it tp the end of the high quartile rankings
              stock_sell_rank[symbols] = np.append(stock_sell_rank[symbols],
                                                  stock_sell_avg[symbols])

          # add the average low close daily volatility over the period and
          # add it to the end of the low quartile rankings
              stock_buy_rank[symbols] = np.append(stock_buy_rank[symbols],
                                                 stock_buy_avg[symbols])

          # calculate buy-sell prices based on expected volatility along the
          # high-low range around the previous days close and store in lists.
              previous_close = round(self.__get_previous_close(analyze_stock,
                                                        symbols),2)
              sell_prices = self.__get_prices(stock_sell_rank,
                                       symbols,
                                       previous_close,
                                       'sell')
              buy_prices = self.__get_prices(stock_buy_rank,
                                      symbols,
                                      previous_close,
                                      'buy')
              #calculate prices based on expected volatility along the high-
              # low range around the previous days close and store in lists.
              pct_lose = [.99,.985,.98,.97,.94]
              pct_gain = [1.01,1.015,1.02,1.03,1.06]
              pct_gain_sell_price = self.__get_prices(pct_gain,
                                                   symbols,
                                                   previous_close,
                                                   'inc')
              pct_lose_buy_price = self.__get_prices(pct_lose,
                                              symbols,
                                              previous_close,
                                              'dec')

              #routine that prints suggested buy and sell points based on
              # quartile ranking and percentage changes of price
              self.__print_prices(analyze_stock,
                           symbols,
                           sell_prices,
                           buy_prices,
                           pct_lose_buy_price,
                           pct_gain_sell_price,
                           previous_close)
              self.__save_prices_file(analyze_stock,
                                     symbols,
                                     sell_prices,
                                     buy_prices,
                                     pct_lose_buy_price,
                                     pct_gain_sell_price,
                                     previous_close)

          #if columnmatch fails alert user and close app
          else:
              print('Data does not have correct format. Please check internet' +
                    ' connection before trying again')

        #look in the unresolved list which will inform user if any found
        self.__check_unresolved()

      #these exception relate to the request to the server for the data
      #most common issue would be user not connected to internet
      except ConnectionError:
        print('Please check internet connection and try again')
      #This error is received by the server if the ticker cant be found
      except AssertionError:
        #look in the unresolved list which will inform user if any found
        self.__check_unresolved()
        print(f"\nNo data retreived from ticker {symbols}. please check ticker"
              " symbol and try again. ")

    #User failed to input a properly formatted ticker symbol
    else:
        print("no valid stock ticker input.  please try again")

  def __data_2_analyze(self, original_data,s_ticker,endrow,numrowscopy):
      """
      seperates the stock data to be analzyed from original data retrieved.
      ------------------------------------------------------------------------
      input
      -------
      original_data type dictionary
      s_ticker type string: stock to analyze
      endrow type int: total rows in data
      numrowscopy type int: how many rows to be analyzed
      Returns
      -------
      dictionary: new dictionary with only columns necessary to analyze data

      """
      stock2analyze = {}
      od = original_data
      t = s_ticker
      startrow = endrow - numrowscopy

      #snip only requested data from original data received
      stock2analyze[t]=od[t][['high','low','close']][startrow:endrow]
      #add two new columns that indicate volatility percentage per index between
      #high to close and low to close.
      stock2analyze[t].insert(3,'hiclpct',(1-(stock2analyze[t]
                                      .close/stock2analyze[t].high)))
      stock2analyze[t].insert(4,'lclpct',(1-(stock2analyze[t]
                                      .close/stock2analyze[t].low)))
      return stock2analyze

  def __price_quartiles(self, original_data,s_ticker,sell_quartiles,days_2_rank):
      """
      establish quartile rankings of 14 day volatility for high or low price
      compared to closing price.  This information is used to recommend buy and
      sell points of stock being analyzed.
      high2close = sell prices ; close2high = buy prices
      ------------------------------------------------------------------------
      input
      -------
      original_data type dictionary:
      s_ticker type string: stock data to breakdown into quartiles
      sell_quartiles type boolean: flag: True = sell prices
      days_2_rank type integer:
      Returns
      -------
      dictionary: new dictionary that holds the short term quartile rankings

      """
      pct_array = [10,25,40,50,60,75]
      quartiles = {}
      od = original_data
      t = s_ticker
      if sell_quartiles:
        quartiles[t] = np.percentile(
              od[t]['hiclpct'][(od[t].hiclpct.count()-days_2_rank):
              od[t].hiclpct.count()],pct_array)
      else:
        quartiles[t] = np.percentile(
              od[t]['lclpct'][(od[t].lclpct.count()-days_2_rank):
              od[t].lclpct.count()],pct_array)
      return quartiles

  def __price_averages(self, original_data,s_ticker,sell_averages,days_2_avg):
      """
      this function shows the average buy and sell points over
      the time frame(days_2_avg).  averages the original_data
      to determine what percentile the average falls in.
      The output can be compared to median price to indicate
      price direction over the time frame.
      ------------------------------------------------------------------------
      input
      -------
      original_data type dictionary:
      s_ticker type string: stock data to average
      sell_averages type boolean: determines if original_data based on
      daily high to Close margin, if false assumes data based on daily
      low to close margin.
      Returns
      -------
      dictionary: new dictionary that contains average short term price
      """

      st_avg = {}
      od = original_data
      t = s_ticker
      if sell_averages:
        st_avg[t] = np.average(
              od[t]['hiclpct'][(od[t].hiclpct.count()-days_2_avg):
              od[t].hiclpct.count()],)
      else:
        st_avg[t] = np.average(
              od[t]['lclpct'][(od[t].lclpct.count()-days_2_avg):
              od[t].lclpct.count()],)
      return st_avg

  def __check_data_structure(self,receiveddata,rows2copy):
      """
      checks to make sure the data has the correct columns and enoough rows to
      analyze the data.
      ------------------------------------------------------------------------
      input
      -------
      receiveddata type dictionary
      rows2copy type int
      Returns
      -------
      Boolean.

      """
      columnmatchcount = 0
      for col in receiveddata.columns:
        if col == 'low' or col == 'high' or col == 'close':
              columnmatchcount +=  1
      if columnmatchcount == 3 and receiveddata.shape[0] >= rows2copy:
          return True
      else:
        return False

  def __check_unresolved(self):
    """
    This Function checks if there are unresolved ticker symbols
    and if found prints out each unresolved ticker symbol that
    was passed in by the user
    ------------------------------------------------------------------------
    input
    -----
    None

    Returns
    -------
    None
    """

    if self.unresolved_tickers:
      print('\nThe following tickers could not be resolved:')
      for ticker in self.unresolved_tickers:
        print(f"{ticker}")
      print('This message appears when the ticker symbol length is greater '
              'than 5.\nIf this is a valid ticker symbol please contact '
              'the administrator.')

  def __print_prices(self, analyze_stock,
                               symbols,
                               s_prices,
                               b_prices,
                               p_lose_prices,
                               p_gain_prices,
                               p_close):
      """
      Takes in ticker symbol of the stock and utilizing snipped historical
      data prints to screen and writes to a file suggested buy and sell prices
      for stock the day the analysis is run.
      ------------------------------------------------------------------------
      input
      -----
      s_ticker str:

      Returns
      -------
      None
      """

      sma_twenty = round(self.__get_sma(analyze_stock,symbols),2)

      # utilize buy, sell prices and previous days close to determine extreme
      # and average trading days

      xtreme_split_pos_pct = round(1-(p_close/s_prices[5]),3)
      xtreme_split_neg_pct = round(1-(b_prices[0]/p_close),3)
      avg_pos_pct = round(1-(p_close/s_prices[6]),3)
      avg_neg_pct = round(1-(b_prices[6]/p_close),3)
      xtreme_day = round(s_prices[5] - b_prices[0],2)
      xtreme_pos = round(p_close+xtreme_day,2)
      xtreme_neg = round(p_close-xtreme_day,2)
      xtreme_pos_pct = round(1-(p_close/xtreme_pos),3)
      xtreme_neg_pct = round(1-(xtreme_neg/p_close),3)

      #print the suggested buy and sell points of the analyzed stock
      print("Ticker:" + symbols + "\tSMA20: " + str(sma_twenty) +
            "\tYesterday's Close: " + str(p_close))
      print("\tSugggested prices")
      print("Percentile Rank:\tbuy:\tsell:\trange (%)")
      print("\t75%:\t\t\t{0:.2f}\t{1:.2f}".format(b_prices[5],
                                                s_prices[0]))
      print("\t60%:\t\t\t{0:.2f}\t{1:.2f}".format(b_prices[4],
                                                s_prices[1]))
      print("\t50%:\t\t\t{0:.2f}\t{1:.2f}".format(b_prices[3],
                                                s_prices[2]))
      print("\t40%:\t\t\t{0:.2f}\t{1:.2f}".format(b_prices[2],
                                                s_prices[3]))
      print("\t25%:\t\t\t{0:.2f}\t{1:.2f}".format(b_prices[1],
                                                s_prices[4]))
      print("\t10%:\t\t\t{0:.2f}\t{1:.2f}\t-{2:.1%} +{3:.1%}".
            format(b_prices[0],s_prices[5],xtreme_split_neg_pct,
                   xtreme_split_pos_pct))
      print("\tAVG%:\t\t\t{0:.2f}\t{1:.2f}\t-{2:.1%} +{3:.1%}".
            format(b_prices[6],s_prices[6],avg_neg_pct,avg_pos_pct))
      print("percentage dec/inc:\t\tprice:")
      print("\t-/+1.0%:\t\t{0:.2f}\t{1:.2f}".format(p_lose_prices[0],
                                                  p_gain_prices[0]))
      print("\t-/+1.5%:\t\t{0:.2f}\t{1:.2f}".format(p_lose_prices[1],
                                                  p_gain_prices[1]))
      print("\t-/+2.0%:\t\t{0:.2f}\t{1:.2f}".format(p_lose_prices[2],
                                                  p_gain_prices[2]))
      print("\t-/+3.0%:\t\t{0:.2f}\t{1:.2f}".format(p_lose_prices[3],
                                                  p_gain_prices[3]))
      print("\t-/+6.0%:\t\t{0:.2f}\t{1:.2f}".format(p_lose_prices[4],
                                                  p_gain_prices[4]))
      print("\t-{0:.1%} +{1:.1%}\t{2:.2f}\t{3:.2f}".
            format(xtreme_neg_pct,xtreme_pos_pct,xtreme_neg,xtreme_pos))
      print(self.__get_stock_trend(b_prices[6],b_prices[3]))

  def __save_prices_file(self, analyze_stock,
                             symbols,
                             s_prices,
                             b_prices,
                             p_lose_prices,
                             p_gain_prices,
                             p_close):
    """
    save the suggested buy and sell points of the analyzed stock to
    suggestedstockprices.txt in same folder as program
    create/open a text file to hold price suggestions of stocks analyzed
    """
    try:
      stockfile=open('suggestedstockprices.txt','a')
    except FileNotFoundError:
      stockfile=open('suggestedstockprices.txt','w')
    else:
      sma_twenty = round(self.__get_sma(analyze_stock,symbols),2)
      stockfile.write("Ticker:" + symbols + "\tSMA20: " + str(sma_twenty) +
            "\tYesterday's Close: " + str(p_close) + '\n')
      stockfile.write("\tSugggested prices\n")
      stockfile.write("Percentile Rank:\tbuy:\tsell:\n")
      stockfile.write("\t75%:\t\t{0:.2f}\t{1:.2f}\n".
                  format(b_prices[5],s_prices[0]))
      stockfile.write("\t60%:\t\t{0:.2f}\t{1:.2f}\n".
                  format(b_prices[4],s_prices[1]))
      stockfile.write("\t50%:\t\t{0:.2f}\t{1:.2f}\n".
                  format(b_prices[3],s_prices[2]))
      stockfile.write("\t40%:\t\t{0:.2f}\t{1:.2f}\n".
                  format(b_prices[2],s_prices[3]))
      stockfile.write("\t25%:\t\t{0:.2f}\t{1:.2f}\n".
                  format(b_prices[1],s_prices[4]))
      stockfile.write("\t10%:\t\t{0:.2f}\t{1:.2f}\n".
                  format(b_prices[0],s_prices[5]))
      stockfile.write("\tAVG%:\t\t{0:.2f}\t{1:.2f}\n".
                  format(b_prices[6],s_prices[6]))
      stockfile.write("percentage lost:\tprice:\n")
      stockfile.write("\t-/+1.0%:\t{0:.2f}\t{1:.2f}\n".
                  format(p_lose_prices[0],p_gain_prices[0]))
      stockfile.write("\t-/+1.5%:\t{0:.2f}\t{1:.2f}\n".
                  format(p_lose_prices[1],p_gain_prices[1]))
      stockfile.write("\t-/+2.0%:\t{0:.2f}\t{1:.2f}\n".
                  format(p_lose_prices[2],p_gain_prices[2]))
      stockfile.write("\t-/+3.0%:\t{0:.2f}\t{1:.2f}\n".
                  format(p_lose_prices[3],p_gain_prices[3]))
      stockfile.write("\t-/+6.0%:\t{0:.2f}\t{1:.2f}\n".
                  format(p_lose_prices[4],p_gain_prices[4]))
      self.__check_file_status(stockfile)

  def __get_previous_close(self, original_data,s_ticker):
      """
      returns the stocks previous closing price
      ------------------------------------------------------------------------
      input
      -------
      original_data type dictionary:
      s_ticker type string:
      Returns
      -------
      float

      """
      return float(original_data[s_ticker]['close'][-1:])

  def __get_prices(self,
                 original_data,
                 s_ticker=None,
                 previous_close=0,
                 price_type=''):
      """
      returns prices based on type being requested (buy, sell, inc, dec)
      ------------------------------------------------------------------------
      input
      -------
      original_data type dictionary for buy or sell; list for inc or dec:
      s_ticker type string:
      previous_close type float:
      pricetype type string: Allowed strings (buy,sell,inc,dec)
      Returns
      -------
      list

      """
      prices = []
      price_types = ['buy','sell','inc','dec']
      if price_type not in price_types:
        raise ValueError
      else:
        if price_type ==  'buy' or price_type == 'sell':
          for i in range(0,7):
              temp_price = round(previous_close +
                                 (previous_close*original_data[s_ticker][i]),2)
              prices.append(temp_price)
        else:
          for i in range(0,5):
              temp_price = round(previous_close * original_data[i],2)
              prices.append(temp_price)
        return prices

  def __get_sma(self, original_data,s_ticker,):
      """
      returns simple moving average, days based on rows_2b_copied value
      ------------------------------------------------------------------------
      input
      -------
      original_data type dictionary:
      s_ticker type string:

      Returns
      -------
      float

      """
      return original_data[s_ticker].close.mean()

  def __get_stock_trend(self, avg_price,median_price):

      """

      returns short term stock price direction
      ------------------------------------------------------------------------
      input
      -------
      avg_price type float:
      median_price type float:

      Returns
      -------
      string

      """
      if avg_price > median_price and avg_price-median_price > .02:
          result = "UPWARD"
      elif avg_price < median_price and median_price-avg_price > .02:
          result = "DOWNWARD"
      else:
          result = "SIDEWAYS"
      return f'STOCK IS IN A {result} TREND'

  def __set_entity_tickers(self, entity_tickers_symbols):
    """
    sets/initializes company ticker symbol list
    ------------------------------------------------------------------------
    input
    -------
    entity_ticker list:

    Returns
    -------
    None

    """
    self.entity_tickers = entity_tickers_symbols.copy()

  def __set_entity_names(self, list_entity_names):
    """
    sets/initializes company names list
    ------------------------------------------------------------------------
    input
    -------
    entity_names list:

    Returns
    -------
    None

    """
    self.entity_names = list_entity_names.copy()

  def __set_unresolved_tickers(self, unresolved_ticker):

    self.unresolved_tickers.append(unresolved_ticker)

  def __check_file_status(self, file):
      """
      Checks if file is closed if not close the file
      -------
      input:
      file type object

      Returns
      -------
      None.

      """
      if file.closed == False:
          file.close()



