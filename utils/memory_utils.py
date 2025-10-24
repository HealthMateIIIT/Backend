from models.memory import UserMemory
from datetime import datetime

def get_memory_prompt(user_id):
    """
    Format the user's memory into a prompt for the LLM
    Returns a string that can be included in the system prompt
    """
    memory = UserMemory(user_id).get_memory()
    
    prompt_parts = []
    
    # Add long-term memory
    if memory['long_term']:
        prompt_parts.append("Long-term medical context about the user:")
        for key, value in memory['long_term'].items():
            if value:  # Only include non-empty values
                # Convert key to more readable format (e.g., 'has_asthma' -> 'has asthma')
                readable_key = key.replace('_', ' ').replace('has ', '')
                prompt_parts.append(f"- User {readable_key}: {value}")
    
    # Add recent memories
    if memory['recent']:
        prompt_parts.append("\nRecent medical context:")
        for mem in memory['recent'][:5]:  # Only include most recent 5 memories
            prompt_parts.append(f"- {mem['text']} ({mem['type']})")
    
    return "\n".join(prompt_parts) if prompt_parts else ""

def update_memory_from_conversation(user_id, user_query, llm_response, raw_output=None):
    """
    Update user's memory based on the conversation and LLM analysis
    
    Args:
        user_id: The user's unique ID
        user_query: The user's message
        llm_response: The AI's response
        raw_output: Raw output from the ML models (optional)
        
    Returns:
        bool: True if memory was updated, False otherwise
    """
    memory = UserMemory(user_id)
    memory_updated = False
    
    try:
        # Add the conversation to recent memory
        memory.add_recent_memory(
            memory_text=f"User: {user_query}\nAssistant: {llm_response}",
            memory_type="conversation"
        )
        memory_updated = True
        
        # Update long-term memory based on the task type and content
        if raw_output and isinstance(raw_output, dict):
            task_type = raw_output.get('task_type')
            
            # Handle different task types
            if task_type == 'symptom_to_disease' and 'top_diseases' in raw_output:
                # If the model predicted diseases with high confidence, remember them
                diseases = raw_output.get('top_diseases', [])
                probabilities = raw_output.get('probabilities', [])
                
                # Only remember if we have high confidence predictions
                if diseases and probabilities and probabilities[0] > 0.7:  # 70% confidence threshold
                    memory.update_long_term({
                        'recent_disease_prediction': {
                            'diseases': diseases[:3],
                            'probabilities': [float(p) for p in probabilities[:3]],
                            'timestamp': datetime.utcnow().isoformat()
                        }
                    })
                    memory_updated = True
            
            elif task_type == 'disease_to_precaution' and 'disease' in raw_output:
                # Remember that the user was interested in precautions for a specific disease
                disease = raw_output.get('disease')
                if disease:
                    memory.update_long_term({
                        'last_discussed_disease': disease,
                        'last_discussion_type': 'precautions',
                        'last_discussion_time': datetime.utcnow().isoformat()
                    })
                    memory_updated = True
            
            elif task_type == 'disease_to_symptom' and 'disease' in raw_output:
                # Remember that the user was interested in symptoms of a specific disease
                disease = raw_output.get('disease')
                if disease:
                    memory.update_long_term({
                        'last_discussed_disease': disease,
                        'last_discussion_type': 'symptoms',
                        'last_discussion_time': datetime.utcnow().isoformat()
                    })
                    memory_updated = True
        
        # Extract and remember any mentioned medical conditions
        medical_terms = extract_medical_terms(f"{user_query} {llm_response}")
        if medical_terms:
            for term, term_type in medical_terms.items():
                if term_type == 'condition':
                    memory.update_long_term({
                        f'has_{term.lower().replace(" ", "_")}': True,
                        f'last_mentioned_{term.lower().replace(" ", "_")}': datetime.utcnow().isoformat()
                    })
                    memory_updated = True
        
        return memory_updated
        
    except Exception as e:
        print(f"Error updating memory: {str(e)}")
        return False

def extract_medical_terms(text):
    """
    Extract medical terms from text using simple pattern matching
    In a production environment, you might want to use a more sophisticated NLP approach
    """
    # This is a simplified example - expand this list as needed
    medical_conditions = [
        'asthma', 'diabetes', 'hypertension', 'high blood pressure', 'migraine',
        'allergy', 'allergies', 'arthritis', 'anxiety', 'depression', 'asthma',
        'cancer', 'cholesterol', 'heart disease', 'high cholesterol', 'obesity',
        'osteoporosis', 'stroke', 'thyroid', 'ulcer'
    ]
    
    found_terms = {}
    text_lower = text.lower()
    
    for condition in medical_conditions:
        if condition in text_lower:
            found_terms[condition] = 'condition'
    
    return found_terms
