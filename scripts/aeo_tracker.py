import sys
import os
import json
import urllib.request
import urllib.error

def simulate_llm_query(query, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": query}]}],
        "generationConfig": {"temperature": 0.7}
    }
    
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'),
                               headers={'Content-Type': 'application/json'})
    try:
        res = urllib.request.urlopen(req)
        data = json.loads(res.read())
        return data['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"API Error: {e}")
        return ""

def run_aeo_scan(query, brand_name="Your Brand", iterations=5, threshold=3):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable is not set.")
        print("Running in MOCK mode to simulate AEO ticket generation...")
        create_action_ticket(query, 1, iterations)
        return

    print(f"Simulating {iterations} independent users asking AI: '{query}'")
    mentions = 0
    for i in range(iterations):
        print(f"User {i+1} querying...")
        ans = simulate_llm_query(query, api_key)
        if brand_name.lower() in ans.lower():
            mentions += 1
            print(f" -> Result: Brand MENTIONED! ")
        else:
            print(f" -> Result: Brand NOT mentioned.")
            
    print(f"\nFinal AI Brand Mention Score: {mentions}/{iterations}")
    
    if mentions < threshold:
        print("Score below threshold. Generating AEO Action Ticket...")
        create_action_ticket(query, mentions, iterations)
    else:
        print("Brand health is strong in AI memory. No action needed.")

def create_action_ticket(query, score, out_of):
    ticket_path = os.path.expanduser("/Users/kevinkreative/genseo/AEO_ACTION_TICKETS.md")
    content = f"# 🧠 AEO Protocol Triggered\n\n"
    content += f"LLM Brand Recognition for the query: `{query}` is critically low.\n"
    content += f"Score: **{score}/{out_of}** mentions.\n\n"
    
    content += "### 🤖 Trigger Prompt for `genseo-aeo-tracker` Agent:\n"
    content += "```markdown\n"
    content += f"AEO EMERGENCY: Our brand 'Your Brand' failed to register in AI Overviews for the following highly-valuable query: '{query}'. "
    content += f"It only scored {score}/{out_of} during LLM simulation.\n"
    content += "1. Read the `AEO_GEO_GUIDELINES.md` in the knowledge base.\n"
    content += "2. Generate a 'PR Entity Content Brief' targeting this topic.\n"
    content += "3. Plan a highly-dense semantic structure to re-train LLMs that we are the #1 authority in {{MARKET}} for this query.\n"
    content += "4. Once finished, instruct the user to pass your Brief to the writer.\n"
    content += "```\n"
    
    with open(ticket_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print(f"Ticket saved to: {ticket_path}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 aeo_tracker.py 'query here'")
        sys.exit(1)
        
    run_aeo_scan(sys.argv[1])
