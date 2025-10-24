import pandas as pd
import os
from difflib import get_close_matches

class DiseaseToSymptomModel:
    def __init__(self, dataset_path=None):
        """Initialize the model and load the symptoms dataset."""
        if dataset_path is None:
            # Default path relative to project root
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            dataset_path = os.path.join(base_dir, 'dataset', 'DiseaseAndSymptoms.csv')
        
        self.df = pd.read_csv(dataset_path)
        self.diseases = self.df['Disease'].str.lower().unique().tolist()
    
    def get_symptoms(self, disease_query):
        """
        Get symptoms for a given disease.
        
        Args:
            disease_query: Disease name (can be approximate)
            
        Returns:
            dict: {
                "disease": matched disease name,
                "symptoms": list of symptoms,
                "found": boolean indicating if disease was found
            }
        """
        # Normalize input
        disease_query = disease_query.strip().lower()
        
        # Try exact match first
        matching_rows = self.df[self.df['Disease'].str.lower() == disease_query]
        
        # If no exact match, try fuzzy matching
        if matching_rows.empty:
            # Find closest matches
            close_matches = get_close_matches(disease_query, self.diseases, n=1, cutoff=0.6)
            if close_matches:
                disease_query = close_matches[0]
                matching_rows = self.df[self.df['Disease'].str.lower() == disease_query]
        
        if not matching_rows.empty:
            # Get all unique symptoms for this disease
            symptoms_set = set()
            
            for _, row in matching_rows.iterrows():
                for i in range(1, 18):  # Up to 17 symptoms
                    col_name = f'Symptom_{i}'
                    if col_name in row and pd.notna(row[col_name]):
                        symptom = str(row[col_name]).strip()
                        if symptom:
                            symptoms_set.add(symptom)
            
            disease_name = matching_rows.iloc[0]['Disease']
            
            return {
                "disease": disease_name,
                "symptoms": sorted(list(symptoms_set)),
                "found": True
            }
        
        # Disease not found
        return {
            "disease": disease_query,
            "symptoms": [],
            "found": False
        }
    
    def get_all_diseases(self):
        """Return list of all unique diseases in the dataset."""
        return self.df['Disease'].unique().tolist()
