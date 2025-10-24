import pandas as pd
import numpy as np
import os
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import BernoulliNB
from sklearn.metrics import accuracy_score

class SymptomToDiseaseModel:
    def __init__(self, dataset_path=None):
        """Initialize the model and load the symptoms dataset."""
        if dataset_path is None:
            # Default path relative to project root
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            dataset_path = os.path.join(base_dir, 'dataset', 'DiseaseAndSymptoms.csv')
        
        self.df = pd.read_csv(dataset_path)
        self._prepare_data()
        self._train_model()
    
    def _prepare_data(self):
        """Prepare data by extracting symptoms and building vocabulary."""
        # Get all symptom columns
        symptom_cols = [col for col in self.df.columns if "Symptom" in col]
        
        # Fill NaN with empty string
        self.df[symptom_cols] = self.df[symptom_cols].fillna('')
        
        # Clean and normalize symptoms
        for col in symptom_cols:
            self.df[col] = self.df[col].apply(lambda x: str(x).strip().lower().replace(' ', '_') if x else '')
        
        # Combine all symptom columns into a list per row
        self.df['Symptoms'] = self.df[symptom_cols].values.tolist()
        
        # Build symptom vocabulary
        self.all_symptoms = sorted(set(s for sublist in self.df['Symptoms'] for s in sublist if s != ''))
        print(f"Loaded {len(self.all_symptoms)} unique symptoms and {len(self.df['Disease'].unique())} diseases")
    
    def _symptoms_to_vector(self, symptoms):
        """Convert symptoms list to binary vector."""
        vector = np.zeros(len(self.all_symptoms))
        for s in symptoms:
            s_normalized = str(s).strip().lower().replace(' ', '_')
            if s_normalized in self.all_symptoms:
                vector[self.all_symptoms.index(s_normalized)] = 1
        return vector
    
    def _train_model(self):
        """Train the Naive Bayes classifier."""
        # Prepare features (X) and labels (y)
        X = np.array([self._symptoms_to_vector(s) for s in self.df['Symptoms']])
        y = self.df['Disease']
        
        # Split data for training and testing
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Train Bernoulli Naive Bayes model
        self.model = BernoulliNB()
        self.model.fit(X_train, y_train)
        
        # Evaluate model
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        print(f"Model trained with accuracy: {round(accuracy * 100, 2)}%")
    
    def predict_disease(self, symptoms, top_n=5):
        """
        Predict possible diseases based on given symptoms using Naive Bayes.
        
        Args:
            symptoms: List of symptom strings
            top_n: Number of top predictions to return (default: 5)
            
        Returns:
            dict: {
                "diseases": list of top matching diseases,
                "probabilities": dict mapping disease to probability (as percentage),
                "input_symptoms": list of normalized input symptoms
            }
        """
        # Normalize input symptoms
        normalized_symptoms = [s.strip().lower().replace(' ', '_') for s in symptoms]
        
        # Convert to vector
        input_vector = self._symptoms_to_vector(normalized_symptoms)
        
        # Get probabilities from model
        probs = self.model.predict_proba([input_vector])[0]
        disease_probs = dict(zip(self.model.classes_, probs))
        
        # Sort by probability descending
        sorted_probs = sorted(disease_probs.items(), key=lambda x: x[1], reverse=True)
        
        # Get top N diseases
        top_diseases = [disease for disease, _ in sorted_probs[:top_n]]
        top_probabilities = {disease: round(prob * 100, 2) for disease, prob in sorted_probs[:top_n]}
        
        return {
            "diseases": top_diseases,
            "probabilities": top_probabilities,
            "input_symptoms": normalized_symptoms
        }
    
    def get_all_symptoms(self):
        """Return list of all unique symptoms in the dataset."""
        return self.all_symptoms
    
    def get_model_accuracy(self):
        """Return model accuracy on test set."""
        X = np.array([self._symptoms_to_vector(s) for s in self.df['Symptoms']])
        y = self.df['Disease']
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        y_pred = self.model.predict(X_test)
        return round(accuracy_score(y_test, y_pred) * 100, 2)
