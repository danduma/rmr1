from litellm import completion
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

safety_settings = [
{
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_NONE",
        },
]

def get_llm_response(question, prompt):
    
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": question}
    ]
    
    response = completion( 
        model='gemini/gemini-2.0-flash-exp',
        messages=messages,
        stream=False,
        safety_settings=safety_settings
        )
    
    response_text = response.choices[0].message.content
    return response_text