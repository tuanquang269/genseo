import re

with open('/Users/kevinkreative/genseo/2ndRound_120_tickets.md', 'r') as f:
    content = f.read()

def get_ticket(text, t_num):
    match = re.search(r'(### 📝 Ticket #' + str(t_num) + r' - .*?\n```markdown\n.*?\n```\n)', text, re.DOTALL)
    return match.group(1) if match else None

t3 = get_ticket(content, 3)
t4 = get_ticket(content, 4)
t5 = get_ticket(content, 5)

t40 = get_ticket(content, 40)
t63 = get_ticket(content, 63)
t47 = get_ticket(content, 47)

def swap(text, numA, textA, numB, textB):
    new_textA = textA.replace(f"Ticket #{numA}", f"Ticket #{numB}")
    new_textB = textB.replace(f"Ticket #{numB}", f"Ticket #{numA}")
    
    text = text.replace(textA, "|||PLACEHOLDER_A|||")
    text = text.replace(textB, "|||PLACEHOLDER_B|||")
    
    text = text.replace("|||PLACEHOLDER_A|||", new_textB)
    text = text.replace("|||PLACEHOLDER_B|||", new_textA)
    return text

if t3 and t40: content = swap(content, 3, t3, 40, t40)
if t4 and t63: content = swap(content, 4, t4, 63, t63)
if t5 and t47: content = swap(content, 5, t5, 47, t47)

with open('/Users/kevinkreative/genseo/2ndRound_120_tickets.md', 'w') as f:
    f.write(content)
print("Swapped 3<->40, 4<->63, 5<->47")
