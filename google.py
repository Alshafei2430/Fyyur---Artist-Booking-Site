import requests, json

res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "BeQKHKMGw7vdTLOt2JLPPA", "isbns": "9781632168146"})
data = res.json()
print(data["books"][0]["isbn"])