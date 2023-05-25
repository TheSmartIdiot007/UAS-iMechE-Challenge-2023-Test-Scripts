import numpy as np 
import matplotlib.pyplot as plt


F = 10
m = 2
x0= 0
u = 0
t = np.linspace(0,10,1000)
F = 10*t
a = F/m
v = []
x = []

for i in range(len(t)):
    v.append(u)
    u = u+a[i]*(t[1]-t[0])
print(v)

for i in range(len(t)):
    x.append(x0)
    x0 = x0 + v[i]*(t[1]-t[0])
print(x0)
plt.plot(t,x)
plt.show()
