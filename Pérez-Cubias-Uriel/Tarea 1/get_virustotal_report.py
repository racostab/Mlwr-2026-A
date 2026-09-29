import requests

url = "https://www.virustotal.com/api/v3/files/%2033c39c78b9aa5ce8ad78dfd41df81792%20"

headers = {
    "accept": "application/json",
    "x-apikey": "a59be554b4190f7228f679d9c7f23f4f9c8c52a3134ebcb732dfe21521e1506e"
}

response = requests.get(url, headers=headers)

print(response.text)