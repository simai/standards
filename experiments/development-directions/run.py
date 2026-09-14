#!/usr/bin/env python3
"""Run isolated demonstrations through the existing reader; no service calls."""
import copy
import json
from pathlib import Path
import sys
import tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'tools'))
from aifirst02 import Reader
from domain import digest, project, locate, assess_scenario, assess_images, assess_delivery

HERE = Path(__file__).resolve().parent
NOW = '2026-09-12T12:00:00+00:00'


def material(value):
    # Complete fenced JSON is readable documentation and preserves every field.
    return '# Experiment domain description\n\nSynthetic data; not executable instructions.\n\n```json\n'+json.dumps(value,indent=2)+'\n```\n'


def build_publication(root, value):
    data = json.dumps(value,indent=2)+'\n'
    (root/'domain.json').write_text(data)
    (root/'domain.md').write_text(material(value))
    reps = [{'href':name,'mediaType':media} for name,media in
            [('domain.json','application/json'),('domain.md','text/markdown')]]
    manifest = {'format':'ai-first','formatVersion':'0.2','document':'manifest','revision':digest(value),
                'resource':{'id':'urn:fixture:publication','name':'Experiment','description':'Domain descriptions for isolated tests',
                            'language':'en','scope':'./','publisher':{'name':'Synthetic fixture'}},
                'items':[{'id':'urn:fixture:description','kind':'knowledge','title':'Domain description','description':'Synthetic composition and scenario',
                          'language':'en','revision':digest(value),'status':'published','source':'domain.md','representations':reps}],
                'related':[{'href':'https://unreachable.invalid/ai.json','relation':'associated-description','description':'An unverified association'}]}
    (root/'ai.json').write_text(json.dumps(manifest,indent=2)+'\n')


def observation(requirement, provider):
    return {'subject':provider['id'],'providerDigest':digest(provider),'requirementDigest':digest(requirement),
            'tenant':'fixture-tenant','configurationRevision':provider['configurationRevision'],
            'method':'synthetic-image-observation-v1','checker':'fixture-checker',
            'observedAt':'2026-09-12T11:00:00+00:00','expiresAt':'2026-09-12T13:00:00+00:00',
            'testedInputBytes':12582912,'result':'pass'}


def delivery_observation(requirement, provider):
    return {'subject':provider['id'],'providerDigest':digest(provider),'requirementDigest':digest(requirement),
            'tenant':'fixture-tenant','configurationRevision':provider['configurationRevision'],
            'method':'synthetic-delivery-observation-v1','checker':'fixture-checker',
            'observedAt':'2026-09-12T11:00:00+00:00','expiresAt':'2026-09-12T13:00:00+00:00',
            'testedWeightKg':20,'result':'pass'}


