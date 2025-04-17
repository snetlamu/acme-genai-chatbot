import gradio as gr
import boto3
import json
import base64

# AWS Bedrock client setup
bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')

def chat_with_ai(text_input, image_input):
     # Process text_input and image_input with Bedrock
     content = []

     image_b64 = None

     with open(image_input, "rb") as image_file:
          image_b64 = base64.b64encode(image_file.read())

     if text_input:
          content.append({"type": "text", "text": text_input})

     if image_input:
          content.append({"type": "image", "source": {"type": "base64","media_type": "image/jpeg", "data": image_b64.decode("utf-8") }})
     kwargs = {
          "modelId": "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
          "contentType": "application/json",
          "accept": "application/json",
          "body": json.dumps({
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
          })
          }
     response = bedrock_client.invoke_model(**kwargs)
     body = response['body'].read().decode("utf-8")
     response_text = json.loads(body)['content'][0]['text']
     response_image = None
     return response_text

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

app.launch(server_name="0.0.0.0", server_port=80, show_api=False, ssl_keyfile="key.pem", ssl_certfile="cert.crt", ssl_verify=False)