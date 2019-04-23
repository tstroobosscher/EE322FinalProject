import numpy as np
import math

f = open("tommy1.csv", "r")

mat = np.loadtxt(f, delimiter=",")

set_1_avg = float()
set_2_avg = float()
set_3_avg = float()

for index in range(0, 10):
  set_1_avg += (math.cos(math.pi / 180 * abs(mat[index, 0] - mat[index, 1])) + 1)/2
  set_2_avg += (math.cos(math.pi / 180 * abs(mat[index, 2] - mat[index, 3])) + 1)/2
  set_3_avg += (math.cos(math.pi / 180 * abs(mat[index, 4] - mat[index, 5])) + 1)/2

set_1_avg *= 10
set_2_avg *= 10
set_3_avg *= 10

print "Set 1 Average: {0:.2f}%".format(set_1_avg)
print "Set 2 Average: {0:.2f}%".format(set_2_avg)
print "Set 3 Average: {0:.2f}%".format(set_3_avg)

