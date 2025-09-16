#!python3

x = [1,10,88,2,5,50,15]
print('my numbers:', x)

xlen = len(x)
swapped = True

while swapped:
  swapped = False
  i = 0
  while i < xlen - 1:
    print('compare>>' + 'A:', x[i], 'B:', x[i+1])
    if x[i] > x[i+1]:
        x[i], x[i+1] = x[i+1],x[i]
        swapped = True
        print('swapped - true')
    i = i + 1

print('sorted:', x)
