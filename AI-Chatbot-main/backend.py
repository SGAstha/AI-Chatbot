import requests 
# Imports the essential 'requests' library for making HTTP requests (required to talk to the Gemini API).
import json 
# Imports the 'json' library for handling JSON data (needed to prepare the API payload and parse the response).


import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY") 
# Stores the unique API key, required for authentication. (Placeholder value is currently shown).
MODEL_NAME = "gemini-1.5-flash" 
# Specifies the exact language model to be used for generating the diagnosis.
API_BASE_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent" 
# Constructs the complete base URL used for all API calls.
# -------------------------------------

def fetch_diagnosis(symptoms: list) -> dict: 
# Defines the main function that handles API communication; accepts a list of symptoms and returns a dictionary.
    """
    Connects to the Gemini API to fetch a simulated diagnosis based on symptoms.
    
    The system prompt is configured to force a single paragraph output.
    """
    
    # 1. Define the AI's role and instructions
    system_prompt = ( 
# Starts the definition of the strict instructions for the AI model.
        "You are a professional, non-medical triage AI. Based ONLY on the symptoms provided, " 
# Sets the AI's persona and limits its information source strictly to the provided symptoms.
        "provide a concise summary (3-4 sentences total) as a single paragraph covering the most likely common causes. " 
# Enforces the single paragraph output structure and content goal.
        "The final sentence must always be the mandatory disclaimer: 'Consult a healthcare professional for a real diagnosis.' " 
# Enforces the crucial safety disclaimer, which is mandatory in the output.
    )
    
    # 2. Construct the user's query
    user_prompt = f"Patient reported symptoms are: {', '.join(symptoms)}." 
# Formats the list of symptoms into a single, clean string for the AI's prompt.

    # 3. Construct the API payload
    payload = { 
# Starts the main payload dictionary request required by the Gemini API.
        "contents": [{"parts": [{"text": user_prompt}]}], 
# Inserts the user's formatted symptoms into the content structure.
        "systemInstruction": {"parts": [{"text": system_prompt}]} 
# Inserts the strict behavioral instructions for the model.
    } 
    
    # 4. API key is passed as a query parameter
    api_url_with_key = f"{API_BASE_URL}?key={API_KEY}" 
# Appends the secret API_KEY to the URL as a query parameter for authentication.
    
    headers = { 
# Defines the HTTP headers for the request.
        "Content-Type": "application/json", 
# Tells the server that the data being sent is in JSON format.
    }

    try: 
# Begins the try block for robust error handling of the network request.
        # Sends the request without unnecessary debugging prints or time delays
        response = requests.post(api_url_with_key, headers=headers, data=json.dumps(payload)) 
# Executes the POST request to the Gemini API, sending the payload as a JSON string.
        response.raise_for_status() 
# Checks the HTTP response status code; raises an exception (HTTPError) if the code is 4xx or 5xx.
        data = response.json() 
# Parses the successful JSON response body into a Python dictionary.
        return data 
# Returns the structured API response dictionary.

    except requests.exceptions.HTTPError as errh: 
# Catches specific errors related to bad HTTP status codes (e.g., invalid API key, rate limiting).
        return {"error": f"HTTP Error occurred: {errh}. Check if your API key is valid."} 
# Returns a structured error message detailing the HTTP issue.
    except requests.exceptions.RequestException as err: 
# Catches any other generalized error that occurred during the request (e.g., network timeout, connection refusal).
        return {"error": f"An unexpected error occurred: {err}"} 
# Returns a generalized error message.