import pickle

import numpy as np
from matplotlib import pyplot as plt
from sklearn import manifold
from sklearn.decomposition import PCA

matrix = np.array(pickle.load(open('matrix.p', 'rb')))
#tenses = np.array(pickle.load(open('tenses.p', 'rb')))

mds = manifold.MDS(n_components=2, dissimilarity='precomputed')
pos = mds.fit(matrix).embedding_

clf = PCA(n_components=2)
pos = clf.fit_transform(pos)

plt.figure(1)
plt.axes([0., 0., 1., 1.])
plt.scatter(pos[:, 0], pos[:, 1], s=20, c='g')
plt.show()
