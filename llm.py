from litellm import completion
import os
import json

current_dir = os.path.dirname(os.path.abspath(__file__))
default_location = os.path.join(current_dir, "vertexai-api-key.json")  
file_path = os.environ.get("VERTEXAI_API_KEY_PATH", default_location)


with open(file_path, 'r') as file:
    vertex_credentials = json.load(file)
    
os.environ["VERTEXAI_PROJECT"] = os.environ.get("VERTEXAI_PROJECT", "cognivita")
os.environ["VERTEXAI_LOCATION"] = os.environ.get("VERTEXAI_LOCATION", "us-central1")

def get_llm_response(question, prompt):
    
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": question}
    ]
    
    response = completion( 
        model='vertex_ai/gemini-1.5-pro-002',
        messages=messages,
        stream=False,
        vertex_credentials=vertex_credentials
        )
    
    response_text = response.choices[0].message.content
    return response_text