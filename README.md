# Quandl Google Sheets & Excel Spreadsheet Add-on

Quandl is a premier source for open, commercial, and alternative data, with a particular focus on investment professionals. This Quandl spreadsheet integration for Google Sheets and Microsoft Excel enables you to import table and time-series datasets from Quandl. This add-on will enable you to integrate on-demand, refreshable stock market and portfolio data without leaving your spreadsheet.

For example, with this Excel and Google Sheets add-on you can:

* Extract financial time-series data directly in Excel and Google Sheets, filtering by both columns and date.
* Import tables, such as the Sharadar Fundamentals, and filter based on what is relevant and available for that given data set (e.g., columns, date, ticker, investor, etc.).

Here are some examples:

```
=FLEX("YOUR_TEAM_NAME/quandl-series", "NASDAQOMX/XNDXT25", "trade date, low, high", "2019-09-01", "2019-09-30")
```

```
=FLEX("YOUR_TEAM_NAME/quandl-table", "SHARADAR/SF3", "*", "ticker=AAPL,MSFT&investorname=VANGUARD GROUP INC")
```

## Prerequisites

The Quandl spreadsheet functions utilize [Flex.io](https://www.flex.io) and Quandl](https://www.quandl.com/). To use these functions, you'll need:

* A [Flex.io account](https://www.flex.io/app/signup) to run the functions
* A [Flex.io Add-on](https://www.flex.io/add-ons) for Microsoft Excel or Google Sheets to use the functions in your spreadsheet
* A [Quandl account](https://www.quandl.com/sign-up-modal?defaultModal=showSignUp)

## Installing the Functions

Once you've signed up for Flex.io and have the Flex.io Add-on installed, you're ready to install the function pack.

You can install these functions directly by mounting this repository in Flex.io:

1. [Sign in](https://www.flex.io/app/signin) to Flex.io
2. In the Functions area, click the "New" button in the upper-left and select "Function Mount" from the list
3. In the function mount dialog, select "GitHub", then authenticate with your GitHub account
4. In the respository URL box, enter the name of this repository, which is "flexiodata/functions-quandl"
5. Click "Create Function Mount"

If you prefer, you can also install these using the [Flex.io Quandl Integration](https://www.flex.io/integrations/quandl).

## Using the Functions

Once you've installed the function pack, you're ready to use the functions.

1. Open Microsoft Excel or Google Sheets
2. Open the Flex.io Add-in:
   - In Microsoft Excel, select Home->Flex.io
   - In Google Sheets, select Add-ons->Flex.io
3. In the Flex.io side bar, log in to Flex.io and you’ll see the functions you have installed
4. For any function, click on the “details” in the function list to open a help dialog with some examples you can try at the bottom
5. Simply copy/paste the function into a cell, then edit the formula with a value you want to use

## Documentation

Here are some additional resources:

* [Quandl Function Documentation.](https://www.flex.io/integrations/quandl#functions-and-syntax) Here, you'll find a list of the functions available, their syntax and parameters, as well as examples for how to use them.
* [Flex.io Add-ons.](https://www.flex.io/add-ons) Here, you'll find more information about the Flex.io Add-ons for Microsoft Excel and Google Sheets, including how to install them and use them.
* [Flex.io Integrations.](https://www.flex.io/integrations) Here, you'll find out more information about other spreadsheet function packs available.

## Help

If you have question or would like more information, please feel free to live chat with us at our [website](https://www.flex.io) or [contact us](https://www.flex.io/about#contact-us) via email.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

