from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.llm_handler import GeminiLLMHandler
from models.symptom_to_disease import SymptomToDiseaseModel
from models.disease_to_precaution import DiseaseToPrecautionModel
from models.disease_to_symptom import DiseaseToSymptomModel

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize models (load once at startup)
print("Loading models...")
symptom_model = SymptomToDiseaseModel()
precaution_model = DiseaseToPrecautionModel()
symptom_lookup_model = DiseaseToSymptomModel()
llm_handler = GeminiLLMHandler()
print("Models loaded successfully!")

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "message": "Disease Query Processing Server is running"
    }), 200

@app.route('/query', methods=['POST'])
def query_endpoint():
    """
    Main endpoint to process user health queries.
    
    Expected JSON body:
    {
        "query": "I have fever and cough"
    }
    
    Returns:
    {
        "status": "success",
        "detected_task": "symptom_to_disease",
        "raw_output": {...},
        "response": "Natural language response"
    }
    """
    try:
        # Get user query from request
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                "status": "error",
                "message": "Missing 'query' field in request body"
            }), 400
        
        user_query = data['query'].strip()
        
        if not user_query:
            return jsonify({
                "status": "error",
                "message": "Query cannot be empty"
            }), 400
        
        # Step 1: Use LLM to analyze query and determine task type
        print(f"Analyzing query: {user_query}")
        analysis = llm_handler.analyze_query(user_query)
        task_type = analysis['task_type']
        extracted_info = analysis['extracted_info']
        
        print(f"Task type: {task_type}")
        print(f"Extracted info: {extracted_info}")
        
        # Step 2: Execute appropriate model based on task type
        raw_output = {}
        
        if task_type == 'symptom_to_disease':
            # Predict diseases from symptoms
            result = symptom_model.predict_disease(extracted_info)
            raw_output = {
                "top_diseases": result['diseases'][:3],
                "probabilities": result['probabilities'],
                "input_symptoms": result['input_symptoms']
            }
        
        elif task_type == 'disease_to_precaution':
            # Get precautions for disease
            # Extract disease name from query
            disease_name = ' '.join(extracted_info) if isinstance(extracted_info, list) else extracted_info
            result = precaution_model.get_precautions(disease_name)
            raw_output = {
                "disease": result['disease'],
                "precautions": result['precautions'],
                "found": result['found']
            }
        
        elif task_type == 'disease_to_symptom':
            # Get symptoms for disease
            disease_name = ' '.join(extracted_info) if isinstance(extracted_info, list) else extracted_info
            result = symptom_lookup_model.get_symptoms(disease_name)
            raw_output = {
                "disease": result['disease'],
                "symptoms": result['symptoms'],
                "found": result['found']
            }
        
        else:
            return jsonify({
                "status": "error",
                "message": f"Unknown task type: {task_type}"
            }), 400
        
        # Step 3: Use LLM to format response naturally
        print("Formatting response...")
        natural_response = llm_handler.format_response(task_type, raw_output, user_query)
        
        # Step 4: Return complete response
        return jsonify({
            "status": "success",
            "detected_task": task_type,
            "raw_output": raw_output,
            "response": natural_response
        }), 200
    
    except Exception as e:
        print(f"Error processing query: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            "status": "error",
            "message": f"Internal server error: {str(e)}"
        }), 500

@app.route('/diseases', methods=['GET'])
def get_diseases():
    """Get list of all available diseases."""
    try:
        diseases = precaution_model.get_all_diseases()
        return jsonify({
            "status": "success",
            "diseases": diseases,
            "count": len(diseases)
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/symptoms', methods=['GET'])
def get_symptoms():
    """Get list of all available symptoms."""
    try:
        symptoms = symptom_model.get_all_symptoms()
        return jsonify({
            "status": "success",
            "symptoms": symptoms[:100],  # Limit to first 100 for readability
            "total_count": len(symptoms)
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    # Check if GEMINI_API is set
    if not os.getenv('GEMINI_API'):
        print("\n⚠️  WARNING: GEMINI_API environment variable not set!")
        print("Set it using: export GEMINI_API='your-api-key'")
        print("Or the server will fail when processing queries.\n")
    
    # Run Flask app
    print("\n🚀 Starting Disease Query Processing Server...")
    print("📡 Server will be available at: http://127.0.0.1:5000")
    print("\nEndpoints:")
    print("  POST /query       - Process health queries")
    print("  GET  /health      - Health check")
    print("  GET  /diseases    - List all diseases")
    print("  GET  /symptoms    - List all symptoms")
    print("\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
