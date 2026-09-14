#!/usr/bin/env python3
"""Reproducible local synthetic benchmark; no model calls or adoption claims."""
import argparse
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import tempfile
import threading
import time
from urllib.request import urlopen
from aifirst10 import Reader


def encoded(value): return (json.dumps(value, separators=(',', ':'))+'\n').encode()


def item(n, version='1.0', language='en'):
    return {'id': f'urn:benchmark:item:{n}', 'kind': 'knowledge',
            'title': f'Install {version} {language}', 'description': 'Installation instructions',
            'language': language, 'revision': '1', 'status': 'published',
            'source': f'doc-{n}.md', 'appliesTo': {'product': 'urn:benchmark:product', 'versions': [version]},
            'representations': [{'href': f'doc-{n}.md', 'mediaType': 'text/markdown'}]}


def manifest():
    return {'format': 'ai-first', 'formatVersion': '1.0', 'document': 'manifest',
            'revision': 'root-1', 'resource': {'id': 'urn:benchmark:resource', 'name': 'Benchmark',
            'description': 'Synthetic test data', 'language': 'en', 'scope': './',
            'publisher': {'name': 'AI First reference fixtures'}}}


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *args): pass


def benchmark():
    with tempfile.TemporaryDirectory() as directory:
        root=Path(directory);large=root/'large';large.mkdir();small=root/'small';small.mkdir()
        doc=manifest();doc['requires']=['selective-catalogs'];doc['catalogs']=[]
        target=42*200+7
        for shard in range(500):
            items=[item(shard*200+n,str(shard)) for n in range(200)]
            cat={'format':'ai-first','formatVersion':'1.0','document':'catalog','revision':f'shard-{shard}',
                 'resourceId':doc['resource']['id'],'items':items}
            data=encoded(cat);name=f'shard-{shard}.json';(large/name).write_bytes(data)
            doc['catalogs'].append({'href':name,'description':f'Version {shard}', 'revision':cat['revision'],
                                    'sha256':hashlib.sha256(data).hexdigest(),'select':{'versions':[str(shard)]}})
        (large/'ai.json').write_bytes(encoded(doc));(large/f'doc-{target}.md').write_text('# Selected material\n\n```text\nexact example\n```\n')
        records=[]
        for version in ('1.0','2.0'):
            for language in ('en','fr'):
                i=item(len(records),version,language)
                text=f'# Install {version} {language}\n\n| Setting | Value |\n| --- | --- |\n| Port | 443 |\n\n```sh\nexample --version {version}\n```\n'
                (small/i['source']).write_text(text);records.append(i)
        s=manifest();s['items']=records;(small/'ai.json').write_bytes(encoded(s))
        html='<html><body><h1>Documentation</h1>'+''.join(f'<a href="{i["source"]}">{i["title"]}</a>' for i in records)+'</body></html>'
        llms='# Documentation\n\n> Installation instructions\n\n## Guides\n\n'+'\n'.join(f'- [{i["title"]}]({i["source"]}): Installation instructions' for i in records)+'\n'
        (small/'index.html').write_text(html);(small/'llms.txt').write_text(llms)
        server=ThreadingHTTPServer(('127.0.0.1',0),lambda *a,**kw:Handler(*a,directory=root,**kw))
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        base=f'http://127.0.0.1:{server.server_port}/'
        try:
            started=time.perf_counter();reader=Reader(base+'large/',allow_loopback=True)
            reader.discover();report=reader.inventory({'versions':['42'],'ids':[f'urn:benchmark:item:{target}']})
            found=reader.select(item_id=f'urn:benchmark:item:{target}',version='42');material=reader.material(*found[0])
            assert report['completeness']=='targeted' and len(report['omittedCatalogs'])==499
            assert len(reader.transport.records)==3 and len(report['items'])==200
            large_result={'itemsInPublication':100000,'shards':500,'itemsPerShard':200,
                          'catalogsFetched':report['catalogRequests'],'catalogsOmitted':499,
                          'itemsLoaded':len(report['items']),'httpRequests':len(reader.transport.records),
                          'decodedBytes':reader.transport.total,'transferredBytes':reader.transport.wire_total,
                          'elapsedSeconds':round(time.perf_counter()-started,6),'completeness':material['completeness'],
                          'selectedId':material['id'],'limits':'reference defaults; no raised descriptor or item limits'}
            results=[]
            # Fixed deterministic tasks, exact version/language matching. All
            # three indexes deliberately contain enough information to succeed.
            for expected in records:
                version=expected['appliesTo']['versions'][0];language=expected['language']
                expected_bytes=(small/expected['source']).read_bytes()
                for mode in ('ordinary-html','llms.txt','ai-first'):
                    requests=[];start=time.perf_counter()
                    if mode=='ai-first':
                        r=Reader(base+'small/',allow_loopback=True);r.discover();r.inventory()
                        matched=r.select(product='urn:benchmark:product',version=version,language=language)
                        result=r.material(*matched[0]);data=result['text'].encode();selected=result['id']
                        requests=[x['transferredBytes'] for x in r.transport.records]
                    else:
                        index='index.html' if mode=='ordinary-html' else 'llms.txt'
                        with urlopen(base+'small/'+index,timeout=10) as response: body=response.read()
                        requests.append(len(body));text=body.decode()
                        candidates=(re.findall(r'<a href="([^"]+)">([^<]+)</a>',text) if mode=='ordinary-html'
                                    else [(href,label) for label,href in re.findall(r'\[([^\]]+)\]\(([^)]+)\)',text)])
                        links=[href for href,label in candidates if label==f'Install {version} {language}']
                        assert len(links)==1
                        with urlopen(base+'small/'+links[0],timeout=10) as response:data=response.read()
                        requests.append(len(data));selected=next(i['id'] for i in records if i['source']==links[0])
                    results.append({'task':f'install-{version}-{language}','mode':mode,'correctSelection':selected==expected['id'],
                                    'exactMaterialBytes':data==expected_bytes,'codeAndTablePreserved':data==expected_bytes,
                                    'httpRequests':len(requests),'transferredBytes':sum(requests),
                                    'elapsedSeconds':round(time.perf_counter()-start,6)})
            return {'status':'pass','scope':'synthetic deterministic local HTTP tests, not LLM evaluation or independent adoption',
                    'largeCatalog':large_result,'fixedTasks':results,
                    'publishingEffort':{'sourceMetadataRecords':len(records),'metadataDuplicatedByHuman':0,
                                        'generatedIndexes':3,'humanTimeMeasured':False,
                                        'note':'All indexes derive from the same records; code does not estimate developer hours.'},
                    'limitations':['Loopback HTTP benchmark; HTTPS is covered separately by trusted-certificate tests.',
                                   'No model accuracy claims; ordinary and llms.txt titles include explicit version/language.',
                                   'AI First adds machine-checked constraints and provenance but is not guaranteed smaller or faster.',
                                   'Large fixture proves selective network retrieval; peak memory is not measured.',
                                   'No product pilot or third-party implementation evidence.']}
        finally:
            server.shutdown();server.server_close();thread.join()


if __name__=='__main__':
    print(json.dumps(benchmark(),indent=2))
