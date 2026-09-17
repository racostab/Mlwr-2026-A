import requests

url = "https://www.virustotal.com/api/v3/files/992b3e05d5eb40e8e9a751b134a7b72a"

headers = {
    "accept": "application/json",
    "x-apikey": "874e92fd80480fdbc3c036b598ec66241229e18ffbec66a80f65f19eb6ee0e60"
}

response = requests.get(url, headers=headers)

print(response.text)
