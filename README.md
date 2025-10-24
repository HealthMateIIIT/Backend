# 🧠 Disease Query Processing Server

## 📋 Overview

This project implements a **Flask-based server** that takes **natural language health-related queries** (like “I have a headache and fever” or “What are the precautions for dengue?”) and returns **appropriate responses** such as predicted diseases, symptoms, or precautions.

The system acts as an **intelligent query-processing pipeline** where multiple internal models and datasets are coordinated by an **LLM (Google Gemini)** that decides:

* What kind of query the user has asked (symptom-based, disease-based, or precaution-based),
* Which internal model or function to invoke,
* How to interpret the model’s output,
* And finally, how to convert the raw output into a user-friendly natural language response.

---

## 🧩 Project Architecture

### 🔄 Flow

```
User Query → Flask API → Gemini LLM → Model Selector → Internal Model(s) → LLM Response Formatter → Output to User
```

### ⚙️ Step-by-Step Flow Description

1. **User Input (Frontend or API Call)**
   The user sends a text query to the Flask endpoint (e.g., `/query`).

2. **Query Processing (LLM Decision Layer)**
   The query is sent to **Gemini API**, which analyzes and decides:

   * What the user is asking (symptoms → disease, disease → precautions, etc.),
   * Which model or function to use,
   * What kind of output is expected.

3. **Model Execution Layer**
   Based on Gemini’s decision:

   * If the input is *symptoms*, a **Symptom-to-Disease model** is called.
   * If the input is *disease*, a **Disease-to-Precautions** or **Disease-to-Symptoms** model is used.

   These functions return mock/random outputs for now (to simulate model responses).

4. **Output Interpretation (LLM Again)**
   The LLM reformats the raw output into a **human-readable** explanation.

5. **Final Response (Flask)**
   The Flask server returns a JSON response back to the client.

---

## 📂 Directory Structure

```
project-root/
│
├── server.py                     # Main Flask application
├── requirements.txt           # Dependencies list
│
├── dataset/                   # Data folder
│   ├── Disease_precaution.csv # Disease → Precautions mapping
│   └── DiseaseAndSymptoms.csv # Disease → Symptoms mapping
│
├── models/                    # Placeholder for model logic
│   ├── disease_to_precaution.py
│   ├── disease_to_symptom.py
│   └── symptom_to_disease.py
│
├── utils/
│   └── llm_handler.py         # Handles Gemini API calls and reasoning
│
└── README.md                  # This documentation
```

---

## 🧠 Role of Gemini LLM

Gemini acts as the **intelligent brain** of the system.

It performs three major tasks:

1. **Intent Recognition**
   Understands what the user query means (e.g., “I have cough and fever” → user is describing symptoms).

2. **Routing Decision**
   Determines which internal model or dataset function to invoke.

3. **Response Formatting**
   Takes raw model output (like probabilities or lists) and generates a natural, human-friendly response.

You can access your Gemini API key in the system using:

```bash
echo $GEMINI_API
```

---

## 🧪 Example Query Scenarios

| User Query                             | Expected Task   | Model Used            | Output Example                                 |
| -------------------------------------- | --------------- | --------------------- | ---------------------------------------------- |
| “I have fever and cough”               | Predict disease | symptom_to_disease    | “You may have Flu, COVID, or Dengue.”          |
| “What are the precautions for dengue?” | Get precautions | disease_to_precaution | “Use mosquito nets, stay hydrated, rest well.” |
| “Tell me symptoms of malaria”          | Get symptoms    | disease_to_symptom    | “High fever, chills, sweating, and fatigue.”   |

---

## 🚀 API Endpoints

### `POST /query`

#### Description:

Takes user input query and returns an intelligent response.

#### Request:

```json
{
  "query": "I have headache and sore throat"
}
```

#### Response (Example):

```json
{
  "status": "success",
  "detected_task": "symptom_to_disease",
  "top_diseases": ["Common Cold", "Flu", "COVID-19"],
  "response": "Based on your symptoms, you might have Common Cold, Flu, or COVID-19. Please consult a doctor if symptoms persist."
}
```

---

## 🧰 Mock Implementations

For now, the model functions will **return random/predefined results** to simulate responses.
Later, you can replace these stubs with actual ML models.

Example:

```python
# models/symptom_to_disease.py
import random

def predict_disease(symptoms):
    diseases = ["Flu", "Common Cold", "Dengue", "Malaria", "COVID-19"]
    return random.sample(diseases, 3)
```

---

## 🧪 Running the Server

### 1️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

### 2️⃣ Set the Gemini API Key

```bash
export GEMINI_API="AIzaSyBo6CfSxrCxNqXmkqSvo8ignurOA0vitwQ"
```

### 3️⃣ Run Flask App

```bash
python server.py
```

### 4️⃣ Test using cURL or Postman

```bash
curl -X POST http://127.0.0.1:5000/query -H "Content-Type: application/json" -d '{"query": "I have cough and fever"}'
```

---

## 📘 Future Work

| Area                      | Description                                                        |
| ------------------------- | ------------------------------------------------------------------ |
| 🔍 Intent Classification  | Use Gemini to detect query type more accurately                    |
| 🤖 Model Integration      | Replace mock functions with trained models                         |
| 🧾 Response Summarization | Add LLM-based answer refinement                                    |
| 💬 Frontend UI            | Add a chat interface where users can talk or speak (voice-to-text) |
| 🧠 Context Memory         | Allow multi-turn conversations with contextual awareness           |

---