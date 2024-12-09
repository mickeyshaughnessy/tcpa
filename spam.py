import json, sys
from collections import Counter

"""
🤔 Key design decisions:
- Loading contacts as a set of numbers for fast lookup
- Processing each record type separately due to different rules
- Keeping all enriched data in the output
- Using Counter for stats
"""

SPAM_CARRIERS = {
    "SINCH (FKA INTELIQUENT/NEUTRAL TANDEM)",
    "BANDWIDTH",
    "O1 COMMUNICATIONS",
    "TELNYX LLC",
    "VOIPSTREET, INC.",
    "FRACTEL, LLC",
    "LUMEN (FKA CENTURYLINK)"
}

def clean_number(number):
    if not number: return None
    digits = ''.join(c for c in str(number) if c.isdigit())
    return digits[-10:] if len(digits) >= 10 else None

def load_contacts(filename):
    """Load contacts and clean numbers"""
    contacts = set()
    with open(filename) as f:
        data = json.load(f)
        for number in data:
            clean = clean_number(number)
            if clean:
                contacts.add(clean)
    return contacts

def is_spam(record, contacts, record_type):
    number = record.get('number')
    if not number: return False
    
    # Specific allowed numbers
    if number == '7072668159':
        return False
    
    # 406 area code is never spam
    if number.startswith('406'):
        return False
    
    # SMS with name field = not spam (strong signal to keep)
    if record_type == 'sms' and record.get('name'):
        return False
    
    # Known spam carriers (case insensitive)
    carrier = str(record.get('carrier') or '').lower()
    if carrier and any(spam_carrier.lower() in carrier for spam_carrier in SPAM_CARRIERS):
        return True
    
    # Any VoIP or related carrier type
    carrier_type = str(record.get('carrier_type') or '').lower()
    if carrier_type and any(vtype in carrier_type for vtype in ['voip', 'wireless', 'mobil']):
        return True
    
    # Any number not in contacts is spam
    return number not in contacts

def process_file(infile, outfile, contacts, record_type):
    spam_records = []
    stats = Counter()
    number_counter = Counter()
    not_spam_reasons = Counter()
    sample_spam_records = []  # Keep a few samples
    area_codes = Counter()
    
    with open(infile) as f:
        for line in f:
            record = json.loads(line.strip())
            stats['total'] += 1
            
            # Track detailed spam/not-spam reasons
            carrier = str(record.get('carrier') or '').lower()
            carrier_type = str(record.get('carrier_type') or '').lower()
            number = record.get('number')
            
            # Track area codes
            if number and len(number) >= 3:
                area_codes[number[:3]] += 1
            
            if is_spam(record, contacts, record_type):
                spam_records.append(record)
                stats['spam'] += 1
                if number:
                    number_counter[number] += 1
                if carrier:
                    stats[f"spam_carrier_{carrier}"] += 1
                    
                # Track why it's spam
                if any(sc.lower() in carrier for sc in SPAM_CARRIERS):
                    stats['spam_known_carrier'] += 1
                elif any(vtype in carrier_type for vtype in ['voip', 'wireless', 'mobil']):
                    stats['spam_voip_type'] += 1
                else:
                    stats['spam_not_in_contacts'] += 1
                
                # Keep sample records (up to 3 of each type)
                if len(sample_spam_records) < 3:
                    sample_spam_records.append(record)
            else:
                stats['not_spam'] += 1
                # Track why it's not spam
                if number == '7072668159':
                    not_spam_reasons['allowed_number'] += 1
                elif number and number.startswith('406'):
                    not_spam_reasons['area_code_406'] += 1
                elif number in contacts:
                    not_spam_reasons['in_contacts'] += 1
                elif record_type == 'sms' and record.get('name'):
                    not_spam_reasons['sms_has_name'] += 1
    
    with open(outfile, 'w') as f:
        for record in spam_records:
            f.write(json.dumps(record) + '\n')
    
    return stats, number_counter, not_spam_reasons, sample_spam_records, area_codes

def format_record(record):
    """Format a record for display"""
    number = record.get('number', 'Unknown')
    carrier = record.get('carrier', 'Unknown')
    carrier_type = record.get('carrier_type', 'Unknown')
    duration = record.get('duration', 'N/A')
    name = record.get('name', 'N/A')
    
    return (f"\n    Number: {number}"
            f"\n    Carrier: {carrier}"
            f"\n    Type: {carrier_type}"
            f"\n    Duration: {duration}"
            f"\n    Name: {name}")

def print_spam_details(record_type, number, count, carriers):
    carrier_info = carriers.get(number, {})
    print(f"  {number}: {count} times - {carrier_info.get('carrier', 'Unknown')} "
          f"({carrier_info.get('carrier_type', 'Unknown')})")

if __name__ == "__main__":
    contacts = load_contacts('contacts.json')
    print(f"Loaded {len(contacts)} contacts")
    
    # Load carriers for detailed reporting
    carriers = {}
    with open('numbers.dat') as f:
        for line in f:
            data = json.loads(line.strip())
            carriers[data.get('number')] = data
    
    # Process each type
    for record_type in ['calls', 'voicemails', 'sms']:
        infile = f"{record_type}.dat"
        outfile = f"spam_{record_type}.dat"
        stats, number_counter, not_spam_reasons, sample_records, area_codes = process_file(
            infile, outfile, contacts, record_type)
        
        print(f"\n{'='*50}")
        print(f"{record_type.upper()} Analysis:")
        print(f"{'='*50}")
        print(f"Total records processed: {stats['total']}")
        
        # Spam stats
        print("\nSPAM STATISTICS:")
        print(f"Total spam records: {stats['spam']}")
        print(f"  - Known spam carriers: {stats.get('spam_known_carrier', 0)}")
        print(f"  - VoIP/Wireless/Mobile: {stats.get('spam_voip_type', 0)}")
        print(f"  - Not in contacts: {stats.get('spam_not_in_contacts', 0)}")
        
        # Non-spam stats
        print(f"\nNON-SPAM STATISTICS:")
        print(f"Total non-spam records: {stats['not_spam']}")
        for reason, count in not_spam_reasons.most_common():
            print(f"  - {reason}: {count}")
        
        # Area code stats
        print(f"\nTOP AREA CODES:")
        for area_code, count in area_codes.most_common(5):
            print(f"  {area_code}: {count} calls")
        
        # Top spammers
        print(f"\nTOP 10 SPAM {record_type.upper()} NUMBERS:")
        for num, count in number_counter.most_common(10):
            print_spam_details(record_type, num, count, carriers)
            
        # Sample records
        if sample_records:
            print(f"\nSAMPLE SPAM {record_type.upper()} RECORDS:")
            for i, record in enumerate(sample_records, 1):
                print(f"\nRecord {i}:{format_record(record)}")
