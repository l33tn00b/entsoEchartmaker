# for date arithmetics
import datetime

#from entsoe import EntsoeRawClient
import entsoe

# hash calculation
# for image update check
import hashlib

#Locale settings
import locale

# plotting
import matplotlib.pyplot as plt
import matplotlib.dates as md
import numpy as np
import pandas as pd
# render / modify images
from PIL import Image, ImageDraw

# trying to get time right
from pytz import timezone 

# copy over result
import subprocess

#exit
import sys

# config file
import yaml


def create_error_image(outfile_name, errmsg: str):
    """
    Create an image for display on a Lilygo T5 4.7" ePaper.
    The image contains a short text (parameter errmsg) giving the
    reason for the error.
    Returns a b/w PIL image which has to be saved and/or encoded for
    display using bincode_image() (and hashed for update check).
    By-product is a png file written so as to have a
    human-readable description. Result will also be copied (if desired) to
    www server directory.
    """
    # create new white background image
    img = Image.new('1', (960, 540), color = 'white')
    # print current (local) time on it
    now = datetime.datetime.now()    
    ImageDraw.Draw(img).text((2, 80),now.strftime('%Y-%m-%d %H:%M:%S'),(0))
    # print error message on it
    ImageDraw.Draw(img).text((2, 90),errmsg,(0))
    # write it in png format so we may easily read it
    # from a normal web browser
    #outfile_name = config_file.get("outfile_name")
    img.save(outfile_name+".png")
    if config_file.get("copy_to_www_dir") == True:
        copy_to_wwwdir(outfile_name+".png")
    return img


def bincode_image(im: Image, outfile_name:str):
    """
    Takes a PIL Image (im) to be encoded for display
    on the ePaper and to be written to a file named
    outfile.
    Writes hash file to disk using calc_bin_image_hash().
    Doesn't return any value.
    """
    contents = []
    # Write output file.
    for y in range(0, im.size[1]):
        value = 0
        done = True
        for x in range(0, im.size[0]):
            pixel = im.getpixel((x, y))
            if x % 2 == 0:
                value = pixel >> 4
                done = False
            else:
                value |= pixel & 0xF0
                contents.append(value.to_bytes(1, "little"))
                done = True
        if not done:
            contents.append(value.to_bytes(1, "little"))
    data = b"".join(contents)
    print(type(data))
    with open(outfile_name, "wb") as f:
        f.write(data)
    #content_hash = hashlib.sha256(data).hexdigest()
    #with open(outfile + ".sha", "wb") as f:
    #    f.write(content_hash.encode())
    calc_bin_image_hash(data, outfile_name)
    if config_file.get("copy_to_www_dir") == True:
        copy_to_wwwdir(outfile_name)

def calc_bin_image_hash(data: bytes, bin_filename: str):
    """
    Calculate SHA-256 hash of data
    Write to file given by binFileName appending .sha to it
    Returns hash. If specified, copy hash file to www dir.
    """
    content_hash = hashlib.sha256(data).hexdigest()
    with open(bin_filename + ".sha", "wb") as f:
        f.write(content_hash.encode())
    if config_file.get("copy_to_www_dir") == True:
        copy_to_wwwdir(bin_filename + ".sha")
    return content_hash

def copy_to_wwwdir(infilename: str):
    """
    Copy file to www server directory.
    Destination path must be given in config file (www_dir).
    infilename will be appended to path given in config file.

    Be careful. Destination files will be overwritten!
    Must be able to access directory (which is to be provided to the user
    running this script by the container environment).
    """
    # copy to web server directory
    # yessir to any prompt
    # you have been warned!
    # Done: Change container environment to be able to do this
    # without sudo (big change). Usage of sudo makes this a script reliant
    # on a unix-like environment.
    www_dir = config_file.get("www_dir")
    # this is so unsafe...
    # please, please, never mount any host dir into the container
    #cmd_str = "yes | sudo cp " + infilename + " " + www_dir+"/"+infilename
    cmd_str = "yes | cp " + infilename + " " + www_dir+"/"+infilename
    print(cmd_str)
    subprocess.run(cmd_str, shell=True)

