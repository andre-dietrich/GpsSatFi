import pickle
import numpy as np
import matplotlib.pyplot as plt

results = pickle.load( open( "results.p", "rb" ) )
height = range(0, 150)

for i in range(0, len(results)):
  hist, _ = np.histogram(results[i], height, normed=True)
  res = np.cumsum(hist)
  if i<5:
    plt.plot(res, label='DOP='+str(i+2))
  else:
    plt.plot(res)

plt.legend(shadow=True, fancybox=True, loc=2)
plt.ylabel('Probability')
plt.xlabel('Height to guaranty a specific DOP level')
plt.text(80,0.5,'<- Direction of increasing DOP')
plt.show()

print 'Aus Maus'