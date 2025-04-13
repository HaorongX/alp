import os

for i in ['s', 'w']:
    for j in ['21', '22', '23']:
        for k in ['11', '12', '13', '21', '22', '23', '31', '32', '33']:
            name = f"./9618{i}{j}_qp_{k}.pdf"
            os.system(f"python3 preprocessing.py {name}")
            os.system(f"python3 extractqp.py {name.replace('.pdf', '_processed.pdf')}")