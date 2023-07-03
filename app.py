from urllib.request import urlopen
import openai
import pandas as pd
import json
import requests
import os
from apikey import OPENAI_API_KEY, FMP_API_KEY
openai.api_key = OPENAI_API_KEY


def get_jsonparsed_data(url):
    """
    Receive the content of ``url``, parse it as JSON and return the object.

    Parameters
    ----------
    url : str

    Returns
    -------
    dict
    """
    response = urlopen(url)
    data = response.read().decode("utf-8")
    print(data)
    return json.loads(data)


def get_financial_statements(ticker, limit, period, statement_type):
    if statement_type == "Income Statement":
        url = f"https://financialmodelingprep.com/api/v3/income-statement/{ticker}?period={period}&limit={limit}&apikey={FMP_API_KEY}"
    elif statement_type == "Balance Sheet":
        url = f"https://financialmodelingprep.com/api/v3/balance-sheet-statement/{ticker}?period={period}&limit={limit}&apikey={FMP_API_KEY}"
    elif statement_type == "Cash Flow":
        url = f"https://financialmodelingprep.com/api/v3/cash-flow-statement/{ticker}?period={period}&limit={limit}&apikey={FMP_API_KEY}"

    data = get_jsonparsed_data(url)

    if isinstance(data, list) and data:
        # Create a folder for storing each company's financial statements
        data_folder = f"{ticker}_financial_data"
        os.makedirs(data_folder, exist_ok=True)

        # Save each financial statement as a separate JSON file
        for i, statement in enumerate(data):
            file_path = os.path.join(
                data_folder, f"{ticker}_{statement_type}_{period}_{i+1}.json")
            with open(file_path, "w") as f:
                json.dump(statement, f, indent=4)

        return pd.DataFrame(data)
    else:
        print("Unable to fetch financial statements. Please ensure the ticker is correct and try again.")
        return pd.DataFrame()


def generate_financial_summary(financial_statements, statement_type, ticker):
    """
    Generate a summary of financial statements for the statements using GPT-3.5 Turbo or GPT-4.
    """

    # Create a summary of key financial metrics for all periods
    summaries = []
    for _, row in financial_statements.iterrows():
        if statement_type == "Income Statement":
            summary = f"""
                For the period ending {row['date']}, the company reported the following:
                Revenue: {row['revenue']}

                Cost of Revenue: {row['costOfRevenue']}

                Gross Profit: {row['grossProfit']}
                Gross Margin: {row['grossProfitRatio']}

                Operating Expenses: {row['operatingExpenses']}
                interest Expense: {row['interestExpense']}
                depreciation and Amortization: {row['depreciationAndAmortization']}
                ebitda: {row['ebitda']}
                ebitda Margin: {row['ebitdaratio']}
                Operating Income: {row['operatingIncome']}
                operating Income Margin: {row['operatingIncomeRatio']}


                Income Tax Expense: {row['incomeTaxExpense']}
                
                Net Income: {row['netIncome']}
                Earnings per Share: {row['eps']}
                ...
                """
        elif statement_type == "Balance Sheet":
            summary = f"""
                For the period ending {row['date']}, the company reported the following:
                Assets: {row['totalAssets']}
                Liabilities: {row['totalLiabilities']}
                Equity: {row['totalStockholdersEquity']}
                ...
                """
        elif statement_type == "Cash Flow":
            summary = f"""
                For the period ending {row['date']}, the company reported the following:
                Operating Cash Flow: {row['operatingCashflow']}
                Investing Cash Flow: {row['cashFlowFromInvestment']}
                Financing Cash Flow: {row['cashFlowFromFinancing']}
                ...
                """
        summaries.append(summary)

    # Combine all summaries into a single string
    all_summaries = "\n\n".join(summaries)

    # Call GPT-4 for analysis
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "You are an AI trained to provide financial analysis based on financial statements.",
            },
            {
                "role": "user",
                "content": f"""
                Please analyze the following data and provide insights:\n{all_summaries}.\n 
                Write each section out as instructed in the summary section and then provide analysis of how it's changed over the time period and provide detailed/concrete forecast assumptions.
                ...
                """


            }


        ]


    )
    # Save the response to a file as text file
    with open("response.txt", "w") as f:
        f.write(response['choices'][0]['message']['content'])
    # move the file to the data folder
    os.rename("response.txt", f"{ticker}_financial_analysis.txt")

    # Return the response

    return response['choices'][0]['message']['content']


def main():
    statement_type = input(
        "Select financial statement type (Income Statement/Balance Sheet/Cash Flow): ")
    period = input("Select period (Annual/Quarterly): ").lower()
    limit = int(input("Number of past financial statements to analyze: "))
    ticker = input("Please enter the company ticker: ").upper()

    if ticker:
        financial_statements = get_financial_statements(
            ticker, limit, period, statement_type)
        if not financial_statements.empty:
            print("\nFinancial Statements:")
            print(financial_statements)

            financial_summary = generate_financial_summary(
                financial_statements, statement_type, ticker)

            print(f"\nSummary for {ticker}:\n{financial_summary}\n")
        else:
            print(
                "Unable to fetch financial statements. Please ensure the ticker is correct and try again.")
    else:
        print("Company ticker not provided.")


if __name__ == '__main__':
    main()
