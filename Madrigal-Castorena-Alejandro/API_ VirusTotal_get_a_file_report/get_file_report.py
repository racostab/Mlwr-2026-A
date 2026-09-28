import requests

url = "https://www.virustotal.com/api/v3/files/992b3e05d5eb40e8e9a751b134a7b72a"

headers = {
    "accept": "application/json",
    "x-apikey": "xxxxxxxxxx"
}

response = requests.get(url, headers=headers)

print(response.text)
