#!/usr/bin/env python
#
# Author: Qiming Sun <osirpt.sun@gmail.com>
#

import unittest
import numpy
from pyscf import lib
from pyscf.pbc import gto
from pyscf.pbc import scf
from pyscf.pbc import df
from pyscf.pbc import dft
from pyscf.pbc import tools
from pyscf.pbc.x2c import sfx2c1e

cell = gto.Cell()
cell.build(unit = 'B',
           a = numpy.eye(3)*4,
           mesh = [11]*3,
           atom = 'H 0 0 0; H 0 0 1.8',
           verbose = 0,
           basis='sto3g')

class light_speed(object):
    def __init__(self, c):
        self.bak = lib.param.LIGHT_SPEED
        self.c = c
    def __enter__(self):
        lib.param.LIGHT_SPEED = self.c
        return self.c
    def __exit__(self, type, value, traceback):
        lib.param.LIGHT_SPEED = self.bak

class KnownValues(unittest.TestCase):
    def test_hf(self):
        with light_speed(2) as c:
            mf = scf.RHF(cell).sfx2c1e()
            mf.with_df = df.PWDF(cell)
            dm = mf.get_init_guess()
            h1 = mf.get_hcore()
            self.assertAlmostEqual(numpy.einsum('ij,ji', dm, h1), -0.47578184212352159+0j, 9)
            kpts = cell.make_kpts([3,1,1])
            h1 = mf.get_hcore(kpt=kpts[1])
            self.assertAlmostEqual(numpy.einsum('ij,ji', dm, h1), -0.09637799091491725+0j, 9)

    def test_khf(self):
        with light_speed(2) as c:
            mf = scf.KRHF(cell).sfx2c1e()
            mf.with_df = df.PWDF(cell)
            mf.kpts = cell.make_kpts([3,1,1])
            dm = mf.get_init_guess()
            h1 = mf.get_hcore()
            self.assertAlmostEqual(numpy.einsum('ij,ji', dm[0], h1[0]),-0.47578184212352159+0j, 9)
            self.assertAlmostEqual(numpy.einsum('ij,ji', dm[1], h1[1]),-0.09637799091491725+0j, 9)
            self.assertAlmostEqual(numpy.einsum('ij,ji', dm[2], h1[2]),-0.09637799091491725+0j, 9)

    def test_pnucp(self):
        cell1 = gto.Cell()
        cell1.atom = '''
        He   1.3    .2       .3
        He    .1    .1      1.1 '''
        cell1.basis = {'He': [[0, [0.8, 1]],
                              [1, [0.6, 1]]
                             ]}
        cell1.gs = [7]*3
        cell1.a = numpy.array(([2.0,  .9, 0. ],
                               [0.1, 1.9, 0.4],
                               [0.8, 0  , 2.1]))
        cell1.build()

        charge = -cell1.atom_charges()
        Gv = cell1.get_Gv(cell1.gs)
        SI = cell1.get_SI(Gv)
        rhoG = numpy.dot(charge, SI)

        coulG = tools.get_coulG(cell1, gs=cell1.gs, Gv=Gv)
        vneG = rhoG * coulG
        vneR = tools.ifft(vneG, cell1.gs).real

        coords = cell1.gen_uniform_grids(gs=cell1.gs)
        aoR = dft.numint.eval_ao(cell1, coords, deriv=1)
        ngrids, nao = aoR.shape[1:]
        vne_ref = numpy.einsum('p,xpi,xpj->ij', vneR, aoR[1:4], aoR[1:4])

        mydf = df.AFTDF(cell1)
        dat = sfx2c1e.get_pnucp(mydf)
        self.assertAlmostEqual(abs(dat-vne_ref).max(), 0, 7)

        mydf.eta = 0
        dat = sfx2c1e.get_pnucp(mydf)
        self.assertAlmostEqual(abs(dat-vne_ref).max(), 0, 7)


if __name__ == '__main__':
    print("Full Tests for pbc.scf.x2c")
    unittest.main()
