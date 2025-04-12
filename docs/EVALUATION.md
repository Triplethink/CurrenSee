# Evaluation of market options

I defined the following _Data Source Requirements_ and did some Googling first. Then I used these metrics in Perplexity Deep Research and Gemini Deep Research. Last but not least, I double-checked some of the outputs. In real life (not an interview home-work), I would definitely spend more time on it.

### Data Source Requirements
KEY:
- FREQUENCY: provides daily and hourly data (it is ok if hourly will be for some small fee)
- ACCURACY: do they have some data accuracy disclaimers? Which other companies are using it?
- TRUSTWORTHY: Terms and conditions clarity, does it allow commercial use?
- STABILITY: Availability (is there any status page if the service is alive?)
- DOCUMENTATION: Does it exist? How good is it?
- RATE LIMITS: Clear understanding of request quotas and throttling policies.
- COST: (is there some free tier? What are the limitations etc.?)

NICE TO HAVE:
- Historical data for free
- Official Python SDK
- Custom dashboard for monitoring
- More currencies is of course better, but it is not crucial for us.

### Results from AI (summarized by me)
The models just confirmed that the best way would be to use some API. There are some other options like Python libraries such as [CurrencyConverter](https://pypi.org/project/CurrencyConverter/) or [forex-python](https://github.com/MicroPyramid/forex-python) as well as some public APIs of banks (like European Central Bank, Bank of Canada etc). But all these have some limitations and didn't pass our KEY requirements. So I decided that the best would be to choose from some commercial API providers which offer some good free tier + reasonable tier for future needs (e.g. hourly updates).

#### Top Commercial API providers
The top dog here is [XE Currency Data](https://www.xe.com/xecurrencydata/), but it is very pricey and its features are maybe too advanced, we don't need real-time data, 220 currencies etc.

On the second-fourth place are [fixer.io](https://fixer.io), [Open Exchange Rates](https://openexchangerates.org) and [ExchangeRate-API.com](https://www.exchangerate-api.com), all of these have good free tiers and fulfill almost all the requirements.

### Winner
I've chosen the [Open Exchange Rates](https://openexchangerates.org) as they provide a free tier:
- up to hourly updates (with base currency USD) and up to 1,000 requests/month.
- historical data endpoint
- API [status page](https://status.openexchangerates.org) that can be subscribed even to a slack channel
- a dashboard where you can track your requests and also set some reminders when you are at 80 or 90% of your limit
- returning the data as JSON
The paid tier is for a good price, the [terms and conditions](https://openexchangerates.org/terms) looks clear and allow commercial use. It is also used by some other big tech companies like Kickstarter, Shopify etc. Last but not least the API documentation looks clear.

##  Potential Risks
- Inconsistencies of data - should not be problem with this provider, but we can have some discrepancy and DQ checks
- Outages / API changes - we should be able to use the raw data when needed.
- Licensing / Rate limits - the terms and conditions looks good as well as rate limits, to avoid unnecessary calls I've added `DRY_RUN` param.
- Currency conversion logic errors - we are always using USD as a base, so it should not be a problem.
