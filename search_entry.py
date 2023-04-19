import datetime

start = False
while start == False:
    now = datetime.datetime.now()

    if now.minute % 5 == 0:
        start = True
print("start")