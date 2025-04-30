import gradio as gr
import json
import base64
import boto3
import os
import re
import time
import traceback

ai_defense_gateway_url = os.environ['AIDEF_PROXY_URL']

# Custom event hook to change URL before signing

def change_url_to_ai_defense_after_signing(**kwargs):
    new_url = re.sub(
        pattern=r"https:\/\/[^/]*",
        repl=ai_defense_gateway_url,
        string=kwargs["request"].url,
    )
    kwargs["request"].url = new_url

# Sends request to Bedrock

def send_prompt(payload):
    session = boto3.Session()
    bedrock_client = session.client(
        service_name="bedrock-runtime",
        region_name="us-east-1",
    )

    bedrock_client.meta.events.register(
        "before-send.bedrock-runtime.InvokeModel",
        change_url_to_ai_defense_after_signing
    )

    try:
        response = bedrock_client.invoke_model(**payload)
        return response
    except Exception as e:
        print(f"ERROR: Can't invoke model. Reason: {e}")
        traceback.print_exc()
        return None

# Processes the model response

def process_response(response):
    if not response:
        return "Error in model response."
    body = response['body'].read().decode("utf-8")
    response_text = json.loads(body)['content'][0]['text']
    return response_text

# Prepare message from user and send to model

def handle_user_input(history, message):
    content = []
    media_type = ""

    if message["text"]:
        content.append({"type": "text", "text": message["text"]})

    if message.get("files"):
        for filepath in message["files"]:
             with open(filepath, "rb") as file:
                file_b64 = base64.b64encode(file.read()).decode("utf-8")
                file_extension = os.path.splitext(filepath)[-1].lower()
                media_type = "image/jpeg" if file_extension == ".jpg" or file_extension == ".jpeg" else "unsupported"
                content.append({
                      "type": "image",
                      "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": file_b64
                      }
                })

    request_payload = {
        "modelId": "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        "contentType": "application/json",
        "accept": "application/json",
        "body": json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 5000,
            "top_k": 250,
            "stop_sequences": [],
            "temperature": 1,
            "top_p": 0.999,
            "messages": [{"role": "user", "content": content}]
        })
    }

    reply_text = "Unsupported file type. Please upload a JPEG image."
    if media_type != "unsupported":
          response = send_prompt(request_payload)
          reply_text = process_response(response)
    history.append({"role": "user", "content": message["text"]})
    history.append({"role": "assistant", "content": ""})

    for char in reply_text:
        history[-1]["content"] += char
        time.sleep(0.01)
        yield history
    
    return "", history

# UI setup

with gr.Blocks(title="ACME GenAI ChatBot") as app:
    heading = gr.Markdown("<div style='font-weight: bold; font-size: 2em' align='center'>ACME GenAI ChatBot</div><div  style='font-weight: bold; font-size: 1em' align='center'>[Approved for Internal Enterprise Use]</div>")

    chatbot = gr.Chatbot(elem_id="chatbot", bubble_full_width=False, type="messages")

    chat_input = gr.MultimodalTextbox(
        interactive=True,
        file_count="single",
        file_types=["image"],
        placeholder="Enter message or upload file...",
        show_label=False,
    )

    chat_msg = chat_input.submit(
        handle_user_input, [chatbot, chat_input], [chatbot]
    )

    chat_msg.then(lambda: gr.MultimodalTextbox(interactive=True, value=None), None, [chat_input])


if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=443, show_api=False, ssl_keyfile="./key.pem", ssl_certfile="./certn.cer", ssl_verify=False)
