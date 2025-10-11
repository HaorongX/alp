import os

for i in ['s', 'w']:
    for j in ['21', '22', '23', '24']:
        for k in ['11', '12', '13', '21', '22', '23', '31', '32', '33']:
            name = f"./9618_{i}{j}_ms_{k}"
            try:
                if len(os.listdir(name)) != len(os.listdir(name.replace("ms", "qp"))):
                    if len(os.listdir(name)) == 0:
                        print("empty", name)
                    else:
                        print(name, len(os.listdir(name.replace("ms", "qp"))) - len(os.listdir(name)))
            except FileNotFoundError:
                continue