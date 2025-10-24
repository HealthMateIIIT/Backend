import os
import google.generativeai as genai
import json

class GeminiLLMHandler:
    def __init__(self):
        """Initialize Gemini API with API key from environment variable."""
        api_key = os.getenv("GEMINI_API")
        if not api_key:
            raise ValueError("GEMINI_API environment variable not set")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    def analyze_query(self, user_query):
        """
        Analyze user query to determine intent and extract relevant information.
        
        Returns:
            dict: {
                "task_type": "symptom_to_disease" | "disease_to_precaution" | "disease_to_symptom",
                "extracted_info": list of symptoms or disease name
            }
        """
        prompt = f"""
You are a medical query analyzer. Analyze the following user query and determine:
1. What type of query is this?
   - symptom_to_disease: User is describing symptoms and wants to know possible diseases
   - disease_to_precaution: User is asking about precautions for a specific disease
   - disease_to_symptom: User is asking about symptoms of a specific disease

2. Extract the relevant information:
   - If symptom_to_disease: Extract list of symptoms mentioned
   - If disease_to_precaution: Extract the disease name
   - If disease_to_symptom: Extract the disease name

User Query: "{user_query}"

Respond ONLY with a JSON object in this exact format:
{{
    "task_type": "symptom_to_disease or disease_to_precaution or disease_to_symptom",
    "extracted_info": ["list", "of", "symptoms or disease name"]
}}
"""
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean up response to extract JSON
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(response_text)
            return result
        except Exception as e:
            print(f"Error analyzing query: {e}")
            # Fallback to basic keyword matching
            return self._fallback_analysis(user_query)
    
    def _fallback_analysis(self, query):
        """Fallback method for query analysis if LLM fails."""
        query_lower = query.lower()
        
        # Check for precaution-related keywords
        if any(word in query_lower for word in ['precaution', 'prevent', 'avoid', 'care', 'safety', 'protect']):
            # Extract potential disease name (simple approach)
            disease_words = query.split()
            return {
                "task_type": "disease_to_precaution",
                "extracted_info": [query]
            }
        
        # Check for symptom-related keywords
        elif any(word in query_lower for word in ['symptom', 'symptoms', 'signs', 'indication']):
            return {
                "task_type": "disease_to_symptom",
                "extracted_info": [query]
            }
        
        # Default to symptom to disease (most common use case)
        else:
            # Extract potential symptoms
            symptoms = query.split(',') if ',' in query else query.split('and')
            symptoms = [s.strip() for s in symptoms]
            return {
                "task_type": "symptom_to_disease",
                "extracted_info": symptoms
            }
    
    def format_response(self, task_type, model_output, user_query):
        """
        Use LLM to format the raw model output into a natural language response.
        
        Args:
            task_type: Type of task performed
            model_output: Raw output from the model
            user_query: Original user query
            
        Returns:
            str: Natural language response
        """
        prompt = f"""
You are a helpful medical assistant. A user asked a health-related question and our system has processed it.

User Query: "{user_query}"

Task Type: {task_type}

System Output: {json.dumps(model_output)}

Please create a natural, empathetic, short, brief, and informative response for the user based on this information.
Guidelines:
- Be clear and very concise
- Use emojis if needed
- Use natural language
- Format the information in a readable way
- Be empathetic and supportive

Respond with ONLY the formatted message to the user (no JSON, no extra formatting).
"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error formatting response: {e}")
            return self._fallback_format(task_type, model_output)
    
    def _fallback_format(self, task_type, model_output):
        """Fallback method for response formatting if LLM fails."""
        print("Falling Back because of no LLM response")
        if task_type == "symptom_to_disease":
            diseases = model_output.get('diseases', [])
            return f"Based on the symptoms you described, you might have: {', '.join(diseases)}. Please consult a doctor for proper diagnosis."
        
        elif task_type == "disease_to_precaution":
            precautions = model_output.get('precautions', [])
            return f"Here are some precautions: {', '.join(precautions)}. Always follow your doctor's advice."
        
        elif task_type == "disease_to_symptom":
            symptoms = model_output.get('symptoms', [])
            return f"Common symptoms include: {', '.join(symptoms)}. If you experience these, please consult a healthcare professional."
        
        return "I'm not sure how to respond to that. Please try rephrasing your question."

    def analyze_query_with_context(self, user_query, memory_context):
        """
        Analyze user query with memory context to determine intent and extract relevant information.
        
        Args:
            user_query: The user's message
            memory_context: The user's memory context from the database
            
        Returns:
            dict: {
                "task_type": str,
                "extracted_info": list,
                "requires_memory_update": bool
            }
        """
        prompt = f"""