def run():
    source=json.loads((HERE/'source.json').read_text()); results=[]
    def record(name, actual, expected):
        if actual != expected: raise AssertionError((name,actual,expected))
        results.append({'case':name,'observed':actual,'expected':expected,'status':'pass'})
    comp=source['composition'];scenario=source['scenario'];install=comp['installation']
    for layout in ('monolith','remote'):
        projected=project(comp,'operator')
        for r in projected['resources']:
            r['location']=('https://shop.example/services/'+r['id'].split(':')[-1] if layout=='monolith'
                           else 'https://'+r['id'].split(':')[-1]+'.example/')
        result=locate(projected,'assortment.import',install)
        record(layout+'-same-provider',result['provider'],'urn:fixture:catalog')
        record(layout+'-not-installation-proof',result['installedVerified'],False)
    public=project(comp,'public')
    record('hidden-prerequisite',assess_scenario(scenario,public,install)['status'],'unknown')
    public_text=json.dumps(public)+material(public)
    record('hidden-name-not-exported','private-validator' in public_text,False)
    record('hidden-contract-not-exported','private-validate' in public_text,False)
    missing=project(comp,'operator');missing['resources']=missing['resources'][:1]
    record('known-missing-prerequisite',assess_scenario(scenario,missing,install)['status'],'missing-prerequisite')
    full=project(comp,'operator')
    record('declared-prerequisites',assess_scenario(scenario,full,install)['status'],'declared-prerequisites-present')
    record('wrong-installation',locate(full,'assortment.import','urn:other')['status'],'unknown')
    unavailable=copy.deepcopy(full);unavailable['resources'][0]['availability']='unavailable'
    record('unavailable-provider',locate(unavailable,'assortment.import',install)['status'],'unknown')
    req=source['requirement'];x,y=source['providers']
    evaluate=lambda provider,e:assess_images(req,provider,e,now=NOW,tenant='fixture-tenant',trusted_checkers={'fixture-checker'})
    record('provider-X',evaluate(x,None)['status'],'incompatible')
    record('provider-Y-without-evidence',evaluate(y,None)['status'],'unknown')
    good=observation(req,y)
    record('provider-Y-bound-evidence',evaluate(y,good)['status'],'compatible')
    for key,value in [('expiresAt','2026-09-12T11:30:00+00:00'),('observedAt','2026-09-13T00:00:00+00:00'),
                      ('tenant','other-tenant'),('providerDigest','0'*64),('requirementDigest','0'*64),
                      ('checker','untrusted'),('configurationRevision','2'),('result','fail'),('testedInputBytes',1024)]:
        bad=copy.deepcopy(good);bad[key]=value
        record('evidence-'+key,evaluate(y,bad)['status'],'unknown')
    delivery_req=source['deliveryRequirement'];delivery_a,delivery_b=source['deliveryProviders']
    evaluate_delivery=lambda provider,e:assess_delivery(
        delivery_req,provider,e,now=NOW,tenant='fixture-tenant',trusted_checkers={'fixture-checker'})
    record('delivery-provider-A',evaluate_delivery(delivery_a,None)['status'],'incompatible')
    record('delivery-provider-B-without-evidence',evaluate_delivery(delivery_b,None)['status'],'unknown')
    delivery_good=delivery_observation(delivery_req,delivery_b)
    record('delivery-provider-B-bound-evidence',evaluate_delivery(delivery_b,delivery_good)['status'],'compatible')
    delivery_small=copy.deepcopy(delivery_good);delivery_small['testedWeightKg']=5
    record('delivery-provider-B-insufficient-weight',evaluate_delivery(delivery_b,delivery_small)['status'],'unknown')
    transfer=[]
    with tempfile.TemporaryDirectory() as directory:
        for audience in ('public','operator'):
            root=Path(directory)/audience;root.mkdir()
            value={'composition':project(comp,audience),
                   'domainExamples': {'image': {'requirement': req, 'providers': source['providers']},
                                      'delivery': {'requirement': delivery_req,
                                                   'providers': source['deliveryProviders']}}}
            # A scenario naming a protected capability is itself protected.
            if audience=='operator':value['scenario']=scenario
            build_publication(root,value)
            reader=Reader(root);reader.discover();inventory=reader.inventory();result=reader.material(*reader.select()[0])
            record(audience+'-read-original-value',json.loads(result['text']),value)
            record(audience+'-publication-complete',inventory['completeness'],'complete')
            record(audience+'-related-not-fetched',any(r['url'].startswith('https:') for r in reader.transport.records),False)
            if audience=='public':
                output=json.dumps(result)
                record('public-reader-no-private-name','private-validator' in output,False)
                record('public-reader-no-private-contract','private-validate' in output,False)
            validation=reader.publication();record(audience+'-publication-validation',validation['publication'],'pass')
            transfer.append({'audience':audience,'readerRequests':len(reader.transport.records),
                             'decodedBytes':reader.transport.total,'transport':'local-files-including-validation'})
    return {'status':'pass','experimentOnly':True,'businessExecution':'not-run','newRequiredCoreFields':0,
            'newWireProfiles':0,'cases':results,'measurements':transfer,
            'domains':['assortment-composition','image-processing','delivery'],
            'sharedEvidenceFields':['subject','providerDigest','requirementDigest','tenant',
                                    'configurationRevision','method','checker','observedAt','expiresAt','result'],
            'semanticsOwner':'Synthetic domain adapter, not generic AI First reader',
            'limitations':['Synthetic observations are not real image-processing evidence.',
                           'No product pilot or real tenant cache isolation is proven here.',
                           'Transport was local; current candidate has separate HTTPS tests.',
                           'Restricted projection does not enumerate hidden capabilities.',
                           'No automatic traversal, authorization, service switching or workflow execution.']}

if __name__=='__main__':print(json.dumps(run(),indent=2))
