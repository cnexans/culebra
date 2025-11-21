data = open("./aoc/2024/1/input.txt", "r").read().split("\n")

left, right = [], []
for line in data:
    left.append(int(line.split("   ")[0]))
    right.append(int(line.split("   ")[1]))

left.sort()
right.sort()

dist = 0
for i in range(len(left)):
    dist += abs(left[i] - right[i])

print(dist)