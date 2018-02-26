import unittest2 as unittest
import argparse
from os.path import join
from os import access,R_OK
from autoanalysis.processmodules.Bleach import Bleach, create_parser

class TestBleach(unittest.TestCase):
    def setUp(self):
        parser = create_parser()
        args = parser.parse_args()
        inputdir = args.outputdir
        datafiles = [join(inputdir, args.datafile), join(inputdir, args.bleachfile)]
        self.mod = Bleach(datafiles, args.outputdir, showplots=False)
        self.args = args

    def test_config(self):
        cfg = self.mod.getConfigurables()
        # set values - this will be done from configdb
        cfg['EXPT_EXCEL'] = self.args.suffix
        self.mod.setConfigurables(cfg)
        self.assertEqual(self.mod.cfg['EXPT_EXCEL'],self.args.suffix)

    def test_dataloaded(self):
        self.assertIsNotNone(self.mod.data)
