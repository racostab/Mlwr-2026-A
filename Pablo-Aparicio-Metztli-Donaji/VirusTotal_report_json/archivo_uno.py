import requests

url = "https://www.virustotal.com/api/v3/files/7f9e869133ec86dd8316e6610419e87e"

headers = {
    "accept": "application/json",
    "x-apikey": "899adc0d8237c25d9500293250c4b9fd15a269ac393c8ac16d8bfd10ac9fa932"
}

response = requests.get(url, headers=headers)

print(response.text)
