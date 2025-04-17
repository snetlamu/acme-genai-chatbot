```markdown
# ACME AI ChatBot

This application is a chat-based interface that uses AWS Bedrock for generating responses. The UI is built using Gradio and supports both text and image inputs, as well as text and image outputs. Additionally, the interface includes an option to clear the chat history.

## Features

- **Input**: Accepts both text and image inputs.
- **Output**: Generates both text and image outputs.
- **Clear Chat**: Provides a button to clear the entire chat history.

## Requirements

- Python 3.7 or higher
- Gradio
- AWS SDK for Python (Boto3)

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/snetlamu/ai-defense-ai-app.git
    cd ai-defense-ai-app
    ```

2. Install dependencies:
    ```bash
    pip install gradio==4.20.0 boto3==1.37.35 urllib3==1.25.4
    ```

3. Configure AWS credentials for Bedrock:
    ```bash
    aws configure
    ```

## Usage

Run the application:
```bash
python app.py
```