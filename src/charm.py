#!/usr/bin/env python3
  
import sys
sys.path.append('lib')
from ops.charm import CharmBase  # NoQA: E402
from ops.framework import StoredState  # NoQA: E402
from ops.main import main  # NoQA: E402
from ops.model import (  # NoQA: E402
    ActiveStatus,
    MaintenanceStatus,
    WaitingStatus,
)

from oci_image import OCIImageResource

import logging  # NoQA: E402
logger = logging.getLogger()


class BitlbeeK8sCharm(CharmBase):

    state = StoredState()

    def __init__(self, framework, key):
        super().__init__(framework, key)
        # get our bitlbee_image from juju
        # ie: juju deploy . --resource bitlbee_image=bitlbee:latest
        self.bitlbee_image = OCIImageResource(self, 'bitlbee_image')
        self.framework.observe(self.on.start, self.configure_pod)
        self.framework.observe(self.on.config_changed, self.configure_pod)
        self.framework.observe(self.on.upgrade_charm, self.configure_pod)

    def configure_pod(self, event):
        if not self.framework.model.unit.is_leader():
            self.model.unit.status = WaitingStatus('Not a leader')
            return

        bitlbee_image_details = self.bitlbee_image.fetch()
        self.model.unit.status = MaintenanceStatus('Configuring pod')
        config = self.model.config
        self.model.pod.set_spec({
            'containers': [{
                'name': self.framework.model.app.name,
                'imageDetails': bitlbee_image_details,
                'ports': [{
                    'containerPort': int(self.framework.model.config['bitlbee_port']),
                    'protocol': 'TCP',
                }],
                'config': {
                    'BITLBEE_PORT': config['bitlbee_port'],
                },
            }]
        })
        self.state.is_started = True
        self.model.unit.status = ActiveStatus()


if __name__ == '__main__':
    main(BitlbeeK8sCharm)