import os
import ccxt
from pprint import pprint
from datetime import datetime
import requests
from dotenv import load_dotenv


# CryptowatchでBTCFXの価格データを取得
def get_price(min, before=0, after=0):
    # Cryptowatchのparamはbefore, after, period
    # before: int Unix timstamp
    # after:  int Unix timstamp
    # period: array Example: 60,180,108000

	price = []
    # 何分単位かを設定
	params = {"periods" : min }
    # ローソク足取得期間が初期値０以外の時の処理
	if before != 0:
		params["before"] = before
	if after != 0:
		params["after"] = after
    
    # OHLCを取得
	response = requests.get("https://api.cryptowat.ch/markets/bitflyer/btcfxjpy/ohlc",params)
	data = response.json()
	
    # dataがNoneでなければデータをdict型に整形してPriceに入れる
	if data["result"][str(min)] is not None:
		for i in data["result"][str(min)]:
			price.append({ "close_time" : i[0],
				"close_time_dt" : datetime.fromtimestamp(i[0]).strftime('%Y/%m/%d %H:%M'),
				"open_price" : i[1],
				"high_price" : i[2],
				"low_price" : i[3],
				"close_price": i[4] })
	return price


def calculate_MA(price, value, before=None):
	"""単純移動平均計算

	単純移動平均を計算する

	Args:
		price(Any) : 価格
		value(Int) : MAの期間
		before(Int) : n足前の指定
	Returns:
		小数を丸めたMA
	"""
	if before is not None:
		MA = sum(i["close_price"] for i in price[-1*value + before: before]) / value
	else:
		MA = sum(i["close_price"] for i in price[-1*value:]) / value
	return round(MA)

def cross_MA(event=None, context=None):
	load_dotenv('.env') # 環境変数読み込み
	bitflyer = ccxt.bitflyer()
	bitflyer.apiKey = os.environ.get("APIKEY")
	bitflyer.secret = os.environ.get("SECRETKEY")

	# 使用する時間足
	chart_sec = 900 # 15分

	# 価格チャートを取得
	price = get_price(chart_sec)

	# 一つ前
	MA10_BEFORE1 = calculate_MA(price, 10, -1)     # 現在の10期間移動平均の数値
	MA21_BEFORE1 = calculate_MA(price, 21, -1)     # 現在の21期間移動平均の数値

	# 現在
	MA10 = calculate_MA(price, 10)     # 現在の10期間移動平均の数値
	MA21 = calculate_MA(price, 21)     # 現在の21期間移動平均の数値

	# 一つ前の移動平均線の状態を設定
	state_line_before1 = 0 # 初期値
	if MA10_BEFORE1 > MA21_BEFORE1:
		state_line_before1 = 1 # プラス傾向
	elif MA10_BEFORE1 < MA21_BEFORE1:
		state_line_before1 = -1 # マイナス傾向

	# 現在の移動平均線の状態を設定
	state_line = 0 # 初期値
	if MA10 > MA21:
		state_line = 1 # プラス傾向
	elif MA10 < MA21:
		state_line = -1 # マイナス傾向

	# 移動平均線を最新と一つ前で比較してクロスしているかを判定
	if state_line_before1 > state_line: #プラスクロス
		order = bitflyer.create_order(
		symbol = 'BTC/JPY',
		type='market',
		side='buy',
		amount='0.01',
		params = { "product_code" : "FX_BTC_JPY" })
		pprint( order )
	elif state_line_before1 < state_line: #マイナスクロス
		order = bitflyer.create_order(
		symbol = 'BTC/JPY',
		type='market',
		side='sell',
		amount='0.01',
		params = { "product_code" : "FX_BTC_JPY" })
		pprint( order )
	else:
		print("クロスしてないから何もしない")

if __name__ == "__main__":
	cross_MA()