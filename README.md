# entsoEchartmaker
Re-create the Tibber Price Chart for ePaper Display. 

This little project aims to re-create the Tibber price chart instead of scraping it from their website. Final result is a container running the script which creates the price chart. The chart in turn will be served to clients by a web server.

This is very, very bad code. But hey, whatever works.

## Why? 
The scraped chart is pretty hard to read. So we'd love to have a more legible display. 

## How? 
Tibber pricing is based off european spot market prices. There's additional cost per kWh caused by transmission fees and some german peculiarities. We need to add these to the spot market price reported to/by ENTSO-E.

## Problems along the way? 
Good luck finding the levies and/or transmission fees you need to add to the raw spot market price. Even then, the result probably won't match the price chart on Tibber's website. That's not a problem, though. Tibber don't know the exact amount of fees/levies themselves and will only be told by your local utility once you have a contract with Tibber.

## Result
This is how the chart looks like with raw spot market pricing (DST Switch):
![ENTSO-E Price Chart (Bars)](entso_e_zeitumstellung.png "ENTSO-E Price Chart Rendering, DST Switch")

This is how a line render of the pricing data looks like with VAT and additional pricing components included:
![Tibber Price Chart (Line)](tibber_entsoe_linechart_vatincl.png "Tibber Price Chart Rendering, Line Style")

## Run it
- Edit ```scripts/config.yaml``` 
  ![Edit config file](edit_config.png "Edit config file")
  - Enter your API key (most important). 
  - Change country code (if desired) to match your location
  - Change language (if desired, optional)
- Build the image: ```docker build . -t tchart```
- Run the image: ```docker run --restart unless-stopped -d -p 8999:8999 --name tchart_run tchart```


## Where Is My Result? (Default Settings)
- Today's chart is available at ```https://<ip>:8999/image.png```
  - Binary format for ePaper: ```https://<ip>:8999/image.bin```
  - Hash of binary file for ePaper: ```https://<ip>:8999/image.sha```
- Tomorrow's chart is available (if data already available) at ```https://<ip>:8999/image2.png```
  - Binary format for ePaper: ```https://<ip>:8999/image2.bin```
  - Hash of binary file for ePaper: ```https://<ip>:8999/image2.sha```
  
# German Electricity Pricing Components
We'll start from raw spot market pricing.  
On top of that, there's
- a concession fee per kWh (given VAT incl. / excl. depending on provider). Municipalities want money for transmission lines run on their territory (Konzession).
- a general fee per kWh for the benefit of the local utility (given VAT incl. / excl.) (Netzgebühr).
- electricity tax per kWh (VAT excl.). Federal government wants money for electricity consumption (Elektrizitätssteuer).
- levies (VAT excl.). Someone has to pay for wtf (KWKG-Umlage, § 19 StromNEV-Umlage, Offshore-Umlage).

Finally, Tibber will add a fixed amount of procurement cost per kWh.

That's electricity pricing only. Additionally, there's a fee for metering point operation. We don't take that into account.

TF, trying to calculate my price.

Pretty much impossible to to. How on earth is any normal person supposed to calculate their resulting price if
- the local utility has parts of these price components strewn all over their website without a single, comprehensive chart
- my current provider (using the local utility for the last mile) shows different re-imbursements to the local utility from what the local utility has on their website
- the levies for offshore and whateverthefuckelse differ from what federal regulations say?
- Tibber do not give details on their price calculation for any given Zip code.

The only thing cosistently given is electricity tax. Well, at least I found out why Tibber don't give price calculation details. 

