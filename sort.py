#!python3

y = [1,10,88,2,5,50]
print('my numbers:', y)

x = []
ylen = len(y)
i = 0
while ylen - 1 > i:
    x = y
    print('my list:', x)
    print('A:',x[i], 'B:', x[i+1])
    if x[i] < x[i+1]:
        x[i], x[i+1] = x[i+1],x[i]
    
    i = i + 1

print('sorted:', x)