def line_chart(ds):
    """
    Create line chart from Pandas data seriesholding hourly price data.
    Parameters:
        Pandas data series.
    Returns:
        figure object
    """
    # Plot the data series as a line chart that looks like a bar chart
    # more like the tibber chart. entirely sufficient for b/w plotting
    # we just need to remove the date and only plot time values on the x axis

    # get current time as a timestamp
    # this is timezone-naive
    now = pd.Timestamp.now()
    # we only care about the current hour
    #now = pd.Timestamp.now().floor('H')
    # but we have tz-aware timestamps in the data series
    # so we need to make it aware of tz
    now = now.tz_localize(tz=config_file.get("timezone"))
    if now is None:
        # just in case if something went wrong
        print("Unable to get current date/time. \
              Check timezone declaration in config file.")
        sys.exit(1)

    # fuck matplotlib and their inches. and decimal separator (see below)
    # https://matplotlib.org/stable/gallery/subplots_axes_and_figures/figure_size_units.html
    px = 1/plt.rcParams['figure.dpi']  # pixel in inches
    iwidth = config_file.get("chart_width")
    iheight = config_file.get("chart_height")
    if (iwidth is None) or (iheight is None):
        print("Unable to get width and/or height from config file. Exit.")
        sys.exit(1)
    fig, ax = plt.subplots(figsize=(iwidth*px, iheight*px))

    # Tell matplotlib to use the locale we set above
    loc_langterr = config_file.get("loc_langterr")
    if loc_langterr is None:
        print("Unable to determine language/territory of locale. Exit.")
        sys.exit(1)
    loc_codeset = config_file.get("loc_codeset")
    if loc_codeset is None:
        print("Unable to determine codeset of locale. Exit.")
        sys.exit(1)
    locale.setlocale(locale.LC_NUMERIC, (loc_langterr, loc_codeset))
    plt.rcParams['axes.formatter.use_locale'] = True

    print("Start date: ", start.strftime('%Y-%m-%d'))
    print("End date: ", end.strftime("%Y-%m-%d"))
    # Chart label 
    # configurable from config file
    if config_file.get("update_timestamp") is False:
        plt.title(config_file.get("label_str") + start.strftime('%d.%m.%Y'))
    else:
        # set additional timestamp info
        plt.title(config_file.get("label_str") + start.strftime('%d.%m.%Y') +
                  ", updated " + now.strftime('%Y-%m-%d %X'))

    xlabel_str = config_file.get("xlabel_str")
    if xlabel_str is None:
        # just set german default if not specified.
        xlabel_str = "Stunde"
    plt.xlabel(xlabel_str)

    # y-label to be according to
    # price calculation result (i.e. €/MWh if raw data
    # and Cents/kWh if all inclusive pricing)
    if config_file.get("raw_pricing") == True:
        plt.ylabel('€/MWh')
        # we're talking Euros/MWh
        # annotation line needs more space
        # used for positive values
        # negative values will be fixed at distance 1
        annot_space = 20
        # same for annotation text
        text_space = 25
        # leave room for annotation of negative values
        # if contained in data
        annot_neg_space = 30
        annot_pos_space = 40
    else:
        plt.ylabel('Cents/kWh')
        # cents/kWh
        # less space for annotation line
        # used for positive values
        # negative values will be fixed at distance 1
        annot_space = 2
        # also less space for annotation text
        text_space = 3
        annot_neg_space = 5
        annot_pos_space = 10
        
    # wtf are timezones?
    # https://github.com/pandas-dev/pandas/issues/2106
    #plt.gca().xaxis.set_major_formatter(md.DateFormatter('%H', \
    #    timezone('Europe/Berlin')))
    plt.gca().xaxis.set_major_formatter(md.DateFormatter('%H', \
        timezone))
    # TODO: Make this configurable (options file)
    # set tick for each bar.
    tick_positions = ds.index
    plt.gca().xaxis.set_ticks(tick_positions)

    plt.step(ds.index, ds.values, where='mid', linewidth=2, color='k')

    # adjust ylim to fit labels
    # leave headroom for  annotation
    ax.set_ylim(top=max(ds.values)+annot_pos_space)
    # values normally start at zero
    # we don't want the line to float around without
    # having a base reference (i.e. ZERO)
    ax.set_ylim(ymin=0)
    # we'd normally have positive values.
    # sometimes maybe negative
    # take care of that by giving space for annotation of values
    if min(ds.values) < 0: 
        ax.set_ylim(bottom = min(ds.values)-annot_neg_space)

    rounded_indices = ds.index.floor('H')

    # works but is deprecated
    #print(ds.index.get_loc(now, method='nearest'))
    # new way of doing things
    # find number of index matching the current hour
    indexnum = ds.index.get_indexer([now], method='nearest')[0]
    if config_file.get("debug") is True:
        print(ds.index.get_indexer([now], method='nearest')[0])
    # check if value fits
    # we start at zero (it's a list...)
    if config_file.get("debug") is True:
        print("Current price [€/MWh]: ",ds[indexnum])

    # Add an annotation above the bar giving price for current time / hour
    annotated_value = ds[indexnum]
    # find max to place label above all bars so we won't collide with any
    # bar
    max_value = ds.values.max()
    # we need to do this according to value of bar
    # values <= 0 : start at zero (above bar)
    # values > 0 : start above bar
    curlabel_str = config_file.get("curlabel_str")
    if curlabel_str is None:
        # don't worry. we default to gerrrmän
        curlabel_str = "Momentan: "
    if annotated_value <= 0:
        ax.annotate(f'{curlabel_str}: {annotated_value:.2f}',
                    xy=(ds.index[indexnum], 1),    #fix y at 1
                    xytext=(ds.index[indexnum], max_value+text_space),
                    ha='center',  fontsize=15,          
                    arrowprops=dict(arrowstyle="-"))
    else:
        # value was greater zero
        ax.annotate(f'{curlabel_str}: {annotated_value:.2f}',
                    # y + 20 should leave enough space
                    xy=(ds.index[indexnum], annotated_value + annot_space),
                    xytext=(ds.index[indexnum], max_value+text_space),
                    ha='center', fontsize=15,
                    arrowprops=dict(arrowstyle="-"))
    # add basic information
    # like daily (non-weighted) average
    # minimum and maximum price including hour
    # that means we need to find some free space in the figure
    # matplotlib doesn't really support this.
    # see https://github.com/matplotlib/matplotlib/issues/1313
    # so we just make a lazy effort at deconfliction:
    # if we're before 12:00: put it in the right hand upper corner
    # if after, put it in the left hand upper corner
    # hopefully, we won't run into our label indicating the current hour
    text_kwargs = dict(ha='left', va='top', fontsize=15, color='k',\
                       transform=ax.transAxes)
    val_kwargs = dict(ha='right', va='top', fontsize=15, color='k',\
                       transform=ax.transAxes)
    # set rc params to monospace
    # for proper alignment of decimal separator
    plt.matplotlib.rcParams['font.family'] = ['monospace']
    min_price = min(ds.values)
    max_price = max(ds.values)
    max_value = ds.values.max()
    if config_file.get("debug") is True:
        print("Max value: ",max_value)
    max_index = ds.idxmax()
    if config_file.get("debug") is True:
        print("Max index: ",max_index)
    min_index = ds.idxmin()
    if config_file.get("debug") is True:
        print("Min index: ",min_index)
    min_time = min_index.strftime('%H:%M')
    max_time = max_index.strftime('%H:%M')
    p_average = ds.mean()
    if config_file.get("debug") is True:
        print("Average: ",p_average)
        print(type(p_average))
    text_str = (f'Max:{max_price:6.2f} ({max_time})\n'
                f'Min:{min_price:6.2f} ({min_time})')
    if config_file.get("do_average") == True:
        text_str = (text_str + "\n" + 
                    f'Av :{p_average:6.2f}')
    if now.hour <= 12:
        # top right corner
        plt.text(0.65, 0.95, text_str, **text_kwargs)        
    else:
        # top left corner
        plt.text(0.05, 0.95, text_str, **text_kwargs)

    # Display the chart (debug)
    if config_file.get("debug") is True:
        plt.show(block=False)
    return fig


