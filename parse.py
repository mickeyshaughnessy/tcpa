import json, csv, sys
from collections import defaultdict, Counter

"""
🤔 Keeping it simple:
- Take filename from sys.argv[1]
- Parse content query format
- Count field occurrences 
- Write to CSVs
<flow>
input.json -> parse -> count -> output CSVs
</flow>
"""

def parse_line(line):
    return dict(p.split('=', 1) for p in line.split(',') if '=' in p)

def get_fields(records):
    fields = set()
    for record in records:
        fields.update(parse_line(record).keys())
    return sorted(list(fields))

def main():
    if len(sys.argv) != 2:
        print("Usage: python parse.py input.json")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        data = json.load(f)

    for record_type in ['calls', 'voicemail', 'sms_inbox', 'sms_sent']:
        if record_type not in data or not data[record_type]:
            continue
            
        records = data[record_type]
        fields = get_fields(records)
        parsed = [parse_line(r) for r in records]
        
        # Print stats
        print(f"\n{record_type}:")
        print(f"Total records: {len(records)}")
        
        counts = defaultdict(Counter)
        for record in parsed:
            for field, value in record.items():
                counts[field][value] += 1
                
        for field in fields:
            print(f"\n{field} (top 5):")
            for value, count in counts[field].most_common(5):
                print(f"  {value}: {count}")
        
        # Write CSV
        with open(f"{record_type}.csv", 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(parsed)
            print(f"\nWrote {len(parsed)} records to {record_type}.csv")

if __name__ == '__main__':
    main()