Let's try Hamburg:
All without VAT, 2023 Pricing:
- General Fee 8,92 Cent/kWh
- Concession: 2,39 Cent/kWh
- Levies:
  - KWKG: 0,357 Cent/kWh (https://www.netztransparenz.de/KWKG/KWKG-Umlagen-Uebersicht)
  - Offshore: 0,591 Cent/kWh (https://www.netztransparenz.de/EnWG/Offshore-Netzumlage/Offshore-Netzumlagen-Uebersicht)
  - Cosumer Fee: 0,417 Cent/kWh (https://www.netztransparenz.de/EnWG/-19-StromNEV-Umlage/-19-StromNEV-Umlagen-Uebersicht)
- Electricity Tax: 2,05 Cent/kWh  

Makes for 14,725 Cents/kWh (VAT excl)

Tibber adds another 0,9Cents / kWh (VAT excl) -> 15,645 Cent/kWh VAT excl.

Add 19% VAT (2,97225 Cents/kWh) -> 18,61755 Cent/kWh (VAT incl)  
Add 19% VAT for Spot Market Rate (9,6Cents/kWh x 0,19 = 1,824 Cent/kWh) -> 20,44155 cent/kWh.  

Guess what: Tibber gives us 20,19 Cent/kWh for taxes and fees.

TF.

After back and forth with some really friendly and helpful people from the Tibber helpline: They themselves only know the exact amount of fees and concession as soon as they have a contract with you. Only then, the local utility will let them know the current rates. So they do the best they can when you enter a ZIP code for a price estimate using averages based on their experience. 

TF, the German electricity market is just so broken. How about the Federal Regulator (Bundesnetzagentur) setting up a database? What the hell are these guys doing?

# Technical Deep Dive
## Choice of Container
There's three possibilities for the base image:
- Docker Official Python Image (based on various distros (Debian, Ubuntu, Alpine) and even Windows): https://hub.docker.com/_/python
- Distro Base Image with additional Python install per Dockerfile
- Distroless Python (https://github.com/GoogleContainerTools/distroless)

Now, what are my criteria?
- I'm lazy. The container will be running for quite a while without being re-created. So we'd like to make sure we can auto-update the container.
- I like it comfortable. Debug options should be included. 
- I have room to spare. While a smaller container would be nice, size is not the main criterion.

The result?
We'll use a distribution base image so we can run unattended upgrades for security fixes. If something breaks, it breaks. I'd rather have a broken container than a security problem (yes, problem). The base distro image will also include a shell for debug while being a bit larger.  


## Config
### Dockerfile
The Dockerfile is your place for configuring:
- Container Timezone (for getting correct raw pricing data from ENTSO-E)
- Locale (Trying to get decimal separator right, TF)
### Config File (config.yaml)
The script config file is located at ```scripts/config.yaml```. There's a multitude of options.

| Option        | Description    | 
| ------------- |:-------------:| 
| copy_to_www_dir   | True or False, Copy chart data (png, bin, sha) to web server directory | 
| www_dir          | Target directory for file copy, no trailing slash!      | 
| debug | True or False, display additional data during script execution      | 
| max_lookahead | True or False, Squeeze all available data into one chart|
| next_day  | True or False, try to get data for next day, create a separate chart from it|
| outfile2_name | Specify file name(s) for nex day chart|
| chart_width | width of chart in pixels (change for different display) |
| chart_height | height of chart in pixels (change for different display) |
| chart_style | bar or line, see above for examples |
| do_average | True or False, Calculate average price for day and annotate on chart|
| raw_pricing | True or False, if True, raw ENTSO-E data will be displayed, if False you need to specify additional pricing components, see below|
| vat | VAT applicable (in percent, without percentage sign) |
| net_charge | Durchleitungsgebühren, Transmission fees (Cent/kWh, dot as decimal separator) |
| concession | Konzession, Concession fees (Cent/kWh, dot as decimal separator)|
| etax | Electricity tax (Cent/kWh, dot as decimal separator) |
| levies | Umlagen (Cent/kWh, dot as decimal separator) |
| tibber | Tibber fee (Cent/kWh)|
| label_str | String, Top chart label |
| curlabel_str | String, label for current price indicator |
| xlabel_str | String, label for x axis |
| update_timestamp | True or False, add date/time of latest update to chart |



