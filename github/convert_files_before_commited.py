import base64

def convert_data(data):
    file_paths_and_contents = []
    for item in data:
        path = item['file_path']
        code = item['file_code']
        encoded_code = base64.b64encode(code.encode('utf-8')).decode('utf-8')
        file_paths_and_contents.append((path, encoded_code))
    return file_paths_and_contents


    
def convert_data_without_encoded(data):
    file_paths_and_contents = []
    for item in data:
        name = item['file_name']
        path = item['file_path']
        code = item['file_code']
        file_paths_and_contents.append({
            "file_name": name,
            "file_path": path,
            "file_code": code
        })
    return file_paths_and_contents



# def fetch_code_data(model, user_story, code_type):
#     try:
#         code_instance = model.objects.get(user_story=user_story)
#         code_data = getattr(code_instance, code_type, [])
#         return convert_data_without_encoded(code_data)
#     except model.DoesNotExist:
#         return None
    
    
    
def convert_package_data(data):
    file_paths_and_contents = []
    for item in data:
        path = item['file_path']
        code = item['file_code']
        file_paths_and_contents.append({
            "file_path": path,
            "file_code": code
        })
    return file_paths_and_contents


