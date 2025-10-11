import sys
import os
if __name__ == "__main__":
    os.system(f"python3 preprocessing.py {sys.argv[1]}")
    os.system(f"python3 extractqp.py {sys.argv[1].replace('.pdf', '_processed.pdf')}")
    alt = sys.argv[1].replace('qp', 'ms')
    os.system(f"python3 preprocessing_ms.py {alt}")
    os.system(f"python3 extractms.py {alt.replace('.pdf', '_processed.pdf')}")