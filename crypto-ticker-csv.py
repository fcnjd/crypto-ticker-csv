import requests
import csv
import argparse
from datetime import datetime

def convert_timestamp(timestamp):
    dt = datetime.fromtimestamp(timestamp / 1000)
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def get_interval(days):
    if days == 1:
        return "5m"
    elif days <= 7:
        return "30m"
    elif days <= 14:
        return "1h"
    elif days <= 30:
        return "4h"
    else:
        return "1d"


# retrieve list of valid crypto_ids and their corresponding cryptocurrency names from the CoinGecko API
response = requests.get("https://api.coingecko.com/api/v3/coins/list")
coins = response.json()
crypto_ids = {coin["id"]: coin["name"] for coin in coins}
vs_currencies = requests.get("https://api.coingecko.com/api/v3/simple/supported_vs_currencies").json()

parser = argparse.ArgumentParser(description='Create a CSV file with cryptocurrency price development. Data intervals: 1 day = 5m, 7 days = 30m, 14 days = 1h, 30 days = 4h, >30 days = 1d.')
parser.add_argument('-i', '--crypto-id', type=str, required=False, help='ID of the cryptocurrency to retrieve data for')
parser.add_argument('-c', '--currency', type=str, required=False, help='Currency to retrieve data in')
parser.add_argument('-d', '--days', type=int, required=False, help='Number of days of price data to retrieve')
parser.add_argument('-l', '--list', action='store_true', help='Print list of valid crypto_id values and corresponding cryptocurrency names')
parser.add_argument('-r', '--readable-timestamps', action='store_true', help='Convert timestamps to a human-readable format')
args = parser.parse_args()

if not args.list and (not args.crypto_id or not args.currency or not args.days):
    parser.error("The --crypto-id, --currency, and --days options are required if not using the --list flag.")

if args.list:
    print("Valid crypto_id values and corresponding cryptocurrency names:")
    for crypto_id, name in crypto_ids.items():
        print(f"{crypto_id}: {name}")
    exit()

# validate the crypto_id input
if args.crypto_id not in crypto_ids:
    print(f"Error: '{args.crypto_id}' is not a valid crypto_id value. Use the --list flag to see valid options.")
    exit()

# validate the currency input
if args.currency not in vs_currencies:
    print(f"Error: '{args.currency}' is not a valid currency. Supported currencies are: {', '.join(vs_currencies)}")
    exit()

# extract the cryptocurrency name from the crypto_ids dictionary
crypto_name = crypto_ids[args.crypto_id]

# make a GET request to the CoinGecko API to retrieve the price data
response = requests.get(f"https://api.coingecko.com/api/v3/coins/{args.crypto_id}/market_chart?vs_currency={args.currency}&days={args.days}")

# check if the response contains price data
if not response.json()["prices"]:
    print(f"Error: No price data found for {crypto_name} in {args.currency} for the last {args.days} days.")
    exit()

# get the interval for the requested days
interval = get_interval(args.days)

# create a CSV file to write the price data to
filename = f"{crypto_name}_{args.currency}_{args.days}d_{interval}_prices.csv"
with open(filename, "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["timestamp", "price"])
    for price in response.json()["prices"]:
        timestamp = price[0]
        if args.readable_timestamps:
            timestamp = convert_timestamp(timestamp)
        writer.writerow([timestamp, price[1]])

print(f"Price data for {crypto_name} in {args.currency} for the last {args.days} days with {interval} intervals written to {filename}.")

