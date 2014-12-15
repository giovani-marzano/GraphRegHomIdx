import unittest
import silhouette

class PreCalculated(unittest.TestCase):

    def setUp(self):
        self.values = {
            1:[1], 5:[5],
            10:[10], 30:[30],
            40:[40], 45:[45]
        }
        # Clusterization[i] = ( clusters, expected silhouettes )
        self.clusterizations = [
            ({1:1, 5:1, 10:2, 30:2, 40:3, 45:3},
            {
                1:silhouette.calcCoeficiente(5-1, (10-1+30-1)/2.0),
                5:silhouette.calcCoeficiente(5-1, (10-5+30-5)/2.0),
                10:silhouette.calcCoeficiente(30-10, (10-1+10-5)/2.0),
                30:silhouette.calcCoeficiente(30-10, (40-30+45-30)/2.0),
                40:silhouette.calcCoeficiente(45-40, (40-10+40-30)/2.0),
                45:silhouette.calcCoeficiente(45-40, (45-10+45-30)/2.0),
            }),
            ({1:1, 5:2, 10:1, 30:2, 40:1, 45:2},
            {
                1:silhouette.calcCoeficiente((10-1+40-1)/2.0,
                      (5-1+30-1+45-1)/3.0),
                5:silhouette.calcCoeficiente((30-5+45-5)/2.0,
                    (5-1+10-5+40-5)/3.0),
                10:silhouette.calcCoeficiente((10-1+40-10)/2.0,
                    (10-5+30-10+45-10)/3.0),
                30:silhouette.calcCoeficiente((30-5+45-30)/2.0,
                    (30-1+30-10+40-30)/3.0),
                40:silhouette.calcCoeficiente((40-1+40-10)/2.0,
                    (40-5+40-30+45-40)/3.0),
                45:silhouette.calcCoeficiente((45-5+45-30)/2.0,
                    (45-1+45-10+45-40)/3.0),
            }),
        ]

        self.clustersSilh = []
        self.totalSilh = []
        for clusters, se in self.clusterizations:
            sc = {}
            countC = {}
            stot = 0.0
            ntot = 0
            for e, s in se.items():
                c = clusters[e]
                scAux = sc.get(c,0.0)
                sc[c] = scAux + s
                counAux = countC.get(c, 0)
                countC[c] = counAux + 1
                stot += s
                ntot += 1
            for c in sc.keys():
                sc[c] = sc[c]/countC[c]

            stot = stot/ntot

            self.clustersSilh.append(sc)
            self.totalSilh.append(stot)

    def test_evaluateClusters(self):
        for c12n, (clusters, expected) in enumerate(self.clusterizations):
            se, sc, st, nei = silhouette.evaluateClusters(self.values, clusters)

            for e, s in se.items():
                self.assertAlmostEqual(s, expected[e],
                msg="Silhoette for {} in clusterization {}".format(e,c12n))

            for c, s in sc.items():
                self.assertAlmostEqual(s, self.clustersSilh[c12n][c],
                msg="Cluster silh for {} in clusterization {}".format(c, c12n))

            self.assertAlmostEqual(st, self.totalSilh[c12n],
                msg="Total silh in clusterization {}".format(c12n))

class PreCalculated2(unittest.TestCase):

    def setUp(self):
        self.values = {
            1:[1], 5:[5],
            10:[10], 30:[30],
            40:[40], 45:[45]
        }
        # Clusterization[i] = ( clusters, expected silhouettes )
        self.clusterizations = [
            ({1:1, 5:1, 10:2, 30:2, 40:3, 45:3},
            {
                1:silhouette.calcCoeficiente((5-1)**2, ((10-1)**2+(30-1)**2)/2.0),
                5:silhouette.calcCoeficiente((5-1)**2, ((10-5)**2+(30-5)**2)/2.0),
                10:silhouette.calcCoeficiente((30-10)**2, ((10-1)**2+(10-5)**2)/2.0),
                30:silhouette.calcCoeficiente((30-10)**2, ((40-30)**2+(45-30)**2)/2.0),
                40:silhouette.calcCoeficiente((45-40)**2, ((40-10)**2+(40-30)**2)/2.0),
                45:silhouette.calcCoeficiente((45-40)**2, ((45-10)**2+(45-30)**2)/2.0),
            }),
            ({1:1, 5:2, 10:1, 30:2, 40:1, 45:2},
            {
                1:silhouette.calcCoeficiente(((10-1)**2+(40-1)**2)/2.0,
                      ((5-1)**2+(30-1)**2+(45-1)**2)/3.0),
                5:silhouette.calcCoeficiente(((30-5)**2+(45-5)**2)/2.0,
                    ((5-1)**2+(10-5)**2+(40-5)**2)/3.0),
                10:silhouette.calcCoeficiente(((10-1)**2+(40-10)**2)/2.0,
                    ((10-5)**2+(30-10)**2+(45-10)**2)/3.0),
                30:silhouette.calcCoeficiente(((30-5)**2+(45-30)**2)/2.0,
                    ((30-1)**2+(30-10)**2+(40-30)**2)/3.0),
                40:silhouette.calcCoeficiente(((40-1)**2+(40-10)**2)/2.0,
                    ((40-5)**2+(40-30)**2+(45-40)**2)/3.0),
                45:silhouette.calcCoeficiente(((45-5)**2+(45-30)**2)/2.0,
                    ((45-1)**2+(45-10)**2+(45-40)**2)/3.0),
            }),
        ]

        self.clustersSilh = []
        self.totalSilh = []
        for clusters, se in self.clusterizations:
            sc = {}
            countC = {}
            stot = 0.0
            ntot = 0
            for e, s in se.items():
                c = clusters[e]
                scAux = sc.get(c,0.0)
                sc[c] = scAux + s
                counAux = countC.get(c, 0)
                countC[c] = counAux + 1
                stot += s
                ntot += 1
            for c in sc.keys():
                sc[c] = sc[c]/countC[c]

            stot = stot/ntot

            self.clustersSilh.append(sc)
            self.totalSilh.append(stot)

    def test_evaluateClusters(self):
        for c12n, (clusters, expected) in enumerate(self.clusterizations):
            se, sc, st, nei = silhouette.evaluateClusters2(self.values, clusters)

            for e, s in se.items():
                self.assertAlmostEqual(s, expected[e],
                msg="Silhoette for {} in clusterization {}".format(e,c12n))

            for c, s in sc.items():
                self.assertAlmostEqual(s, self.clustersSilh[c12n][c],
                msg="Cluster silh for {} in clusterization {}".format(c, c12n))

            self.assertAlmostEqual(st, self.totalSilh[c12n],
                msg="Total silh in clusterization {}".format(c12n))

if __name__ == '__main__':
    unittest.main()
