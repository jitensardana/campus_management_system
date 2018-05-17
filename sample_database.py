import subprocess


def insert_sample_data():
    f = open('sample_data', 'r')

    i = 1
    for line in f:
        returned_value = subprocess.call(line, shell=True)
        print("Line number: "+str(i)+" Returned Value: "+str(returned_value)+"\n")
        i += 1

if __name__ == '__main__':
    insert_sample_data()
