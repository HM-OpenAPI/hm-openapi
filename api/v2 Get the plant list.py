import requests

'''v2 Get the plant list'''
next = 0  # station id
key = "xxxxxxx"  # login key value

url = "https://wapi.hoymiles.com" + f"/v2/plant/list/{next}?key={key}"

headers = {
    'Content-Type': 'application/json;charset=UTF-8'
}

response = requests.post(url=url, headers=headers)

if response.status_code == 200:
    content_type = response.headers.get('Content-Type')
    if content_type == 'application/json;charset=UTF-8':
        res = response.json()
        print(res)
    else:
        print("Unexpected Content-Type:", content_type)
else:
    print("Failed to retrieve data:", response.status_code)
