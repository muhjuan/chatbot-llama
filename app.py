from flask import Flask, render_template, request, jsonify
import requests
import json
import os

app = Flask(__name__)

# Load server configurations from config.json
def load_config():
    try:
        with open('config.json') as config_file:
            config = json.load(config_file)
            return config
    except FileNotFoundError:
        raise FileNotFoundError("config.json file not found. Please make sure it exists.")
    except json.JSONDecodeError:
        raise ValueError("Error decoding the config.json file. Ensure it is valid JSON.")

# Load configurations
config = load_config()

# Ensure MISTRAL_SERVER_URL is available in config.json
MISTRAL_SERVER_URL = config.get('MISTRAL_SERVER_URL')
if not MISTRAL_SERVER_URL:
    raise ValueError("MISTRAL_SERVER_URL is not set in the config.json file.")

# Send message to Mistral hosted in GCP
def format_response(response_data):
    """
    Format the response for better readability.
    This will handle code blocks, nested structures, and regular text.
    """
    formatted_response = ""

    # Check if the response contains code blocks or nested content
    if isinstance(response_data, dict):
        # For nested dictionaries, format it nicely
        formatted_response += "<pre><code>" + json.dumps(response_data, indent=4) + "</code></pre>"
    elif isinstance(response_data, list):
        # For lists, format as a bulleted list
        formatted_response += "<ul>"
        for item in response_data:
            formatted_response += f"<li>{item}</li>"
        formatted_response += "</ul>"
    else:
        # Otherwise, return as simple text
        formatted_response = response_data

    return formatted_response

def send_message_to_mistral(prompt, model):
    """
    Send a message to the Mistral model hosted in GCP and return the response.
    """
    try:
        payload = {
            'model': model,  # Specify the model from the UI
            'prompt': prompt
        }
        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.post(MISTRAL_SERVER_URL, json=payload, headers=headers)
        
        if response.status_code == 200:
            json_objects = response.text.splitlines()
            full_response = ""
            for obj in json_objects:
                try:
                    data = json.loads(obj)
                    formatted_part = format_response(data.get('response', ''))
                    full_response += formatted_part
                except json.JSONDecodeError:
                    continue

            return full_response or "No response received from the Mistral model."
        else:
            return f"Error: Received status code {response.status_code}"

    except Exception as e:
        return f"Error occurred while connecting to Mistral: {str(e)}"

@app.route('/')
def index():
    return render_template('index-20240913.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.form['message']
    selected_model = request.form['model']
    mistral_response = send_message_to_mistral(user_message, selected_model)
    
    return jsonify({
        'user_message': user_message,
        'llama_response': mistral_response
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
