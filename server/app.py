import os,io, requests
from flask import Flask, jsonify, request, send_from_directory
from translator import translate_csv
from s3 import AWSS3

MEDIA_DIR = "../media"
aws_access_key_id = os.environ['AWS_ACCESS_KEY_ID']
aws_secret_access_key = os.environ['AWS_SECRET_ACCESS_KEY']
region_name = "ap-south-1"
bucket_name = "translated-files-from-heroku"
aws_s3 = AWSS3(aws_access_key_id, aws_secret_access_key, region_name)

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({ "status" : "success" }),200

@app.route('/translate',methods=["POST","GET"])
def api_upload():
    '''
    Author: Madhur Jodhwani
    Date of creation: 08/08/2022
    Date of last modification: 10/08/2022
    Function name: api_upload
    Description: Processes the request from client - Reads headers and data - Uploads it's data to the s3 bucket
    Input: None
    Output: None
    '''
    file_name = request.headers.get('file_name')
    request.files['file'].save(f'{file_name}')
    file_size = os.path.getsize(f'{file_name}')
    aws_s3.push_data_to_s3_bucket(bucket_name,open(file_name,'rb'),file_name,file_size,"text/csv")
    os.remove(file_name)
    return jsonify({ "status" : "success" }),200


@app.route('/download-translated-csv',methods=["POST","GET"])
def api_call_translate():
    '''
    Author: Madhur Jodhwani
    Date of creation: 08/08/2022
    Date of last modification: 10/08/2022
    Function name: api_call_translate
    Description: Processes the request from client - Reads the headers and data - Downloads the data from the s3 bucket - reads it and translates it -  converts it back to CSV
    Input: None
    Output: None
    '''
    file_name = request.headers.get("file_name")
    language = request.headers.get("language")
    if not file_name:
        return jsonify({ "status" : "error" }),400
    else:
        #read the s3 bucket file here and translate it
        if(aws_s3.check_if_file_exists(bucket_name,file_name) == True):
            if aws_s3.download_file_from_s3_bucket(bucket_name,file_name) == False:
                return jsonify({ "status" : "error" }),503
            translated_data = translate_csv(f"./{file_name}",language)
            translated_data.to_csv(f"{language}_{file_name}",index=False)
            aws_s3.push_data_to_s3_bucket(bucket_name,open(f"{language}_{file_name}",'rb'),f"{language}_{file_name}",os.path.getsize(f"{language}_{file_name}"),"text/csv")
            return send_from_directory("./",f"{language}_{file_name}",as_attachment=True),200
        return jsonify({ "status" : f"ERROR:{file_name} is not present in the database, please use the /translate api to reupload it." }),503


@app.route('/download-previously-translated-csv',methods=["POST","GET"])
def api_call_download_previously_translated():
    '''
    Author: Madhur Jodhwani
    Date of creation: 08/08/2022
    Date of last modification: 10/08/2022
    Function name: api_call_download_previously_translated
    Description: Processes the request from client - Reads the headers and data - Downloads the data from the s3 bucket - reads it and returns it.
                    If already translated file not present then calls api_call_translate().
    Input: None
    Output: None
    '''
    file_name = request.headers.get("file_name")
    language = request.headers.get("language")
    if not file_name:
        return jsonify({ "status" : "error" })
    else:
        #read the s3 bucket file here and translate it
        if(aws_s3.check_if_file_exists(bucket_name,f"{language}_{file_name}") == True):
            aws_s3.download_file_from_s3_bucket(bucket_name,f"{language}_{file_name}")
            return send_from_directory("./",f"{language}_{file_name}",as_attachment=True),200
        else:
            api_call_translate()