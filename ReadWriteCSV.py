import csv
#-----------MII'S PROJECT
with open('Cleaned_Australian_Student_PerformanceData (ASPD24).csv', newline='', encoding='utf-8') as readfile:
    datareader=csv.reader(readfile)
    with open('outputDA.csv', 'w', newline='', encoding='utf-8') as writefile:
        datawriter= csv.writer(writefile)
        for row in datareader:
            datawriter.writerow(row)
