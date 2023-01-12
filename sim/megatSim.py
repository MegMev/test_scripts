#!/usr/bin/python3

from __future__ import absolute_import, unicode_literals
import os
import sys
import time
import logging
import DDG4
from DDG4 import OutputLevel as Output
from g4units import keV, GeV, mm, ns, MeV
#
#
logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def help():
  logging.info("megatSim.py -option [-option]                           ")
  logging.info("       -vis   <file>            Enable visualization  ")
  logging.info("                                Macro file is optional")
  logging.info("       -macro <file>            Start G4 macro        ")
  logging.info("       -batch                   Batch execution       ")
  logging.info("       -events <number>         If batch: number of events to be executed")

def run():
  args = DDG4.CommandLine(help)

  # Kernel is KernelHandle class, create/return the master instance
  kernel = DDG4.Kernel()
  description = kernel.detectorDescription()
  install_dir = os.environ['REST_PATH']
  kernel.loadGeometry(str("file:" + install_dir + "/geometry/compact/Megat.xml"))
  DDG4.importConstants(description)

  geant4 = DDG4.Geant4(kernel)
  geant4.printDetectors()
  logger.info("#  Configure UI")
  ui = geant4.setupCshUI(macro=args.macro, vis=args.vis)
  kernel.UI = 'UI'
  if args.batch:
    ui.Commands = ['/run/beamOn ' + str(args.events), '/ddg4/UI/terminate']

  # logger.info("#  Configure G4 magnetic field tracking")
  # geant4.setupTrackingField()

  logger.info("#  Setup random generator")
  rndm = DDG4.Action(kernel, 'Geant4Random/Random')
  rndm.Seed = 987654321
  if args.seed_time:
    rndm.Seed = int(time.time())
  rndm.initialize()
  rndm.showStatus()

  logger.info("#  Configure Run actions")
  run1 = DDG4.RunAction(kernel, 'Geant4TestRunAction/RunInit')
  run1.Property_int = 12345
  run1.Property_double = -5e15 * keV
  run1.Property_string = 'Startrun: Hello_2'
  logger.info("%s %s %s", run1.Property_string, str(run1.Property_double), str(run1.Property_int))
  run1.enableUI()
  kernel.registerGlobalAction(run1)
  kernel.runAction().adopt(run1)

  logger.info("#  Configure Event actions")
  prt = DDG4.EventAction(kernel, 'Geant4ParticlePrint/ParticlePrint')
  prt.OutputLevel = Output.INFO
  prt.OutputType = 3  # Print both: table and tree
  kernel.eventAction().adopt(prt)

  logger.info(""" Configure I/O """)
  geant4.setupROOTOutput('RootOutput', 'megat_' + time.strftime('%Y-%m-%d_%H-%M'))

  gen = DDG4.GeneratorAction(kernel, "Geant4GeneratorActionInit/GenerationInit")
  kernel.generatorAction().adopt(gen)

  # VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV
  logger.info("""
  Generation of isotrope tracks of a given multiplicity with overlay:
  """)
  # logger.info("#  First particle generator: pi+")
  # gen = DDG4.GeneratorAction(kernel, "Geant4IsotropeGenerator/IsotropPi+")
  # gen.Mask = 1
  # gen.Particle = 'pi+'
  # gen.Energy = 10 * MeV
  # gen.Multiplicity = 2
  # gen.Distribution = 'uniform'
  # kernel.generatorAction().adopt(gen)
  # logger.info("#  Install vertex smearing for this interaction")
  # gen = DDG4.GeneratorAction(kernel, "Geant4InteractionVertexSmear/SmearPi+")
  # gen.Mask = 1
  # gen.Offset = (0 * mm, 0 * mm, 0 * mm, 0 * ns)
  # gen.Sigma = (0 * mm, 0 * mm, 100 * mm, 0 * ns)
  # kernel.generatorAction().adopt(gen)

  logger.info("#  Second particle generator: mu+")
  gen = DDG4.GeneratorAction(kernel, "Geant4ParticleGenerator/Mu+")
  gen.Mask = 2
  gen.Particle = 'mu+'
  gen.Energy = 1000 * MeV
  gen.Multiplicity = 3
  gen.Position = (10*mm, 10*mm, 0*mm)
  gen.Direction = (0, 0, -1)
  kernel.generatorAction().adopt(gen)
  # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  # logger.info("#  Merge all existing interaction records")
  # gen = DDG4.GeneratorAction(kernel, "Geant4InteractionMerger/InteractionMerger")
  # gen.OutputLevel = 4  # generator_output_level
  # gen.enableUI()
  # kernel.generatorAction().adopt(gen)
  #
  logger.info("#  Finally generate Geant4 primaries")
  gen = DDG4.GeneratorAction(kernel, "Geant4PrimaryHandler/PrimaryHandler")
  gen.OutputLevel = 4  # generator_output_level
  gen.enableUI()
  kernel.generatorAction().adopt(gen)
  #
  logger.info("#  ....and handle the simulation particles.")
  part = DDG4.GeneratorAction(kernel, "Geant4ParticleHandler/ParticleHandler")
  kernel.generatorAction().adopt(part)
  part.SaveProcesses = ['conv','Decay']
  part.MinimalKineticEnergy = 10 * MeV
  part.OutputLevel = 5  # generator_output_level
  part.enableUI()
  user = DDG4.Action(kernel, "Geant4TCUserParticleHandler/UserParticleHandler")
  user.enableUI()
  part.adopt(user)
  
  # logger.info("#  Setup global filters fur use in sensitive detectors")
  # f1 = DDG4.Filter(kernel, 'GeantinoRejectFilter/GeantinoRejector')
  # f2 = DDG4.Filter(kernel, 'ParticleRejectFilter/OpticalPhotonRejector')
  # f2.particle = 'opticalphoton'
  # f3 = DDG4.Filter(kernel, 'ParticleSelectFilter/OpticalPhotonSelector')
  # f3.particle = 'opticalphoton'
  # f4 = DDG4.Filter(kernel, 'EnergyDepositMinimumCut')
  # f4.Cut = 1 * keV
  # f4.enableUI()
  # kernel.registerGlobalFilter(f1)
  # kernel.registerGlobalFilter(f2)
  # kernel.registerGlobalFilter(f3)
  # kernel.registerGlobalFilter(f4)
  #
  # logger.info("#  First the tracking detectors")
  # seq, act = geant4.setupTracker('SiVertexBarrel')
  # seq.adopt(f1)
  # act.adopt(f1)
  # seq, act = geant4.setupTracker('SiTrackerBarrel')
  #
  logger.info("#  Now setup the calorimeters")
  seq, act = geant4.setupCalorimeter('Calorimeter')
  #
  logger.info("#  Now build the physics list:")
  phys = geant4.setupPhysics('QGSP_BERT')
  ph = geant4.addPhysics(str('Geant4PhysicsList/Myphysics'))
  ph.addPhysicsConstructor(str('G4StepLimiterPhysics'))
  #
  # Add global range cut
  # rg = geant4.addPhysics(str('Geant4DefaultRangeCut/GlobalRangeCut'))
  # rg.RangeCut = 0.7 * mm

  # phys.dump()
  #
  if ui and args.vis:
    cmds = []
    cmds.append('/control/verbose 2')
    cmds.append('/run/initialize')
    cmds.append('/vis/open OGL')
    cmds.append('/vis/verbose errors')
    cmds.append('/vis/drawVolume')
    cmds.append('/vis/viewer/set/viewpointThetaPhi 55. 45.')
    cmds.append('/vis/scene/add/axes 0 0 0 10 m')
    ui.Commands = cmds

  kernel.configure()
  kernel.initialize()

  DDG4.setPrintLevel(Output.DEBUG)
  kernel.run()
  kernel.terminate()

if __name__ == "__main__":
  run()
