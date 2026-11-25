import os
from dotenv import load_dotenv
from litellm import completion

load_dotenv()
MODEL = os.getenv("LLM_MODEL")

BUDGET = ("I have GHS 1,200. I want 4 bags of rice at GHS 185 each and "
          "3 gallons of oil at GHS 95 each. How much will I have left?")
FACTUAL = ["What is the capital of the Bono East Region of Ghana?",
           "How many times has the Ghanian cedi currency been changed?"]


def ask(q):
    r = completion(model=MODEL, messages=[{"role": "user", "content": q}],
                   temperature=1)
    return r.choices[0].message.content


for i in range(3):
    print(f"--- Budget attempt {i+1} ---\n{ask(BUDGET)}\n")
for q in FACTUAL:
    print(f"--- {q} ---\n{ask(q)}\n")
