# SPDX-License-Identifier: LGPL-3.0-or-later
"""Separate sampled link admission candidate; no default integration change.

Adds one live-control edge before the existing SYS synchronizer. Sustained
fault/reset withdrawal is delayed by that edge; this is NOT asynchronous kill,
short-pulse capture, bounded physical latency or permission to retry MMIO.
The reset path remains independent and must retain coordinated reset policy.
"""
from migen import Module,Signal
from master_link_boundary import MasterLinkBoundary

class MasterAdmissionRegistered(Module):
    def __init__(self,admit,reset_request,*,control='control'):
        self.allowed=Signal(reset=0)
        sync=getattr(self.sync,control)
        sync += self.allowed.eq(admit & ~reset_request)

class MasterLinkBoundaryRegistered(Module):
    def __init__(self,codec,admit,reset_request,status):
        self.submodules.sample=sample=MasterAdmissionRegistered(admit,reset_request)
        self.submodules.boundary=boundary=MasterLinkBoundary(codec,sample.allowed,reset_request,status)
        self.allowed=boundary.allowed
        self.gt_reset_request=boundary.gt_reset_request
