# entsoEchartmaker
Re-create the Tibber Price Chart for ePaper Display. 

This little project aims to re-create the Tibber price chart instead of scraping it from their website. 

Why? The scraped chart is pretty hard to read. So we'd love to have a more legible display. 

How? Tibber pricing is based off european spot market prices. There's additional cost per kWh caused by transmission fees and some german peculiarities. We need to add these to the spot market price reported to/by ENTSO-E.

This is how the chart looks like with raw spot market pricing (DST Switch):
![ENTO-E Price Chart (Bars)](entso_e_zeitumstellung.png "ENTSO-E Price Chart Rendering, DST Switch")

# German Electricity Pricing Components
We'll start from sport market pricing.  
On top of that, there's
- a concession fee per kWh (given VAT incl. / excl. depending on provider). Municipalities want money for transmission lines run on their territory.
- a general fee per kWh for the benefit of the local utility (given VAT incl. / excl.)
- electricity tax per kWh (VAT excl.). Federal government wants money for electricity consumption.
- levies (VAT excl.). Someone has to pay for wtf.

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
All without VAT:
- General Fee 8,92 Cent/kWh
- Concession: 2,39 Cent/kWh
- Levies:
  - KWKG: 0,357 Cent/kWh (https://www.netztransparenz.de/KWKG/KWKG-Umlagen-Uebersicht)
  - 