def bar_chart(ds):
    """
    Create bar chart from Pandas data series holding hourly price data.
    Parameters:
        Pandas data series.
    Returns:
        figure object
    """

    # try getting timezone from config file
    # if fail, exit
    timezone = config_file.get("timezone")
    if timezone is None:
        print("Unable to get time zone freom config file. Exit.")
        sys.exit(1)

    # get current time as a timestamp
    # this is timezone-naive
    now = pd.Timestamp.now()
    # we only care about the current hour
    #now = pd.Timestamp.now().floor('H')
    # but we have tz-aware timestamps in the data series
    # so we need to make it aware of tz
    now = now.tz_localize(tz=config_file.get("timezone"))
    if now is None:
        # just in case if something went wrong
        print("Unable to get current date/time. \
              Check timezone declaration in config file.")
        sys.exit(1)

    # try getting locale from config
    # exit if fail
    loc_langterr = config_file.get("loc_langterr")
    if loc_langterr is None:
        print("Unable to determine language/territory of locale. Exit.")
        sys.exit(1)
    loc_codeset = config_file.get("loc_codeset")
    if loc_codeset is None:
        print("Unable to determine codeset of locale. Exit.")
        sys.exit(1)
    locale.setlocale(locale.LC_NUMERIC, (loc_langterr, loc_codeset))
    # Tell matplotlib to use the locale we set above
    plt.rcParams['axes.formatter.use_locale'] = True
    
    # let's go for a heat-map style chart
    # like on the tibber website
    # so we are prepared for color displays
    # Define the colormap
    cmap = plt.colormaps['RdYlGn']
    # lower values are better (i.e. low prices)
    # we want these to be green
    # so we need to reverse the color map
    cmap = cmap.reversed()
    # Compute the color for each data point
    colors = cmap(np.linspace(0, 1, len(dayAhead_ds)))

    # Compute the color for each bar
    # highest value should be deepest red
    # we scale the color map accordingly
    colors = cmap(dayAhead_ds.values / dayAhead_ds.values.max())

    # fuck matplotlib and their inches. and decimal separator (see above)
    # https://matplotlib.org/stable/gallery/subplots_axes_and_figures/figure_size_units.html
    px = 1/plt.rcParams['figure.dpi']  # pixel in inches
    iwidth = config_file.get("chart_width")
    iheight = config_file.get("chart_height")
    # try getting chart dim from config
    # exit if fail
    if (iwidth is None) or (iheight is None):
        print("Unable to get width and/or height from config file. Exit.")
        sys.exit(1)
    # set chart dimensions as per config file
    fig, ax = plt.subplots(figsize=(iwidth*px, iheight*px))
   
    # Plot the data series as a bar chart with colored bars
    vbars = ax.bar(dayAhead_ds.index, dayAhead_ds.values, color=colors, width=0.025)
    # Set the chart title and axis labels
    print("Start date: ", start.strftime('%Y-%m-%d'))
    print("End date: ", end.strftime("%Y-%m-%d"))

    # Chart label 
    # configurable from config file
    if config_file.get("update_timestamp") is False:
        plt.title(config_file.get("label_str") + start.strftime('%d.%m.%Y'))
    else:
        # set additional timestamp info
        plt.title(config_file.get("label_str") + start.strftime('%d.%m.%Y') +
                  ", updated " + now.strftime('%Y-%m-%d %X'))

    xlabel_str = config_file.get("xlabel_str")
    if xlabel_str is None:
        # just set german default if not specified.
        xlabel_str = "Stunde"
    plt.xlabel(xlabel_str)

    # y-label to be according to
    # price calculation result (i.e. €/MWh if raw data
    # and Cents/kWh if all inclusive pricing)
    if config_file.get("raw_pricing") == True:
        plt.ylabel('€/MWh')
        # we're talking Euros/MWh
        # annotation line needs more space
        # used for positive values
        # negative values will be fixed at distance 1
        annot_space = 45
        # same for annotation text
        text_space = 55
        # leave room for annotation of negative values
        # if contained in data
        annot_neg_space = 30
        annot_pos_space = 30
        # headroom for max price annotation is too small
        # hack around that
        annot_add_ylim = 50
        # put box safely out of bar region
        annot_sub_ylim = 70
    else:
        plt.ylabel('Cents/kWh')
        # cents/kWh
        # less space for annotation line
        # used for positive values
        # negative values will be fixed at distance 1
        annot_space = 6
        # also less space for annotation text
        text_space = 7
        annot_neg_space = 5
        annot_pos_space = 10
        # headroom for max price annotation is sufficient
        annot_add_ylim = 0
        # put box safely out of bar region
        annot_sub_ylim = 0

    # wtf are timezones?
    # https://github.com/pandas-dev/pandas/issues/2106
    plt.gca().xaxis.set_major_formatter(md.DateFormatter('%H', \
        timezone))
    # TODO: Make this configurable (options file)
    # set tick for each bar.
    tick_positions = dayAhead_ds.index
    plt.gca().xaxis.set_ticks(tick_positions)
    # Label bars with price
    # fuck this decimal separator
    # maybe use callable?
    # https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.bar_label.html
    ax.bar_label(vbars, fmt='%.2f', rotation = 90, padding = 10)

    # leave headroom for  annotation
    ax.set_ylim(top=max(ds.values)+annot_pos_space+annot_add_ylim)

    #FIXME. take into account variable headroom
    # same as for line chart
    
    #ax.set_ylim(top=max(dayAhead_ds.values)+30)  # adjust ylim to fit labels
    
    # we'd normally have positive values.
    # sometimes maybe negative
    # take care of that by giving space for annotation of values
    if min(dayAhead_ds.values) < 0: 
        ax.set_ylim(bottom = min(dayAhead_ds.values)-annot_neg_space-
                    annot_sub_ylim)
    
    # now at beginning
    # get current time as a timestamp
    # this is timezone-naive
    #now = pd.Timestamp.now()
    # but we have tz-aware timestamps in the data series
    # so we need to make it aware of tz
    #now = now.tz_localize(tz=timezone)
    #if now is None:
    #    # just in case if something went wrong
    #    print("Unable to get current date/time. \
    #          Check timezone declaration in config file.")
    #    sys.exit(1)

    rounded_indices = dayAhead_ds.index.floor('H')

    # works but is deprecated
    #print(dayAhead_ds.index.get_loc(now, method='nearest'))
    # new way of doing things
    # find number of index matching the current hour
    indexnum = dayAhead_ds.index.get_indexer([now], method='nearest')[0]
    if config_file.get("debug") is True:
        print(dayAhead_ds.index.get_indexer([now], method='nearest')[0])
    # check if value fits
    # we start at zero (it's a list...)
    if config_file.get("debug") is True:
        print("Current price [€/MWh]: ",dayAhead_ds[indexnum])

    # Add an annotation above the bar giving price for current time / hour
    annotated_value = dayAhead_ds[indexnum]
    # find max to place label above all bars so we won't collide with any
    # bar
    max_value = dayAhead_ds.values.max()
    # we need to do this according to value of bar
    # values <= 0 : start at zero (above bar)
    # values > 0 : start above bar
    curlabel_str = config_file.get("curlabel_str")
    if curlabel_str is None:
        # don't worry. we default to gerrrmän
        curlabel_str = "Momentan: "

    if annotated_value <= 0:
        ax.annotate(f'{curlabel_str}: {annotated_value:.2f}',
                    xy=(ds.index[indexnum], 1),    #fix y at 1
                    xytext=(ds.index[indexnum], max_value+text_space),
                    ha='center',  fontsize=15,          
                    arrowprops=dict(arrowstyle="-"))
    else:
        # value was greater zero
        ax.annotate(f'{curlabel_str}: {annotated_value:.2f}',
                    # y + 20 should leave enough space
                    xy=(ds.index[indexnum], annotated_value + annot_space),
                    xytext=(ds.index[indexnum], max_value+text_space),
                    ha='center', fontsize=15,
                    arrowprops=dict(arrowstyle="-"))

    # add basic information
    # like daily (non-weighted) average
    # minimum and maximum price including hour
    # that means we need to find some free space in the figure
    # matplotlib doesn't really support this.
    # see https://github.com/matplotlib/matplotlib/issues/1313
    # so we just make a lazy effort at deconfliction:
    # if we're before 12:00: put it in the right hand upper corner
    # if after, put it in the left hand upper corner
    # hopefully, we won't run into our label indicating the current hour
    # TODO:
    # place this correctly when negative prices occur.
    text_kwargs = dict(ha='left', va='top', fontsize=15, color='k',\
                       transform=ax.transAxes)
    val_kwargs = dict(ha='right', va='top', fontsize=15, color='k',\
                       transform=ax.transAxes)
    box_props = dict(facecolor='white')
    # set rc params to monospace
    # for proper alignment of decimal separator
    plt.matplotlib.rcParams['font.family'] = ['monospace']
    min_price = min(ds.values)
    max_price = max(ds.values)
    max_value = ds.values.max()
    if config_file.get("debug") is True:
        print("Max value: ",max_value)
    max_index = ds.idxmax()
    if config_file.get("debug") is True:
        print("Max index: ",max_index)
    min_index = ds.idxmin()
    if config_file.get("debug") is True:
        print("Min index: ",min_index)
    min_time = min_index.strftime('%H:%M')
    max_time = max_index.strftime('%H:%M')
    p_average = ds.mean()
    if config_file.get("debug") is True:
        print("Average: ",p_average)
        print(type(p_average))
    text_str = (f'Max:{max_price:6.2f} ({max_time})\n'
                f'Min:{min_price:6.2f} ({min_time})')
    if config_file.get("do_average") == True:
        text_str = (text_str + "\n" + 
                    f'Av :{p_average:6.2f}')
    if now.hour <= 12:
        # default
        # bottom right corner
        # TODO:
        # if currently negative prices: move to top
        plt.text(0.65, 0.20, text_str, **text_kwargs, bbox=box_props)        
    else:
        # bottom left corner
        # TODO:
        # if currently negative prices: move to top
        plt.text(0.05, 0.20, text_str, **text_kwargs, bbox=box_props)
        
    # Display the chart (debug)
    if config_file.get("debug") is True:
        plt.show(block=False)
    return fig


