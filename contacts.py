import subprocess, json, time
from datetime import datetime

"""
🤔 Enhanced data capture strategy:
- Store ALL fields returned by the content provider
- Keep display simple with just name/number
- Store raw field format to help debug content provider responses
- Use set to track which numbers we've seen to avoid duplicates
<query_formats>
The query results come back in formats like:
  display_name=John number=1234567890 custom_ringtone=/path/to/ring.mp3
  _id=42 lookup_key=3030j times_contacted=5 starred=0
We want to capture all of these fields while staying organized
</query_formats>
"""

def normalize_phone(number):
    return ''.join(filter(str.isdigit, number))

def run_query(uri, description=""):
    cmd = ['adb', 'shell', 'content', 'query', '--uri', uri]
    try:
        output = subprocess.check_output(cmd).decode()
        return [line for line in output.split('\n') if line.strip()]
    except subprocess.CalledProcessError as e:
        print(f"Error querying {description}: {e.output.decode() if e.output else str(e)}")
        return []

def get_contacts():
    contacts = {}
    seen_numbers = set()
    
    base_uris = [
        'content://com.android.contacts/contacts',
        'content://contacts/phones'
    ]
    
    for uri in base_uris:
        results = run_query(uri, f"contacts from {uri}")
        for result in results:
            # Store all fields
            fields = dict(item.split('=', 1) for item in result.split(' ') if '=' in item)
            
            # But require at least number for contact to be useful
            number = fields.get('number', '').strip('"')
            if not number:
                continue
                
            norm_number = normalize_phone(number)
            if norm_number in seen_numbers:
                # Merge any new fields with existing record
                contacts[norm_number].update(fields)
                continue
                
            seen_numbers.add(norm_number)
            
            # Store everything but organize critical fields at top level
            contacts[norm_number] = {
                'name': fields.get('display_name', '').strip('"'),
                'raw_number': number,
                'normalized_number': norm_number,
                'raw_data': fields  # Store all fields
            }
    
    return contacts

if __name__ == '__main__':
    print("Extracting contacts...")
    contacts = get_contacts()
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'contacts_{timestamp}.json'
    
    with open(filename, 'w') as f:
        json.dump(contacts, f, indent=2)
    
    print(f"\nExtracted {len(contacts)} contacts")
    print(f"Data saved to {filename}")
    
    if contacts:
        print("\nExample contact (name/number only):")
        sample_number = next(iter(contacts))
        contact = contacts[sample_number]
        print(json.dumps({
            'name': contact['name'],
            'number': contact['raw_number']
        }, indent=2))
        
        print("\nAvailable fields in raw_data:")
        print(list(contacts[sample_number]['raw_data'].keys()))