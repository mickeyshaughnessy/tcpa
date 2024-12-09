import sys, json

if __name__ == "__main__":
    with open(sys.argv[1], 'r') as f:
        d = json.load(f)
    calls, voicemails, sms = d.get('calls'), d.get('voicemails'), d.get('sms_inbox')
    
    for call in calls:
        print(call.split(','))
        _c = {c.split('=')[0]:c.split('=')[1] for c in call.split(',')}
        
        print(_c.keys())
        #input()

    for vm in voicemails:
        print(type(vm))
