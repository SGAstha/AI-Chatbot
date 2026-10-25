import json
# Imports the standard Python JSON library for data serialization and deserialization.
import re
# Imports the regular expression for validation).
from flask import Flask, request, jsonify
# Imports necessary components from the Flask framework:
# Flask: The main class to create the web application.
# request: Object to handle incoming HTTP requests (POST data, headers, etc.).
# jsonify: Helper function to serialize Python objects (like dicts) into JSON responses.

from backend import fetch_diagnosis 
# Imports the core AI interaction function from a separate file (backend.py),
# which contains the logic for calling the Gemini API.

app = Flask(__name__)
# Initializes the Flask application instance. '__name__' helps Flask locate resources.

# Global cache for storing diagnosis history (symptom_key: {analysis: str, source: str})
symptom_history = {} 
# stores all successful diagnoses

# --- Helper Function for Input Validation ---
def is_medical_symptom(text: str) -> bool:
    """
    Performs a very basic check to determine if the input is likely a medical symptom/description
    or a general question. Returns False if it detects common non-symptom question keywords.
    """
    # List of common keywords that indicate a general knowledge query, not a medical symptom.
    non_symptom_keywords = [
        "what is", "how many", "tell me about", "define", 
        "who is", "where is", "when is", "joke", "weather", 
        "capital", "time", "date", "hello","bye"
    ]
    
    text = text.lower()
    # Convert the input text to lowercase for case-insensitive matching.
    
    # Check for short, exact matches (e.g., if the user types just "hello").
    if len(text.split()) < 2 and text in non_symptom_keywords:
        return False
        
    # Check if the input starts with any non-symptom keyword.
    for keyword in non_symptom_keywords:
        if text.startswith(keyword):
            return False
            
    # If none of the non-symptom checks fail, assume the input is valid.
    return True

# --- 1. Root Route: Serves the combined HTML/JS Frontend ---
@app.route('/')
# Flask decorator that registers the index() function to handle requests to the root URL ('/').
def index():
    """Serves the main combined HTML page (the user interface)."""
    try:
        # Opens the frontend HTML file for reading.
        with open('frontend.html', 'r', encoding='utf-8') as f:
            # Reads the entire content of the HTML file.
            return f.read()
            # Returns the HTML content to the client (browser).
    except FileNotFoundError:
        # Handles the error if the HTML file cannot be found.
        return "Error: frontend.html not found. Please ensure the file is in the root directory.", 404
        # Returns a 404 HTTP status code.

