import gradio as gr
import json
import base64
import boto3
import hmac
import hashlib
import requests
import traceback
import datetime
import os

proxyUrl = os.environ['AIDEF_PROXY_URL'] 
model = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
method = 'POST'
service = 'bedrock'
region = 'us-east-1'
host = 'bedrock-runtime.us-east-1.amazonaws.com'
api_endpoint = f"{proxyUrl}/model/{model}/invoke"
 
def sign(key, msg):
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()
 
def get_signature_key(key, date_stamp, region_name, service_name):
    k_date = sign(('AWS4' + key).encode('utf-8'), date_stamp)
    k_region = sign(k_date, region_name)
    k_service = sign(k_region, service_name)
    k_signing = sign(k_service, 'aws4_request')
    return k_signing
 
def create_signed_request(payload):
    t = datetime.datetime.now(datetime.UTC)
    amz_date = t.strftime('%Y%m%dT%H%M%SZ')
    date_stamp = t.strftime('%Y%m%d')
 
    session = boto3.Session()
    credentials = session.get_credentials()
    access_key = credentials.access_key
    secret_key = credentials.secret_key
    session_token = credentials.token
    canonical_uri = f"/model/{model}/invoke"
    canonical_querystring = ''
    canonical_headers = f'host:{host}\n' + f'x-amz-date:{amz_date}\n'
    signed_headers = 'host;x-amz-date'
 
    if session_token:
        canonical_headers += f'x-amz-security-token:{session_token}\n'
        signed_headers += ';x-amz-security-token'
 
    payload_hash = hashlib.sha256(payload.encode('utf-8')).hexdigest()
    canonical_request = f'{method}\n{canonical_uri}\n{canonical_querystring}\n{canonical_headers}\n{signed_headers}\n{payload_hash}'
 
    algorithm = 'AWS4-HMAC-SHA256'
    credential_scope = f'{date_stamp}/{region}/{service}/aws4_request'
    string_to_sign = f'{algorithm}\n{amz_date}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()}'
 
    signing_key = get_signature_key(secret_key, date_stamp, region, service)
    signature = hmac.new(signing_key, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()
 
    authorization_header = f'{algorithm} Credential={access_key}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}'
    headers = {
        'x-amz-date': amz_date,
        'Authorization': authorization_header
    }
 
    if session_token:
        headers['x-amz-security-token'] = session_token

    print("headers:", headers) 
    response = requests.request(method, api_endpoint, headers=headers, data=payload)
    print("response" , response)
    return response
 
def process_response(response):
    if True:
        event_stream = response.iter_lines()
        response_content = bytes([0])
        for data in event_stream:
            response_content += data
        return response_content
    else:
        try:
            response_content = response
        except json.JSONDecodeError:
            response_content = response
        return response_content

def chat_with_ai(text_input, image_input):
     # Process text_input and image_input with Bedrock
     content = []

     image_b64 = None

     if image_input:
          with open(image_input, "rb") as image_file:
               image_b64 = base64.b64encode(image_file.read())

     if text_input:
          content.append({"type": "text", "text": text_input})

     if image_input:
          content.append({"type": "image", "source": {"type": "base64","media_type": "image/jpeg", "data": image_b64.decode("utf-8") }})

     response = create_signed_request(json.dumps({
          "anthropic_version": "bedrock-2023-05-31",
          "max_tokens": 200,
          "top_k": 250,
          "stop_sequences": [],
          "temperature": 1,
          "top_p": 0.999,
          "messages": [
               {
                    "role": "user",
                    "content": content
               }
          ]
     }))
     return process_response(response)

# Gradio app setup
with gr.Blocks(title="ACME GenAI ChatBot") as app:
     gr.Markdown("<div style='font-weight: bold; font-size: 2em' align='center'>ACME GenAI ChatBot (Approved for Internal Enterprise Use)</div>")
     
     with gr.Column():
                text_input = gr.Textbox(label="Prompt", placeholder="Enter your message here...")
                image_input = gr.Image(label="Image Input", type="filepath")
                submit_button = gr.Button("Submit")
                text_output = gr.Textbox(label="Response", interactive=False)
     
     submit_button.click(
          chat_with_ai,
          inputs=[text_input, image_input],
          outputs=[text_output]
     )

app.launch(server_name="0.0.0.0", server_port=443, show_api=False, ssl_keyfile="./key.pem", ssl_certfile="./certn.cer", ssl_verify=False)
