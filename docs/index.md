![T3CO Logo](./images/t3co_logo.svg)

# **T3CO** : Transportation Technology Total Cost of Ownership Tool
[![homepage](https://img.shields.io/badge/homepage-t3co-blue)](https://www.nlr.gov/transportation/t3co.html) [![github](https://img.shields.io/badge/github-t3co-blue.svg)](https://github.com/NatLabRockies/T3CO) [![documentation](https://img.shields.io/badge/documentation-t3co-blue.svg)](https://NatLabRockies.github.io/T3CO/) [![PyPI - Version](https://img.shields.io/pypi/v/t3co)](https://pypi.org/project/t3co/) ![GitHub License](https://img.shields.io/github/license/NLR/T3CO) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/t3co) 

## Description

This repo houses T3CO (Transportation Technology Total Cost of Ownership), software for modeling total cost of ownership for commercial vehicles with advanced powertrains.

**Upgrading to 2.1?** 2.1 corrects a residual-value error that affected every TCO result in 2.0.0, so results from 2.0.x should be regenerated. See [What's New in T3CO](./whats_new.md) for this and the new visualization module, faster optimization, and the 2.0 changes.

To learn about the models, go to the [Overview](./T3CO_Overview.md)

To get started with the tool, go to the [Installation Guide](./installation.md)

To run your first analysis after installing T3CO, go to the [Quick Start Guide](./quick_start.md)

## Usage

**T3CO** is a general framework allowing a user to determine the total cost of ownership (TCO) of a vehicle (sometimes a FASTSim vehicle model paired with drivecycle(s) for determining fuel efficiency). The user can also determine performance of gradeability, acceleration, and range. In addition to straight TCO computation there is also the option to optimize a vehicle powertrain such that it meets performance optional targets while also optionally minimizing TCO.