# --- 2. Diagnosis Route: Handles API/Cache Lookups ---
@app.route('/diagnose', methods=['POST'])
# Registers the diagnose() function to handle POST requests to the '/diagnose' endpoint.
def diagnose():
    """
    Receives symptom request, checks cache, and calls Gemini API if necessary.
    """
    if not request.is_json:
        # Checks if the request body is valid JSON (required by the frontend).
        return jsonify({"error": "Missing JSON in request"}), 400
        # Returns a 400 Bad Request error if not JSON.

    data = request.get_json()
    # Extracts the JSON data from the request body into a Python dictionary.
    symptoms = data.get('symptoms', []) # Expects a list, e.g., ["fever and sore throat"]
    # Retrieves the 'symptoms' key from the JSON data, defaulting to an empty list.

    # Basic validation: check if symptoms is a non-empty list containing at least one item.
    if not symptoms or not isinstance(symptoms, list) or not symptoms[0]:
        return jsonify({"error": "No valid symptoms provided."}), 400
    
    # We use the first (and only) item in the list as the history key
    query_key = symptoms[0].strip().lower()
    # Normalizes the symptom string (removes whitespace, converts to lowercase) for use as a cache key.

    # Input Validation Check
    if not is_medical_symptom(query_key):
        # Calls the helper function to check if the query is a general knowledge question.
        non_medical_response = f"I am a non-medical triage chatbot, and '{query_key}' is not a medical symptom or health-related query. Please ask about symptoms."
        # Creates a friendly, non-medical refusal message.
        # Return a 200 OK with the error message so the frontend displays it cleanly as an AI reply
        return jsonify({
            "diagnosis": non_medical_response,
            "source": "Validation"
        }), 200 # Returns 200 OK status to ensure the frontend processes it successfully.

    # Cache Lookup
    if query_key in symptom_history:
        # Checks if the normalized query key exists in the global cache.
        print(f"Cache Hit for: {query_key}")
        cached_data = symptom_history[query_key]
        # Retrieves the cached analysis and source.
        return jsonify({
            "diagnosis": cached_data['analysis'],
            "source": "History Cache"
        }), 200
        # Returns the cached result immediately with status 200.
        
    # API Call (Cache Miss)
    print(f"Cache Miss. Calling API for: {query_key}")
    
    # We pass the full symptom list to the core API function
    diagnosis_result = fetch_diagnosis(symptoms)
    # Calls the external function that interacts with the Gemini API.

    if "error" in diagnosis_result:
        # Checks if the API interaction returned a known error (e.g., network, authentication).
        return jsonify({"error": diagnosis_result["error"]}), 500
        # Returns a 500 Internal Server Error status.
    else:
        # If the API call succeeded, process the result.
        # Extract the generated text
        try:
            # Safely navigates the nested JSON structure returned by the Gemini API.
            generated_text = diagnosis_result['candidates'][0]['content']['parts'][0]['text']
            
            # Save to history cache
            symptom_history[query_key] = {
                "analysis": generated_text,
                "source": "API"
            }
            # Stores the newly generated diagnosis in the global cache for future use.
            
            # Return new diagnosis
            return jsonify({
                "diagnosis": generated_text,
                "source": "API"
            }), 200
            # Returns the new diagnosis result to the frontend.
            
        except (KeyError, IndexError):
            # Catches errors if the API response structure is unexpected or incomplete.
            return jsonify({"error": "API response structure was unexpected."}), 500
            # Returns a 500 Internal Server Error.

# --- 3. History Retrieval Route ---
@app.route('/history', methods=['GET'])
# Registers the get_history() function to handle GET requests to the '/history' endpoint.
def get_history():
    """Returns the entire symptom history cache."""
    # Return the global cache dictionary as JSON
    return jsonify(symptom_history), 200
    # Returns the entire global history dictionary serialized as JSON.

# --- 4. History Deletion Route ---
@app.route('/delete-history', methods=['POST'])
# Registers the delete_history() function to handle POST requests to the '/delete-history' endpoint.
def delete_history():
    """Handles deletion of either a specific history key or the entire cache."""
    global symptom_history
    # Declares intent to modify the global symptom_history dictionary.
    
    data = request.get_json()
    symptom_key = data.get('symptomKey')
    # Retrieves the 'symptomKey' from the request body (optional).

    if symptom_key:
        # This branch handles the deletion of a specific entry.
        # Delete specific item
        if symptom_key in symptom_history:
            del symptom_history[symptom_key]
            # Removes the entry from the dictionary using the key.
            print(f"Deleted history key: {symptom_key}")
            return jsonify({"message": f"Entry '{symptom_key}' deleted"}), 200
        else:
            return jsonify({"error": "Key not found"}), 404
            # Returns 404 Not Found if the key doesn't exist.
    else:
        # This branch handles the deletion of ALL history (when symptom_key is missing).
        # Delete all history (when payload is empty or doesn't contain symptomKey)
        symptom_history = {}
        # Re-initializes the global dictionary to an empty state, clearing all data.
        print("History cache has been cleared (ALL).")
        return jsonify({"message": "All history successfully cleared"}), 200
        #200 is http code for successful deletion
if __name__ == '__main__':
    # Standard Python entry point to run the script.
    print("🌍 Starting Flask server...")
    print("Open your browser to: http://127.0.0.1:5000/")
    # If the symptom_checker.py file has an error (e.g., API_KEY is missing), it will show up here.
    app.run(debug=True)
    # Starts the Flask development server on the default host and port (localhost:5000).
    # debug=True enables debugging features (auto-reload, detailed error messages).