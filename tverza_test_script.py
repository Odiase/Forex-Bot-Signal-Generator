###### UPLOAD SECTION TEST

# import requests

# def upload_company_content_files(api_url, company_name, file_paths):
#     data = {
#         'company': company_name
#     }

#     files = []
#     for file_path in file_paths:
#         files.append(('file', open(file_path, 'rb')))
#         print("Past here")

#     try:
#         #POST request
#         response = requests.post(api_url, data=data, files=files)
#         print("send requests")
#         for _, file_obj in files:
#             file_obj.close()
#         print("closed files")

#         print(response.status_code)
#         if response.status_code == 201:
#             print('Upload successful:', response.json())
#         else:
#             print('Upload failed:', response.status_code, response.json())

#     except Exception as e:
#         print('An error occurred:', str(e))


# api_url = 'http://127.0.0.1:8000/products/company_content_file_upload'
# company_name = 'scompany__'
# file_paths = ['new.txt', 'new2.txt']

# upload_company_content_files(api_url, company_name, file_paths)


######### SUPLYCHAIN TEST
import requests

def send_data_to_endpoint(user):
    url = "https://tverza-supplychain.onrender.com/supplychain/get_user_store_transaction/efosa"
    
    response = requests.get(url)
    
    if response.status_code == 200:
        print('Data sent successfully!')
        print(response.json())
    else:
        print('Failed to send data. Status code:', response.status_code)

user = 'efosa'
send_data_to_endpoint(user)