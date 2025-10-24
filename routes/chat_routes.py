from flask import Blueprint, request, jsonify, g, current_app
from functools import wraps
from models.user import User
from models.memory import UserMemory
from utils.memory_utils import get_memory_prompt, update_memory_from_conversation
from datetime import datetime
import json

chat_bp = Blueprint('chat', __name__)

def get_llm_handler():
    # Helper to get the LLM handler from the app context
    return current_app.extensions.get('llm_handler')

def get_ml_models():
    # Helper to get ML models from the app context
    return {
        'symptom_model': current_app.extensions.get('symptom_model'),
        'precaution_model': current_app.extensions.get('precaution_model'),
        'symptom_lookup_model': current_app.extensions.get('symptom_lookup_model')
    }

@chat_bp.route('/chat', methods=['POST'])
def chat():
    """
    Handle chat messages with memory integration and ML model processing
    
    Expected JSON body:
    {
        "message": "User's message",
        "user_id": "user_id_from_token"
    }
    
    Returns:
    {
        "response": "AI's response",
        "status": "success",
        "context_updated": bool
    }
    """
    data = request.get_json()
    user_message = data.get('message', '').strip()
    user_id = data.get('user_id')
    
    if not user_message:
        return jsonify({"error": "Message is required", "status": "error"}), 400
    
    if not user_id:
        return jsonify({"error": "User ID is required", "status": "unauthorized"}), 401
    
    try:
        # Get the LLM handler and ML models
        llm_handler = get_llm_handler()
        models = get_ml_models()
        
        if not all([llm_handler, *models.values()]):
            raise Exception("Required services not initialized")
        
        # Get user's memory context
        memory_context = get_memory_prompt(user_id)
        
        # Step 1: Use LLM to analyze query with memory context
        analysis = llm_handler.analyze_query_with_context(user_message, memory_context)
        task_type = analysis['task_type']
        extracted_info = analysis['extracted_info']
        
        # Step 2: Execute appropriate model based on task type
        raw_output = {}
        
        if task_type == 'symptom_to_disease':
            result = models['symptom_model'].predict_disease(extracted_info)
            raw_output = {
                "top_diseases": result['diseases'][:3],
                "probabilities": result['probabilities'],
                "input_symptoms": result['input_symptoms']
            }
        
        elif task_type == 'disease_to_precaution':
            disease_name = ' '.join(extracted_info) if isinstance(extracted_info, list) else extracted_info
            result = models['precaution_model'].get_precautions(disease_name)
            raw_output = {
                "disease": result['disease'],
                "precautions": result['precautions'],
                "found": result['found']
            }
        
        elif task_type == 'disease_to_symptom':
            disease_name = ' '.join(extracted_info) if isinstance(extracted_info, list) else extracted_info
            result = models['symptom_lookup_model'].get_symptoms(disease_name)
            raw_output = {
                "disease": result['disease'],
                "symptoms": result['symptoms'],
                "found": result['found']
            }
        else:
            # For general conversation or unknown task types
            raw_output = {
                "task_type": task_type,
                "extracted_info": extracted_info,
                "is_general_conversation": True
            }
        
        # Step 3: Format response with context
        natural_response = llm_handler.format_response_with_context(
            task_type, 
            raw_output, 
            user_message,
            memory_context
        )
        
        # Step 4: Update memory based on the conversation
        memory_updated = update_memory_from_conversation(
            user_id, 
            user_message, 
            natural_response,
            raw_output
        )
        
        # Step 5: Return the response
        return jsonify({
            "response": natural_response,
            "status": "success",
            "context_updated": memory_updated,
            "task_type": task_type
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        return jsonify({
            "error": "An error occurred while processing your request",
            "status": "error"
        }), 500
