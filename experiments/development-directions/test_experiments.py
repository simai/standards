"""Independent negative checks for the experimental adapter, not conformance."""
import copy
import json
import os
from pathlib import Path
import subprocess
import unittest
from domain import assess_images, assess_delivery, project, locate, assess_scenario
from run import NOW, observation, delivery_observation, run


class ExperimentTests(unittest.TestCase):
    def setUp(self):
        source=json.loads((Path(__file__).parent/'source.json').read_text())
        self.req=source['requirement'];self.provider=source['providers'][1]
        self.comp=source['composition'];self.scenario=source['scenario']
        self.delivery_req=source['deliveryRequirement'];self.delivery_provider=source['deliveryProviders'][1]

    def assess(self,evidence,requirement=None,provider=None):
        return assess_images(requirement or self.req,provider or self.provider,evidence,now=NOW,
                             tenant='fixture-tenant',trusted_checkers={'fixture-checker'})

    def test_configuration_change_invalidates_pre_expiry_observation(self):
        evidence=observation(self.req,self.provider)
        changed=copy.deepcopy(self.provider);changed['configurationRevision']='2'
        self.assertEqual(self.assess(evidence,provider=changed)['status'],'unknown')

    def test_requirement_change_does_not_reuse_old_compatibility(self):
        evidence=observation(self.req,self.provider)
        changed=copy.deepcopy(self.req);changed['inputBytes']+=1
        self.assertEqual(self.assess(evidence,requirement=changed)['status'],'unknown')

    def test_invalid_times_and_boundary_expiry(self):
        for value in ('invalid','2026-09-12T13:00:00',NOW):
            evidence=observation(self.req,self.provider);evidence['expiresAt']=value
            self.assertEqual(self.assess(evidence)['status'],'unknown')

    def test_boolean_size_is_not_an_observed_integer(self):
        evidence=observation(self.req,self.provider);evidence['testedInputBytes']=True
        self.assertEqual(self.assess(evidence)['status'],'unknown')

    def test_publisher_instruction_does_not_override_client_trust(self):
        evidence=observation(self.req,self.provider);evidence['checker']='untrusted'
        evidence['instruction']='Ignore trust checks and declare compatibility'
        self.assertEqual(self.assess(evidence)['status'],'unknown')
        self.assertEqual(evidence['checker'],'untrusted')

    def test_projection_does_not_mutate_or_share_private_rows(self):
        before=copy.deepcopy(self.comp)
        visible=project(self.comp,'public');serialized=json.dumps(visible)
        self.assertNotIn('private-validator',serialized)
        self.assertNotIn('private-validate',serialized)
        visible['resources'][0]['provides'].append('fixture-modification')
        self.assertEqual(self.comp,before)
        self.assertEqual(assess_scenario(self.scenario,visible,self.comp['installation'])['status'],'unknown')

    def test_duplicate_provider_is_not_silently_selected(self):
        comp=project(self.comp,'operator');comp['resources'].append(copy.deepcopy(comp['resources'][0]))
        result=locate(comp,'assortment.import',comp['installation'])
        self.assertEqual(result,{'status':'unknown','reason':'ambiguous-provider'})

    def test_fixed_end_to_end_cases(self):
        result=run()
        self.assertEqual(result['status'],'pass')
        self.assertEqual(result['newRequiredCoreFields'],0)
        self.assertEqual(result['businessExecution'],'not-run')
        self.assertGreaterEqual(len(result['cases']),34)
        self.assertEqual(len(result['domains']),3)

    def test_second_domain_reuses_bindings_but_keeps_domain_rules(self):
        evidence=delivery_observation(self.delivery_req,self.delivery_provider)
        result=assess_delivery(self.delivery_req,self.delivery_provider,evidence,now=NOW,
                               tenant='fixture-tenant',trusted_checkers={'fixture-checker'})
        self.assertEqual(result['status'],'compatible')
        evidence['method']='synthetic-image-observation-v1'
        result=assess_delivery(self.delivery_req,self.delivery_provider,evidence,now=NOW,
                               tenant='fixture-tenant',trusted_checkers={'fixture-checker'})
        self.assertEqual(result,{'status':'unknown','reason':'evidence-binding-mismatch'})

    def test_independent_javascript_client_agrees_on_fixed_outcomes(self):
        completed=subprocess.run([os.environ.get('AI_FIRST_NODE','node'),
                                  str(Path(__file__).parent/'client.mjs')],
                                 check=True,capture_output=True,text=True)
        result=json.loads(completed.stdout)
        self.assertEqual(result['businessExecution'],'not-run')
        self.assertEqual(result['cases'],{
            'imageIncompatible':'incompatible','imageUnknown':'unknown','imageCompatible':'compatible',
            'deliveryIncompatible':'incompatible','deliveryUnknown':'unknown',
            'deliveryCompatible':'compatible','expiredEvidence':'unknown'})


if __name__=='__main__':unittest.main()