You are a medical query analyzer with access to the user's health context.

User's Health Context:
{memory_context}

Analyze the following user query and determine:
1. What type of query is this? (symptom_to_disease, disease_to_precaution, disease_to_symptom, or general_health)
2. Extract relevant information (symptoms, disease names, etc.)
3. Determine if this information should be remembered in the user's health context

User Query: "{user_query}"

Respond ONLY with a JSON object in this exact format:
{{
    "task_type": "symptom_to_disease or disease_to_precaution or disease_to_symptom or general_health",
    "extracted_info": ["list", "of", "symptoms or disease name"],
    "requires_memory_update": true/false,
    "memory_update_type": "long_term" or "recent" or "none"
}}"""
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean up response to extract JSON
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].strip()
            
            # Parse the JSON response
            result = json.loads(response_text)
            
            # Set default values if keys are missing
            result.setdefault('requires_memory_update', False)
            result.setdefault('memory_update_type', 'none')
            
            return result
            
        except Exception as e:
            print(f"Error in analyze_query_with_context: {str(e)}")
            return {
                "task_type": "general_health",
                "extracted_info": [],
                "requires_memory_update": False,
                "memory_update_type": "none"
            }
    
    def format_response_with_context(self, task_type, data, user_query, memory_context):
        """
        Format the model's output into a natural language response with memory context.
        
        Args:
            task_type: The type of task (symptom_to_disease, disease_to_precaution, disease_to_symptom, general_health)
            data: The raw output from the model
            user_query: The original user query
            memory_context: The user's memory context
            
        Returns:
            str: Natural language response
        """
        # Create a prompt that includes the memory context
        prompt = f"""
You are a helpful and empathetic health assistant. Use the following context about the user to provide personalized responses.

User's Health Context:
{memory_context}

Current Query: "{user_query}"

Task Type: {task_type}

Model Output:
{json.dumps(data, indent=2)}

Please provide a helpful, empathetic response that:
1. Acknowledges the user's query
2. Uses the provided context to personalize the response
3. Presents the information in a clear, easy-to-understand way
4. Includes relevant health advice or next steps
5. Is supportive and non-alarming
6. Add Emojis to make engaging
7. Donot give markdown format output. give html format output.

Response:"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error in format_response_with_context: {str(e)}")
            # Fallback to basic formatting if there's an error
            return self._format_basic_response(task_type, data, user_query)
    
    def _format_basic_response(self, task_type, data, user_query):
        """Fallback response formatter if the context-aware formatter fails"""
        if task_type == 'symptom_to_disease':
            diseases = data.get('top_diseases', [])
            probabilities = data.get('probabilities', [])
            symptoms = data.get('input_symptoms', [])
            
            if not diseases:
                return "I couldn't find any diseases matching those symptoms. Could you provide more details?"
                
            response = ["Based on your symptoms:"]
            for symptom in symptoms:
                response.append(f"- {symptom}")
                
            response.append("\nThe most likely conditions are:")
            for disease, prob in zip(diseases, probabilities):
                response.append(f"- {disease} ({(prob * 100):.1f}%)")
                
            response.append("\nPlease consult with a healthcare professional for an accurate diagnosis.")
            return "\n".join(response)
            
        elif task_type == 'disease_to_precaution':
            if not data.get('found', False):
                return f"I couldn't find information about precautions for '{data.get('disease', 'this condition')}'. Could you check the disease name and try again?"
                
            response = [f"Precautions for {data['disease']}:"]
            for i, precaution in enumerate(data.get('precautions', []), 1):
                response.append(f"{i}. {precaution}")
                
            response.append("\nRemember to consult with a healthcare provider for personalized advice.")
            return "\n".join(response)
            
        elif task_type == 'disease_to_symptom':
            if not data.get('found', False):
                return f"I couldn't find information about symptoms of '{data.get('disease', 'this condition')}'. Could you check the disease name and try again?"
                
            response = [f"Common symptoms of {data['disease']} include:"]
            for symptom in data.get('symptoms', []):
                response.append(f"- {symptom}")
                
            response.append("\nNote: Not everyone will experience all these symptoms, and some people may have additional symptoms not listed here.")
            return "\n".join(response)
            
        return "I've processed your health query. Please consult with a healthcare professional for personalized advice."
