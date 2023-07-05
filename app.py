import xlsxwriter
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
                Change in working capital: {row['changeInWorkingCapital']}
                Accounts Receivable: {row['accountsReceivables']}
                Inventory: {row['inventory']}
                Accounts Payable: {row['accountsPayables']}
                Operating Cash Flow: {row['netCashProvidedByOperatingActivities']}
                Investing Cash Flow: {row['netCashUsedForInvestingActivites']}
                Debt Repayment: {row['debtRepayment']}
                Common Stock Issued: {row['commonStockIssued']}
                common Stock Repurchased: {row['commonStockRepurchased']}
                Dividends Paid: {row['dividendsPaid']}
                Financing Cash Flow: {row['netCashUsedProvidedByFinancingActivities']}
                ...
                Operating CashFlow: {row['operatingCashFlow']}
                Capital Expenditure: {row['capitalExpenditure']}
                free Cash Flow: {row['freeCashFlow']}
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

    # Return the response

    return response['choices'][0]['message']['content']


def build_excel_model(income_statements, balance_sheets, cash_flows, ticker):
    """
    Build an Excel model with consolidated financial statements for forecasting.
    """

    # Create a new Excel file
    excel_file = f"{ticker}_financial_model.xlsx"
    workbook = xlsxwriter.Workbook(excel_file)

    # Create worksheets for the financial statements
    income_sheet = workbook.add_worksheet("Income Statement")
    balance_sheet = workbook.add_worksheet("Balance Sheet")
    cash_flow_sheet = workbook.add_worksheet("Cash Flow")

    # Transpose the dataframes
    income_statements = income_statements.transpose()
    balance_sheets = balance_sheets.transpose()
    cash_flows = cash_flows.transpose()

    # Write the column headers (years) for each statement
    years = income_statements.columns
    for col_idx, year in enumerate(years):
        income_sheet.write(0, col_idx + 1, year)
        balance_sheet.write(0, col_idx + 1, year)
        cash_flow_sheet.write(0, col_idx + 1, year)

    # Write the item labels and data for each statement
    items_income = income_statements.index
    items_balance = balance_sheets.index
    items_cash = cash_flows.index

    for row_idx, item in enumerate(items_income):
        income_sheet.write(row_idx + 1, 0, item)
        for col_idx, year in enumerate(years[::-1]):
            income_sheet.write(row_idx + 1, col_idx + 1,
                               income_statements.loc[item, year])

    for row_idx, item in enumerate(items_balance):
        balance_sheet.write(row_idx + 1, 0, item)
        for col_idx, year in enumerate(years[::-1]):
            balance_sheet.write(row_idx + 1, col_idx + 1,
                                balance_sheets.loc[item, year])

    for row_idx, item in enumerate(items_cash):
        cash_flow_sheet.write(row_idx + 1, 0, item)
        for col_idx, year in enumerate(years[::-1]):
            cash_flow_sheet.write(row_idx + 1, col_idx + 1,
                                  cash_flows.loc[item, year])

    # Save the Excel file
    workbook.close()

    return excel_file


def main():
    period = input("Select period (Annual/Quarterly): ").lower()
    limit = int(input("Number of past financial statements to analyze: "))
    ticker = input("Please enter the company ticker: ").upper()

    if ticker:

        IncomeStatement = get_financial_statements(
            ticker, limit, period, "Income Statement")
        BalanceSheet = get_financial_statements(
            ticker, limit, period, "Balance Sheet")
        CashFlow = get_financial_statements(
            ticker, limit, period, "Cash Flow")
        if not IncomeStatement.empty and not BalanceSheet.empty and not CashFlow.empty:
            print("\nFinancial Statements:")
            print(f"Income Statement:\n{IncomeStatement}\n")
            print(f"Balance Sheet:\n{BalanceSheet}\n")
            print(f"Cash Flow:\n{CashFlow}\n")

            IncomeStatementSummary = generate_financial_summary(
                IncomeStatement, "Income Statement", ticker)

            CashFlowSummary = generate_financial_summary(
                CashFlow, "Cash Flow", ticker)

            # Save the summaries to a file as text file
            with open("response.txt", "w") as f:
                f.write(
                    f"Income Statement Summary for {ticker}:\n{IncomeStatementSummary}\n")

                f.write(
                    f"Cash Flow Summary for {ticker}:\n{CashFlowSummary}\n")
            # rename the file
            os.rename("response.txt", f"{ticker}_financial_analysis.txt")

            print(
                f"\nIncome Statement Summary for {ticker}:\n{IncomeStatementSummary}\n")
            print(f"\nCash Flow Summary for {ticker}:\n{CashFlowSummary}\n")

            excel_file = build_excel_model(
                IncomeStatement, BalanceSheet, CashFlow, ticker)
            print(f"Excel model created: {excel_file}")
        else:
            print(
                "Unable to fetch financial statements. Please ensure the ticker is correct and try again.")
    else:
        print("Company ticker not provided.")


if __name__ == '__main__':
    main()
