#!python

d = [44,2,5,66,33,232]
print('my list:', d)

dnums = len(d)
swapped = True

while swapped:
	swapped = False
	i = 0
	while i < dnums - 1:
		print('numA: %d numB: %d' % (d[i], d[i+1]))
		if d[i] > d[i+1]:
			tmp = d[i]
			d[i] = d[i+1]
			d[i+1] = tmp
			swapped = True
		print('tmp list', d)
		i = i + 1

print('sorted:', d) 
