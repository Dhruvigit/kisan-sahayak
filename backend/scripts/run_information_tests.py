from backend.app.information.information_pipeline import handle_information_query
import time
from pathlib import Path
import os

TEST_QUERIES = [
    "What is PMFBY?",
    "What is the eligibility for PM-KISAN?",
    "Who is eligible for PMFBY?",
    "I am a government employee. Am I eligible for PM-KISAN?",
    "I earn some income from another job. Can I still get PM-KISAN?",
    "Who is NOT eligible for PM-KISAN?",
    "I am above 40 years old. Can I apply for PM-KMY?",
    "What are the benefits of PMFBY?",
    "What documents are required for KCC?",
    "How do I apply for PMFBY?",
    "Where should I apply for crop insurance?",
    "I made a mistake in my application. How can I correct it?",
    "What is the last date to apply for PMFBY?",
    "If I was rejected earlier, can I apply again?",
    "I applied but I did not receive any money. What could be the reason?",
    "Tell me about farmer schemes",
    "What is the capital of France?",
    "Can you explain how the crop insurance scheme works for farmers?",
    "Which scheme should I apply for and what is PMFBY?",
    "What is RWBCIS? What documents are required to apply?",
    "There was a flood in my area and my crop got damaged. What should I do?",
    "Heavy rain destroyed my crops, is there any government help?",
    "There is no water for farming in my village. What can farmers do?",
    "I am not earning much from farming. What can I do?",
    "I need money for farming but banks are not helping. What should I do?",
    "Is there any government help if crops fail?",
    "My crop failed. Will government give me money?",
    "My crop failed and I don't know which scheme can help me",
    "I heard government gives money to farmers every year. Is it true?",
    "I am old now. Is there any support for farmers after 60?"
]

results = []

for q in TEST_QUERIES:
    response = handle_information_query(q)
    results.append({
        "query": q,
        "mode": response.get("mode"),
        "scheme_code": response.get("scheme_code"),
        "intent": response.get("intent"),
        "answer": response.get("answer")
    })

    time.sleep(40)  # To avoid rate limiting or overloading the system

# 1. Define the full path where you want to save the file
output_file = Path("backend/scripts/information_test_results_3.txt")
# 2. (Optional but Safe) Create the folder if it doesn't exist yet
output_file.parent.mkdir(parents=True, exist_ok=True)

with open(output_file, "w", encoding="utf-8") as f:
    for r in results:
        f.write(f"QUERY: {r['query']}\n")
        f.write(f"MODE: {r['mode']}\n")
        f.write(f"SCHEME: {r['scheme_code']}\n")
        f.write(f"INTENT: {r['intent']}\n")
        f.write("ANSWER:\n")
        f.write(str(r["answer"] or "No Answer Generated") + "\n")
        f.write("=" * 80 + "\n\n")

print("✅ Test results saved to information_test_results.txt")