def calc_price(spotrate):
    """
    Do price calculation for Tibber pricing. To be applied to
    each value in the time series: ds.apply()
    Parameters:
        raw spot market price
    Retuns:
        tibber rate
    """
    etax = config_file.get("etax")
    if etax is None:
        print("No electricity tax given. Exit.")
        sys.exit(1)
    net_charge = config_file.get("net_charge")
    if net_charge is None:
        print("No network charge given. Exit.")
        sys.exit(1)
    conc = config_file.get("concession")
    if conc is None:
        print("No concession given. Exit.")
        sys.exit(1)
    lev = config_file.get("levies")
    if lev is None:
        print("No levies given. Exit.")
        sys.exit(1)
    tib = config_file.get("tibber")
    if tib is None:
        print("No tibber markup given. Exit.")
        sys.exit(1)
    vat = config_file.get("vat")
    if vat is None:
        print("No VAT given. Exit.")
        sys.exit(1)
    if config_file.get("debug") is True:
        print("etax: ",etax)
        print("ncharge: ",net_charge)
        print("conc: ",conc)
        print("lev: ",lev)
        print("tib: ",tib)
        print("vat: ",vat)
        
    markup =  etax + net_charge + conc + lev + tib
    if config_file.get("debug") is True:
        print("Markup excl. VAT: ", markup)
    result = spotrate /10 + markup
    if config_file.get("debug") is True:
        print("result excl. VAT: ", result)
    result = result + result*0.19
    if config_file.get("debug") is True:
        print("result incl. VAT: ", result)
        print("Spotrate: ", spotrate, "Result: ",result)
    return result




