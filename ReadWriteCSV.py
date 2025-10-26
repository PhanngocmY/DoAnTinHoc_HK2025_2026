import csv
# -----------MII'S PROJECT
def readWrite():
    with open('Cleaned_Australian_Student_PerformanceData (ASPD24).csv', newline='', encoding='utf-8') as readfile:
        datareader = csv.reader(readfile)
        with open('test.csv', 'w', newline='', encoding='utf-8') as writefile:
            datawriter = csv.writer(writefile)
            datawriter.writerows(datareader)
if __name__== "__main__":
    readWrite()
