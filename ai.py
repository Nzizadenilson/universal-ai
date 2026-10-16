from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

client = Groq(api_key=api_key)

SYSTEM_PROMPT = (
    "You are a quick-lookup assistant shown in a small overlay while the user"
    "watches or reads something. Answer in 1-2 sentences, max ~40 words"
    "Lead with the direct answer (e.g. 'Manchester is a city in England known"
    "for football and its industrial history.') if the user gives a single word"
    "or phrase, define it in the simplest way. No markdown, no lists, no preamble."
)

def ask_groq_response(question):
    #Yield the answer in small chunks as they arrive
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
        max_tokens=300, 
        temperature=0.3,         
        reasoning_effort="low",  
        stream=True,
        

    )
    for chunk in response:
        text = chunk.choices[0].delta.content
        if text:
            yield text

def ask_groq(question):
    #Non-streaming version kept for convenience
    return "".join(ask_groq_response(question))