if __name__ == '__main__':
    # read config from file
    # maybe, maybe TODO:
    # we should pass around select content instead of relying
    # on this global variable...
    try:
        config_file = yaml.safe_load(open("config.yaml",'rb'))
    except Exception as e:
        print("Unable to load config file. Either non-existent or corrupt.\n"
              "Cannot continue. Exit.")
        print(repr(e))
        sys.exit(1)

    timezone = config_file.get("timezone")
    if timezone is None:
        print("Unable to get time zone freom config file. Exit.")
        sys.exit(1)

    api_key = config_file.get("api_key")
    if api_key is None:
        print("Unable to get API key from config file. Exit.")
        sys.exit(1)
            
    # get current date (this will return a python datetime object)
    start = pd.Timestamp.now(tz=timezone).date()
    #print(type(start), start)
    # convert the datetime back to a timestamp object
    start = pd.Timestamp(start, tz=timezone)
    #print("nach konvertierung Start: ",type(start), start)

    # fun fact: setting the end date greater than date where
    # last value is available will not raise an error
    # we'll just get all available values
    # so we don't have to worry about when price fixing will have
    # happended.
    if config_file.get("max_lookahead") == True:
        # can't lool ahead for more than 2 days...
        end = pd.Timestamp.now(tz=timezone).date()+ \
              datetime. timedelta(days=2)
        end = pd.Timestamp(end, tz=timezone)
    else:
        # didn't get config option or
        # set to false
        # -> get data for current day only
        end = pd.Timestamp.now(tz=timezone).date()+ \
              datetime. timedelta(days=1)
        end = pd.Timestamp(end, tz=timezone)

    #print(type(end), end)
    #end = pd.Timestamp('20230329', tz='Europe/Berlin')

    country_code = config_file.get("country_code")
    if country_code is None:
        print("Unable to get country_code from config file. Exit.")
        sys.exit(1)

    # die xml-abfrage gibt uns auch die 15 min-werte
    #client = entsoe.EntsoeRawClient(api_key=api_key)
    #xml_string = client.query_day_ahead_prices(country_code, start, end)
    #print(xml_string)

    # die pandas-abfrage gibt nur die 60 min werte:
    # bei start am heutigen tage (24.03.) und end am morgigen tage (25.03.)
    # kriegen wir 25 werte zurück
    # hat jetzt auch nichts mit zeitumstellung zu tun, ist erst morgen
    # (25. auf 26.)
    ##2023-03-24 00:00:00+01:00     55.12
    ##2023-03-24 01:00:00+01:00     43.80
    ##2023-03-24 02:00:00+01:00     40.67
    ##2023-03-24 03:00:00+01:00     40.18
    ##2023-03-24 04:00:00+01:00     35.07
    ##2023-03-24 05:00:00+01:00     40.19
    ##2023-03-24 06:00:00+01:00     62.44
    ##2023-03-24 07:00:00+01:00     81.23
    ##2023-03-24 08:00:00+01:00     81.23
    ##2023-03-24 09:00:00+01:00     62.36
    ##2023-03-24 10:00:00+01:00     36.95
    ##2023-03-24 11:00:00+01:00     25.28
    ##2023-03-24 12:00:00+01:00     11.47
    ##2023-03-24 13:00:00+01:00      3.99
    ##2023-03-24 14:00:00+01:00      2.07
    ##2023-03-24 15:00:00+01:00      5.84
    ##2023-03-24 16:00:00+01:00     29.59
    ##2023-03-24 17:00:00+01:00     79.53
    ##2023-03-24 18:00:00+01:00    101.02
    ##2023-03-24 19:00:00+01:00    116.23
    ##2023-03-24 20:00:00+01:00     96.92
    ##2023-03-24 21:00:00+01:00     82.50
    ##2023-03-24 22:00:00+01:00     76.20
    ##2023-03-24 23:00:00+01:00     64.90
    ##2023-03-25 00:00:00+01:00     15.30

    pclient = entsoe.EntsoePandasClient(api_key=api_key)
    # returns pandas series
    # try to catch errors
    try:
        print("Getting price data from ENTSO-E...")
        dayAhead_ds = pclient.query_day_ahead_prices(country_code, start=start,end=end)
    except Exception as ex:
        print("Unable to retrieve data from ENTSO-E platform. Exit.")
        print(repr(ex))
        print("Probable cause: Incorrect date(s) given. Dates used were ",
              start, " and ", end, ".")
        sys.exit(1)
    print("Got data.")
    # print it?
    # https://stackoverflow.com/questions/19124601/pretty-print-an-entire-pandas-series-dataframe
    with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
        print(dayAhead_ds)

    # apply additional charges and vat?
    # we default to raw spot market data
    if config_file.get("raw_pricing") == False:        
        print("Including additional fees in pricing data..")
        # apply additional charge/vat calculation
        # to each value in data series
        dayAhead_ds = dayAhead_ds.apply(calc_price)
        
    else:
        print("Will continue with raw pricing data from ENTSO-E...")

    # debug print    
    with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
        print(dayAhead_ds)

    # which chart?
    # line or bar?
    # we default to bar
    outfile_name = config_file.get("outfile_name")
    if config_file.get("chart_style") == "line":
        chart = line_chart(dayAhead_ds)
    else:
        chart = bar_chart(dayAhead_ds)
    print("chart1 done")
    print(type(chart))
    #chart_img = Image.frombytes('RGB', chart.get_width_height(),
    #                                chart.tostring_rgb())
    # f*ck me. we need to explicitly draw the figure
    # else we'll have these stupid renderer errors...
    chart.canvas.draw()
    print("drawn")
    chart_img = Image.frombytes('RGB',
                                chart.canvas.get_width_height(),chart.canvas.tostring_rgb())
    # convert to bw
    thresh = 200
    fn = lambda x : 255 if x > thresh else 0
    bw_image = chart_img.convert('L').point(fn, mode='1')
    print("converted")
    bw_image.save(outfile_name+'.png')
    print("saved")
    # copy over to www server directory
    if config_file.get("copy_to_www_dir") == True:
        copy_to_wwwdir(outfile_name+'.png')
    # convert to bin representation for
    # display on epaper
    # and write file containing hash
    bincode_image(bw_image, outfile_name + ".bin")
    print("bincoded/hashed")
    
    # now, for the next day chart if specified
    # i know, thats stupid
    # might have thought of it in advance and just put the code
    # inside a function...
    # but stupid is as stupid does.
    print("checking next day?")
    if config_file.get("next_day") is True:
        # add one day to start timestamp
        # will result im datetime object
        start = pd.Timestamp.now(tz=timezone).date()+ \
              datetime.timedelta(days=1)
        # convert back to pandas timestamp
        start = pd.Timestamp(start, tz=timezone)
        # can't lool ahead for more than 2 days...
        # add two days to end timestamp
        end = pd.Timestamp.now(tz=timezone).date()+ \
              datetime.timedelta(days=2)
        end = pd.Timestamp(end, tz=timezone)
        try:
            outfile_name = config_file.get("outfile2_name")
        except:
            print("Unable to get filename for day 2 chart from config. Exit.")
            sys.exit(1)
            
        # try to catch errors
        try:
            print("Getting price data from ENTSO-E...")
            dayAhead_ds = pclient.query_day_ahead_prices(country_code, start=start,end=end)
        except Exception as ex:
            print("Unable to retrieve data from ENTSO-E platform. Exit.")
            print(repr(ex))
            print("Probable cause: Prices not fixed yet for next day. \
                  Dates used were ", start, " and ", end, ".")
            chart_img = create_error_image(outfile_name,
                                           "Unable to get data from ENTSO-E")
            # convert to bw
            thresh = 200
            fn = lambda x : 255 if x > thresh else 0
            bw_image = chart_img.convert('L').point(fn, mode='1')
            bw_image.save(outfile_name+'.png')
            if config_file.get("copy_to_www_dir") == True:
                copy_to_wwwdir(outfile_name+'.png')
            # convert to bin representation for
            # display on epaper
            # and write file containing hash
            bincode_image(bw_image, outfile_name + ".bin")
            
            sys.exit(1)
        print("Got data.")
        # print it?
        # https://stackoverflow.com/questions/19124601/pretty-print-an-entire-pandas-series-dataframe
        with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
            print(dayAhead_ds)
        # apply additional charges and vat
        # we default to raw spot market data
        if config_file.get("raw_pricing") == False:        
            print("Including additional fees in pricing data..")
            # apply additional charge/vat calculation
            # to each value in data series
            dayAhead_ds = dayAhead_ds.apply(calc_price)            
        else:
            print("Will continue with raw pricing data from ENTSO-E...")

        # debug print    
        with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
            print(dayAhead_ds)
        # which chart?
        # line or bar?
        # we default to bar
        
        if config_file.get("chart_style") == "line":
            chart = line_chart(dayAhead_ds)
        else:
            chart = bar_chart(dayAhead_ds)
        print("chart done")
        print(type(chart))        
        # f*ck me. we need to explicitly draw the figure
        # else we'll have these stupid renderer errors...
        chart.canvas.draw()
        chart_img = Image.frombytes('RGB',
                                    chart.canvas.get_width_height(),chart.canvas.tostring_rgb())
        # convert to bw
        thresh = 200
        fn = lambda x : 255 if x > thresh else 0
        bw_image = chart_img.convert('L').point(fn, mode='1')
        bw_image.save(outfile_name+'.png')
        # copy over to www server directory
        if config_file.get("copy_to_www_dir") == True:
            copy_to_wwwdir(outfile_name+'.png')
        # convert to bin representation for
        # display on epaper
        # and write file containing hash
        bincode_image(bw_image, outfile_name + ".bin")

