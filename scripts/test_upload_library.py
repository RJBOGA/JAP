# test_upload_library.py
import requests

url = "http://localhost:8000/users/335/upload_resume"
files = {'resume': open('C:/Users/rajub/Downloads/Nikhil_Controls_Engineer2.docx', 'rb')}

response = requests.post(url, files=files)

print(response.status_code)
print(response.json())