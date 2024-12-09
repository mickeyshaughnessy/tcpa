import subprocess, json, time
from datetime import datetime, timedelta

def run_query(uri, description=""):
    cmd = [
        'adb', 
        'shell', 
        'content', 
        'query', 
        '--uri', 
        uri
    ]
    try:
        output = subprocess.check_output(cmd).decode()
        return [line for line in output.split('\n') if line.strip()]
    except subprocess.CalledProcessError as e:
        if "Could not find provider" in str(e.output):
            print(f"Provider not available for {description}")
        else:
            print(f"Error querying {description}: {e.output.decode() if e.output else str(e)}")
        return []

def try_get_voicemail():
    # Try different known voicemail URIs
    voicemail_uris = [
        'content://voicemail/voicemail',
        'content://com.android.voicemail/voicemail',
        'content://com.android.providers.voicemail/voicemail'
    ]
    
    for uri in voicemail_uris:
        print(f"Trying voicemail URI: {uri}")
        results = run_query(uri, "voicemail")
        if results:
            return results
    return []

def get_all_records():
    # Calculate timestamp for 3 years ago
    three_years_ago = int((datetime.now() - timedelta(days=3*365)).timestamp() * 1000)
    
    # Get calls
    print("Getting calls...")
    calls = run_query('content://call_log/calls', "calls")
    
    # Get voicemails
    print("\nGetting voicemail...")
    voicemails = try_get_voicemail()
    
    # Get SMS
    print("\nGetting SMS inbox...")
    sms_inbox = run_query('content://sms/inbox', "SMS inbox")
    
    print("Getting SMS sent...")
    sms_sent = run_query('content://sms/sent', "SMS sent")
    
    return {
        'calls': calls,
        'voicemail': voicemails,
        'sms_inbox': sms_inbox,
        'sms_sent': sms_sent
    }

if __name__ == '__main__':
    print("Extracting phone records...")
    records = get_all_records()
    
    # Save all data to JSON
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'phone_records_{timestamp}.json'
    
    with open(filename, 'w') as f:
        json.dump(records, f, indent=2)
    
    # Print summary
    print("\nExtraction complete!")
    for record_type, data in records.items():
        count = len(data) if data else 0
        print(f"{record_type}: {count} records")
    
    print(f"\nData saved to {filename}")
    
    # Print example records if available
    for record_type, data in records.items():
        if data:
            print(f"\nExample {record_type} record:")
            print(data[0])