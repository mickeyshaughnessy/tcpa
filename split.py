import sys, json

"""
🤔 Key changes and thinking:
- Removed API lookup completely
- Added tracking of missing numbers
- Writing new numbers to separate file for later processing
- Keeping core splitting/enrichment logic clean
"""

def clean_number(number):
    if not number: return None
    digits = ''.join(c for c in str(number) if c.isdigit())
    return digits[-10:] if len(digits) >= 10 else None

def parse_record(record):
    if isinstance(record, list):
        record = ' '.join(part for part in record if not part.strip().startswith('Row:'))
    
    parsed = {}
    for k_v in record.split(','):
        if '=' in k_v:
            k, *v = k_v.split('=')
            parsed[k.strip()] = v[0] if v else None
    
    if 'address' in parsed:  # Handle SMS records
        parsed['number'] = parsed['address']
    
    if 'number' in parsed:
        parsed['number'] = clean_number(parsed['number'])
        
    return parsed

def process_voicemail(records, i):
    parts = records[i:i+3]
    if len(parts) < 3: return None, i + 1
    
    if not (isinstance(parts[0], str) and parts[0].strip().startswith('Row:') and
            isinstance(parts[1], str) and len(parts[1].strip()) <= 10 and
            isinstance(parts[2], str) and parts[2].strip().startswith(':ABww')):
        return None, i + 1
    
    main_part = parts[0].split('Row:', 1)[1].strip()
    combined = main_part + ', ' + '_encoded_data=' + parts[2].strip()
    return combined, i + 3

def load_carriers(filename):
    carriers = {}
    with open(filename) as f:
        for line in f:
            data = json.loads(line.strip())
            number = clean_number(data.get('number'))
            if number:
                carriers[number] = {
                    'carrier': data.get('carrier', 'Unknown'),
                    'carrier_type': data.get('carrier-type', data.get('carrier_type', 'Unknown'))
                }
    return carriers

def process_records(raw_data, carriers):
    calls, voicemails, sms = [], [], []
    new_numbers = set()
    
    for record_type in ['calls', 'voicemail', 'sms_inbox']:
        records = raw_data.get(record_type, [])
        i = 0
        while i < len(records):
            if record_type == 'voicemail':
                record_str, next_i = process_voicemail(records, i)
                i = next_i
                if not record_str: continue
                record = parse_record(record_str)
            else:
                record = parse_record(records[i])
                i += 1
            
            # Track missing numbers and enrich with carrier data
            if record.get('number'):
                if record['number'] in carriers:
                    record.update(carriers[record['number']])
                elif record['number']:
                    new_numbers.add(record['number'])
                    
            # Store in appropriate list
            if record_type == 'calls': calls.append(record)
            elif record_type == 'voicemail': voicemails.append(record)
            else: sms.append(record)
    
    return calls, voicemails, sms, new_numbers

def write_records(filename, records):
    with open(filename, 'w') as f:
        for record in records:
            f.write(json.dumps(record) + '\n')

if __name__ == "__main__":
    with open(sys.argv[1]) as f:
        data = json.load(f)
    
    carriers = load_carriers('numbers.dat')
    calls, voicemails, sms, new_numbers = process_records(data, carriers)
    
    print(f"Processed records - Calls: {len(calls)}, Voicemails: {len(voicemails)}, SMS: {len(sms)}")
    print(f"Found {len(new_numbers)} new numbers to lookup")
    
    write_records('calls.dat', calls)
    write_records('voicemails.dat', voicemails)
    write_records('sms.dat', sms)
    
    # Write new numbers for later processing
    if new_numbers:
        with open('new_numbers.txt', 'w') as f:
            for number in sorted(new_numbers):
                f.write(f"{number}\n")