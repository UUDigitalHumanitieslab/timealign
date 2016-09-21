import json
from collections import defaultdict
import pickle

import numpy as np
from matplotlib import pyplot as plt
from sklearn import manifold
from sklearn.decomposition import PCA

# TODO: This is test functionality and should eventually be deleted


def tenses2colors(ts):
    return ['b' if t == 'present perfect' else 'g' for t in ts]

matrix = np.array(pickle.load(open('matrix.p', 'rb')))
fragments = pickle.load(open('fragments.p', 'rb'))
tenses = pickle.load(open('tenses.p', 'rb'))

mds = manifold.MDS(n_components=5, dissimilarity='precomputed')
pos = mds.fit(matrix).embedding_

clf = PCA(n_components=5)
pos = clf.fit_transform(pos)

print clf.explained_variance_ratio_

plt.figure(1)
plt.axes([0., 0., 1., 1.])
plt.scatter(pos[:, 0], pos[:, 1], s=20, c='g')
plt.show()

language = 'en'

j = defaultdict(list)
for n, l in enumerate(pos.tolist()):
    j[tenses[language][n]].append({'x': l[0], 'y': l[1], 'fragment_id': fragments[n], 'tenses': [tenses[l][n] for l in tenses.keys()]})

js = []
for k, v in j.items():
    d = dict()
    d['key'] = k
    d['values'] = v
    js.append(d)

json.dump(js, open('matrix_{}.json'.format(language), 'wb'))
