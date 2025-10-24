import pandas as pd
import os
from difflib import get_close_matches

class DiseaseToPrecautionModel:
    def __init__(self, dataset_path=None):
        """Initialize the model and load the precaution dataset."""
        if dataset_path is None:
            # Default path relative to project root
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            dataset_path = os.path.join(base_dir, 'dataset', 'Disease precaution.csv')
        
        self.df = pd.read_csv(dataset_path)
        self.diseases = self.df['Disease'].str.lower().tolist()
    
    def get_precautions(self, disease_query):
        """
        Get precautions for a given disease.
        
        Args:
            disease_query: Disease name (can be approximate)
            
        Returns:
            dict: {
                "disease": matched disease name,
                "precautions": list of precautions,
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
            row = matching_rows.iloc[0]
            precautions = []
            
            # Extract non-empty precautions
            for i in range(1, 5):
                col_name = f'Precaution_{i}'
                if col_name in row and pd.notna(row[col_name]) and row[col_name].strip():
                    precautions.append(row[col_name].strip())
            
            return {
                "disease": row['Disease'],
                "precautions": precautions,
                "found": True
            }
        
        # Disease not found
        return {
            "disease": disease_query,
            "precautions": [],
            "found": False
        }
    
    def get_all_diseases(self):
        """Return list of all diseases in the dataset."""
        return self.df['Disease'].tolist()
