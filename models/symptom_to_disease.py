import pandas as pd
import os
from collections import defaultdict

class SymptomToDiseaseModel:
    def __init__(self, dataset_path=None):
        """Initialize the model and load the symptoms dataset."""
        if dataset_path is None:
            # Default path relative to project root
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            dataset_path = os.path.join(base_dir, 'dataset', 'DiseaseAndSymptoms.csv')
        
        self.df = pd.read_csv(dataset_path)
        self._build_symptom_index()
    
    def _build_symptom_index(self):
        """Build an index mapping symptoms to diseases for faster lookup."""
        self.symptom_to_diseases = defaultdict(set)
        
        for _, row in self.df.iterrows():
            disease = row['Disease']
            for i in range(1, 18):  # Up to 17 symptoms
                col_name = f'Symptom_{i}'
                if col_name in row and pd.notna(row[col_name]):
                    symptom = str(row[col_name]).strip().lower()
                    if symptom:
                        self.symptom_to_diseases[symptom].add(disease)
    
    def predict_disease(self, symptoms):
        """
        Predict possible diseases based on given symptoms.
        
        Args:
            symptoms: List of symptom strings
            
        Returns:
            dict: {
                "diseases": list of top matching diseases,
                "match_scores": dict mapping disease to number of matching symptoms,
                "input_symptoms": list of normalized input symptoms
            }
        """
        # Normalize input symptoms
        normalized_symptoms = [s.strip().lower().replace(' ', '_') for s in symptoms]
        
        # Count matching diseases
        disease_scores = defaultdict(int)
        
        for symptom in normalized_symptoms:
            # Try direct match first
            if symptom in self.symptom_to_diseases:
                for disease in self.symptom_to_diseases[symptom]:
                    disease_scores[disease] += 1
            else:
                # Try fuzzy matching (contains)
                for indexed_symptom, diseases in self.symptom_to_diseases.items():
                    if symptom in indexed_symptom or indexed_symptom in symptom:
                        for disease in diseases:
                            disease_scores[disease] += 0.5  # Lower weight for fuzzy match
        
        # Sort diseases by score
        sorted_diseases = sorted(disease_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Get top diseases (at least 3, or all with positive score)
        top_diseases = []
        scores = {}
        
        for disease, score in sorted_diseases[:min(5, len(sorted_diseases))]:
            if score > 0:
                top_diseases.append(disease)
                scores[disease] = score
        
        # If no matches found, return some common diseases as fallback
        if not top_diseases:
            common_diseases = self.df['Disease'].value_counts().head(3).index.tolist()
            top_diseases = common_diseases
            scores = {d: 0 for d in common_diseases}
        
        return {
            "diseases": top_diseases,
            "match_scores": scores,
            "input_symptoms": normalized_symptoms
        }
    
    def get_all_symptoms(self):
        """Return list of all unique symptoms in the dataset."""
        return sorted(list(self.symptom_to_diseases.keys()))
