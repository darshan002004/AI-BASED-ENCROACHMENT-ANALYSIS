import re

with open(r'C:\Users\Darshan B\.gemini\antigravity\scratch\encrowatch-ai\ENCROWATCH_AI_FINAL_RESEARCH_PAPER.md', encoding='utf-8') as f:
    text = f.read()

display_eqs = re.findall(r'\$\$(.*?)\$\$', text, re.DOTALL)
print(f'Total Display Equations: {len(display_eqs)}')
for idx, eq in enumerate(display_eqs):
    print(f'Eq {idx+1}: {eq.strip()[:100]}')
