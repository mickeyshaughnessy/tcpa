import requests, sys, json, random
import config
from collections import Counter

numbers = {}
_counter = Counter()

if __name__ == "__main__":
    with open('numbers.dat') as fin:
        for line in fin:
            line = json.loads(line.rstrip())
            number = line.get('number')
            numbers[number] = line

    with open('numbers.dat', 'a') as fout:
        with open(sys.argv[1]) as f:
            for line in f:
                line = line.rstrip()
                if not numbers.get(line):
                    res = requests.get('http://www.carrierlookup.com/api/lookup?key=%s&number=%s' % (config.CL_key, line))
                    res = res.json()
                    res = res.get('Response')
                    record = {'carrier_type': res.get('carrier_type'), 'carrier' : res.get('carrier'), 'number' : line}
                    numbers[line] = record
                    fout.write(json.dumps(record)+'\n') 
                    _counter[record.get('carrier')] += 1
                    if random.random() < 0.1: print(_counter)
                else:
                    print('skipped %s' % line)
    print(_counter)
