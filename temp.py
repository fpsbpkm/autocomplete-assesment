l = [[[1,2,3], [5,6,7]]]

# iは[[1,2,3], [5,6,7]]になる
for i in l:
    for j in i:
        j[0] = 0

print(l)

