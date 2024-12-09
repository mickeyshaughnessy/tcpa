import random

if __name__ == "__main__":
    with open('sampled.txt', 'w') as fout:
        with open('raw_logs.txt', 'r') as f:
            for line in f:
                print(line)
                if random.random() < 0.01:
                    fout.write(line)
                line = line.split(',')
