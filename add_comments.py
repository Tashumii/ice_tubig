import os
import re

def generate_two_words(func_name):
    name = func_name.strip('_')
    if not name or name == 'init':
        return "Initializes object"
    
    parts = name.split('_')
    if len(parts) >= 2:
        # e.g., get_all_announcements -> Gets announcements
        # format: Capitalized first word (make it a verb if possible, we'll just add 's' to common verbs)
        verb = parts[0].capitalize()
        if verb.lower() in ('get', 'fetch', 'create', 'update', 'delete', 'add', 'remove', 'set', 'check', 'load', 'refresh'):
            if not verb.endswith('s'):
                if verb.lower() == 'refresh':
                    verb += 'es'
                else:
                    verb += 's'
        noun = parts[-1]
        return f"{verb} {noun}"
    else:
        # e.g. refresh -> Refreshes data
        verb = parts[0].capitalize()
        if verb.lower() in ('get', 'fetch', 'create', 'update', 'delete', 'add', 'remove', 'set', 'check', 'load', 'refresh'):
            if not verb.endswith('s'):
                if verb.lower() == 'refresh':
                    verb += 'es'
                else:
                    verb += 's'
        return f"{verb} data"

def process_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    lines = content.split('\n')
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)
        # Match def function_name(...):
        match = re.match(r'^(\s*)def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', line)
        if match:
            indent = match.group(1)
            func_name = match.group(2)
            
            # Handle multi-line defs
            j = i
            def_str = line
            while j < len(lines) and not re.search(r':\s*(#.*)?$', lines[j]):
                j += 1
                if j < len(lines):
                    def_str += "\n" + lines[j]
                    new_lines.append(lines[j])
            i = j
            
            # Check if next line is already a comment
            next_line_idx = i + 1
            if next_line_idx < len(lines):
                next_line = lines[next_line_idx].strip()
                if not next_line.startswith('#'):
                    two_words = generate_two_words(func_name)
                    new_lines.append(f"{indent}    # {two_words}")
        i += 1
        
    with open(filepath, 'w') as f:
        f.write('\n'.join(new_lines))

for root, dirs, files in os.walk('.'):
    if '.venv' in root or '__pycache__' in root or '.git' in root:
        continue
    for file in files:
        if file.endswith('.py') and file != 'add_comments.py':
            process_file(os.path.join(root, file))

print("Done")
