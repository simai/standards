#!/usr/bin/env node
/** Standalone AI First 0.2 baseline reader. Node >= 20; no Python dependency.
 * Implements discovery, pinned catalogs and full knowledge-text reads.
 * Capability contracts, credential providers, cache and fallback languages are
 * Python reference features, not claimed by this baseline implementation.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL, fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import dns from 'node:dns/promises';
import https from 'node:https';
import http from 'node:http';
import net from 'node:net';

export class Failure extends Error {
  constructor(code, message) { super(message); this.code = code; }
}
const fail = (code, message) => { throw new Failure(code, message); };
const sha = data => createHash('sha256').update(data).digest('hex');
const utf8 = data => { try { return new TextDecoder('utf-8', {fatal:true, ignoreBOM:true}).decode(data); }
  catch { fail('invalid-text', 'Invalid UTF-8'); } };

export function strictJSON(data) {
  const text = utf8(data); let offset = 0;
  const space = () => { while (/[ \n\r\t]/.test(text[offset] ?? '\0')) offset++; };
  function string() {
    const start = offset++;
    while (offset < text.length) {
      const ch = text[offset++];
      if (ch === '\\') { offset++; continue; }
      if (ch === '"') {
        let value;
        try { value = JSON.parse(text.slice(start, offset)); }
        catch { fail('invalid-json','Invalid JSON string'); }
        for (let i=0; i<value.length; i++) {
          const code=value.charCodeAt(i);
          if (code>=0xd800 && code<=0xdbff) {
            const next=value.charCodeAt(++i);
            if (!(next>=0xdc00 && next<=0xdfff)) fail('invalid-json','Unpaired surrogate');
          } else if (code>=0xdc00 && code<=0xdfff) fail('invalid-json','Unpaired surrogate');
        }
        return value;
      }
    }
    fail('invalid-json','Unterminated string');
  }
  function value(depth=0) {
    if (depth>64) fail('limit-exceeded','JSON depth exceeded');
    space(); const ch=text[offset];
    if (ch==='"') return string();
    if (ch==='{' || ch==='[') {
      offset++; const object=ch==='{', result=object?Object.create(null):[];
      space(); if(text[offset]===(object?'}':']')) {offset++; return result;}
      for (;;) {
        space(); let key;
        if(object) {
          if(text[offset]!=='"') fail('invalid-json','Object key expected');
          key=string(); space();
          if(text[offset++]!==':') fail('invalid-json','Colon expected');
          if(Object.hasOwn(result,key)) fail('invalid-json','Duplicate object key');
        }
        const child=value(depth+1); if(object) result[key]=child; else result.push(child);
        space(); const end=text[offset++];
        if(end===(object?'}':']')) return result;
        if(end!==',') fail('invalid-json','Delimiter expected');
      }
    }
    for(const [token, result] of [['true',true],['false',false],['null',null]]) {
      if(text.startsWith(token,offset)) {offset+=token.length; return result;}
    }
    const number=text.slice(offset).match(/^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?/);
    if(!number) fail('invalid-json','Invalid value');
    offset+=number[0].length; const result=Number(number[0]);
    if(!Number.isFinite(result)) fail('invalid-json','Non-finite number');
    return result;
  }
  const result=value(); space();
  if(offset!==text.length) fail('invalid-json','Trailing JSON data');
  return result;
}

// Implements the exact JSON Schema keywords used by the bundled 0.2 schemas.
// It is deliberately not exported or advertised as a general JSON Schema engine.
function valid(value, schema, root=schema) {
  if(schema.$ref) return valid(value, schema.$ref.slice(2).split('/').reduce((o,k)=>o[k],root), root);
  if(schema.const!==undefined && value!==schema.const) return false;
  if(schema.enum && !schema.enum.includes(value)) return false;
  const type = value===null?'null':Array.isArray(value)?'array':typeof value;
  if(schema.type && schema.type!==type) return false;
  if(type==='string' && ((schema.minLength && [...value].length<schema.minLength) ||
      (schema.pattern && !(new RegExp(schema.pattern,'u')).test(value)))) return false;
  if(type==='array') {
    if(schema.minItems && value.length<schema.minItems) return false;
    if(schema.uniqueItems && new Set(value.map(v=>JSON.stringify(v))).size!==value.length) return false;
    if(schema.items && !value.every(v=>valid(v,schema.items,root))) return false;
  }
  if(type==='object') {
    if(schema.minProperties && Object.keys(value).length<schema.minProperties) return false;
    if(schema.required?.some(k=>!Object.hasOwn(value,k))) return false;
    for(const [key, child] of Object.entries(value)) {
      if(schema.properties?.[key]) { if(!valid(child,schema.properties[key],root)) return false; }
      else if(schema.additionalProperties===false) return false;
    }
  }
  if(schema.allOf && !schema.allOf.every(s=>valid(value,s,root))) return false;
  if(schema.anyOf && !schema.anyOf.some(s=>valid(value,s,root))) return false;
  if(schema.not && valid(value,schema.not,root)) return false;
  if(schema.if && valid(value,schema.if,root) && schema.then && !valid(value,schema.then,root)) return false;
  return true;
}
const schemas={};
for(const kind of ['manifest','catalog']) schemas[kind]=JSON.parse(await fs.readFile(new URL(`../schemas/0.2/${kind}.schema.json`, import.meta.url),'utf8'));
export function structure(doc, kind) {
  if(!doc || doc.format!=='ai-first') fail('unknown-format','Expected AI First');
  if(doc.formatVersion!=='0.2') fail('unsupported-version','Expected 0.2');
  if(doc.document!==kind || !valid(doc, schemas[kind])) fail('invalid-structure','Schema violation');
  const requires=new Set(doc.requires ?? []);
  if([...requires].some(p=>!['core','knowledge','selective-catalogs','translations'].includes(p)))
    fail('unsupported-profile','Profile is outside JavaScript baseline');
  if(doc.access) fail('unsupported-profile','Protected reading is outside JavaScript baseline');
  const ids=new Set();
  for(const item of doc.items ?? []) {
    if(ids.has(item.id)) fail('duplicate-id','Duplicate item'); ids.add(item.id);
    if(item.kind==='capability') fail('unsupported-profile','Capability contract validation is outside baseline');
    if(item.translationOf && !requires.has('translations')) fail('missing-profile','Translation profile required');
    if(!item.representations.some(r=>(r.role??'full')==='full') || item.representations.some(r=>(r.language??item.language).toLowerCase()!==item.language.toLowerCase()))
      fail('invalid-structure','Full representation or language mismatch');
  }
  if((doc.catalogs??[]).some(l=>l.select) && !requires.has('selective-catalogs')) fail('missing-profile','Selector profile required');
  return doc;
}
function resolve(base, href) {
  if(typeof href!=='string' || /[\s\\\x00-\x1f\x7f]/u.test(href) || href.startsWith('//')) fail('access-blocked','Unsafe reference');
  const u=new URL(href,base);
  if(u.username || u.password) fail('access-blocked','Credentials in URL');
  return u.href;
}
function scope(base, href) {
  const u=new URL(resolve(base,href));
  if(!u.pathname.endsWith('/') || u.search || u.hash || !['file:','https:','http:'].includes(u.protocol)) fail('invalid-scope','Invalid directory scope');
  if(/%2f|%5c|%2e/i.test(href)) fail('invalid-scope','Encoded scope is ambiguous');
  return u.href;
}
function covers(scopeURL,target) {const a=new URL(scopeURL),b=new URL(target); return a.origin===b.origin && a.protocol===b.protocol && b.pathname.startsWith(a.pathname);}
function skipped(bound,query) {return Object.entries(bound).some(([key,values])=>query[key]?.length &&
  !values.some(v=>query[key].some(q=>key==='languages'?q.toLowerCase()===v.toLowerCase():q===v)));}
function within(item,bound) {
  const a=item.appliesTo??{}, vals={ids:[item.id],languages:[item.language],products:a.product?[a.product]:[],versions:a.versions??[],kinds:[item.kind]};
  return Object.entries(bound).every(([key,b])=>vals[key].length && vals[key].every(v=>b.some(x=>key==='languages'?x.toLowerCase()===v.toLowerCase():x===v)));
}
function fields(value,delimiter) {
  let quote=false,angle=false,escape=false,start=0; const out=[];
  for(let i=0;i<value.length;i++) {const ch=value[i];
    if(escape){escape=false;continue;} if(quote && ch==='\\'){escape=true;continue;}
    if(ch==='"' && !angle) quote=!quote;
    else if(!quote) {if(ch==='<')angle=true;else if(ch==='>')angle=false;else if(ch===delimiter && !angle){out.push(value.slice(start,i).trim());start=i+1;}}
  }
  out.push(value.slice(start).trim());return out;
}
export function declarations(html,header='') {
  const targets=[];
  // Quote-aware HTML start-tag scanner; comments and raw script/style text are
  // removed before interpreting metadata. No script is executed.
  html=html.replace(/<!--[\s\S]*?-->/g,'').replace(/<(script|style)\b[^>]*>[\s\S]*?<\/\1\s*>/gi,'');
  for(const match of html.matchAll(/<link\b(?:[^>"']|"[^"]*"|'[^']*')*>/gi)) {
    const attrs={};
    for(const m of match[0].slice(5,-1).matchAll(/([^\s=/>]+)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))/g)) attrs[m[1].toLowerCase()]=m[2]??m[3]??m[4];
    if((attrs.rel??'').toLowerCase().split(/\s+/).includes('describedby') && attrs.type?.toLowerCase()==='application/json' && attrs['data-ai-first']==='0.2' && attrs.href) {
      targets.push(attrs.href.replace(/&amp;/g,'&').replace(/&#(x[0-9a-f]+|[0-9]+);/gi,(_,n)=>String.fromCodePoint(n[0].toLowerCase()==='x'?parseInt(n.slice(1),16):Number(n))));
    }
  }
  for(const field of fields(header,',')) {
    const parts=fields(field,';'); if(!/^<.*>$/.test(parts[0]))continue;
    const params={};let duplicate=false;
    for(const p of parts.slice(1)) {const pos=p.indexOf('=');if(pos<0)continue;const key=p.slice(0,pos).trim().toLowerCase();let value=p.slice(pos+1).trim();
      if(value.startsWith('"')&&value.endsWith('"'))value=value.slice(1,-1).replace(/\\(.)/g,'$1');
      if(Object.hasOwn(params,key))duplicate=true;params[key]=value;}
    if((params.rel??'').toLowerCase().split(/\s+/).includes('describedby') && params.type?.toLowerCase()==='application/json' && params['ai-first']==='0.2') {
      if(duplicate || params.anchor!==undefined)fail('ambiguous-discovery','Ambiguous Link declaration');targets.push(parts[0].slice(1,-1));}
  }
  return targets;
}


function publicAddress(address) {
  if(net.isIP(address)===4) {
    const [a,b,c]=address.split('.').map(Number);
    return !(a===0||a===10||a===127||a>=224||a===100&&b>=64&&b<=127||
      a===169&&b===254||a===172&&b>=16&&b<=31||a===192&&(b===168||b===0||b===88&&c===99)||
      a===198&&(b===18||b===19||b===51&&c===100)||a===203&&b===0&&c===113);
  }
  if(net.isIP(address)===6) {
    const words=address.toLowerCase().split(':');const a=parseInt(words[0],16),b=parseInt(words[1]||'0',16);
    return a>=0x2000&&a<0x4000&&a!==0x2002&&a!==0x3fff&&!(a===0x2001&&(b<0x200||b===0xdb8));
  }
  return false;
}

export class Reader {
  constructor(entry,{allowLoopback=false,allowOrigins=[],ca,limits={}}={}) {
    this.input=entry;this.entry=null;this.root=null;
    this.allowLoopback=allowLoopback;this.allowed=new Set(allowOrigins.map(u=>new URL(u).origin));this.ca=ca;
    this.limits={descriptor:262144,material:8388608,total:33554432,documents:64,depth:8,items:10000,timeout:10000,redirects:5,...limits};
    this.total=0;this.wire=0;this.documents=0;this.records=[];
  }
  async init() {
    if(/^https?:/.test(this.input)){this.entry=resolve(this.input,this.input);this.allowed.add(new URL(this.entry).origin);}
    else {const p=await fs.realpath(this.input), stat=await fs.stat(p);this.root=stat.isDirectory()?p:path.dirname(p);this.entry=pathToFileURL(p).href+(stat.isDirectory()?'/':'');}
    return this;
  }
  async fetch(address,media,descriptor=false) {
    const cap=descriptor?this.limits.descriptor:this.limits.material;
    if(descriptor && ++this.documents>this.limits.documents)fail('limit-exceeded','Descriptor count');
    const original=address;let current=address;const seen=new Set(),deadline=Date.now()+this.limits.timeout;
    try {
      for(let hop=0;hop<=this.limits.redirects;hop++) {
        current=resolve(current,current);const u=new URL(current);u.hash='';current=u.href;
        if(seen.has(current))fail('cycle','Redirect cycle');seen.add(current);
        let data,headers={},wire=0;
        if(u.protocol==='file:') {
          if(!this.root || u.host || u.search)fail('access-blocked','Local access not authorized');
          const filename=await fs.realpath(fileURLToPath(u));const rel=path.relative(this.root,filename);
          if(rel==='..'||rel.startsWith('..'+path.sep)||path.isAbsolute(rel))fail('access-blocked','Path leaves root');
          const handle=await fs.open(filename,'r');
          try {
            const maximum=Math.min(cap,Math.max(0,this.limits.total-this.total))+1;
            const buffer=Buffer.alloc(maximum);let count=0;
            while(count<maximum){const got=await handle.read(buffer,count,maximum-count,count);if(!got.bytesRead)break;count+=got.bytesRead;}
            data=buffer.subarray(0,count);wire=data.length;
          }
          finally {await handle.close();}
        } else {
          if(!['http:','https:'].includes(u.protocol)||!this.allowed.has(u.origin))fail('access-blocked','Origin not authorized');
          const decoded=decodeURIComponent(u.pathname);
          if(/[\\\x00-\x20\x7f]/.test(decoded)||/%2f|%5c|%2e/i.test(u.pathname))fail('access-blocked','Ambiguous encoded path');
          const host=u.hostname.replace(/^\[|\]$/g,'');const addresses=await dns.lookup(host,{all:true});
          const loopback=a=>a.address==='::1'||/^127\./.test(a.address);
          if(!addresses.length || addresses.some(a=>!publicAddress(a.address)&&!(this.allowLoopback&&loopback(a))))
            fail('access-blocked','Network destination not authorized');
          if(u.protocol==='http:' && !(this.allowLoopback&&addresses.every(loopback)))
            fail('access-blocked','HTTP requires explicit loopback');
          if(Date.now()>=deadline)fail('limit-exceeded','Deadline exceeded');
          const a=addresses.find(a=>a.family===4)??addresses[0];
          const response=await new Promise((accept,reject)=>{
            const chunks=[];let length=0;const client=u.protocol==='https:'?https:http;
            const request=client.get(u,{ca:this.ca,headers:{Accept:media??'*/*','Accept-Encoding':'identity'},
              lookup:(_host,opts,cb)=>opts?.all?cb(null,[a]):cb(null,a.address,a.family)},res=>{
              if([301,302,303,307,308].includes(res.statusCode)){res.resume();accept({status:res.statusCode,headers:res.headers,data:Buffer.alloc(0)});return;}
              res.on('data',chunk=>{length+=chunk.length;if(length>cap||this.wire+length>this.limits.total){request.destroy(new Failure('limit-exceeded','Transferred bytes'));return;}chunks.push(chunk);});
              res.on('end',()=>accept({status:res.statusCode,headers:res.headers,data:Buffer.concat(chunks)}));res.on('error',reject);
            });
            const timer=setTimeout(()=>request.destroy(new Failure('limit-exceeded','Retrieval deadline')),Math.max(1,deadline-Date.now()));
            request.on('close',()=>clearTimeout(timer));request.on('error',reject);
          });
          headers=response.headers;
          if([301,302,303,307,308].includes(response.status)) {
            if(hop===this.limits.redirects)fail('limit-exceeded','Redirect limit');
            if(!headers.location)fail('invalid-redirect','Missing Location');
            const target=resolve(current,headers.location);
            if(!/^https?:/.test(target)||u.protocol==='https:'&&!target.startsWith('https:'))fail('access-blocked','Unsafe redirect');
            current=target;continue;
          }
          if([401,403].includes(response.status))fail('access-denied','Read denied');
          if([404,410].includes(response.status))fail('not-found','Resource missing');
          if(response.status!==200)fail('unavailable','HTTP status '+response.status);
          if(headers['content-encoding'] && headers['content-encoding']!=='identity')fail('unsupported-encoding','JavaScript baseline accepts identity only');
          if(media && (headers['content-type']??'').split(';')[0].trim().toLowerCase()!==media)fail('media-mismatch','Content-Type mismatch');
          data=response.data;wire=data.length;
        }
        this.total+=data.length;this.wire+=wire;
        if(data.length>cap||this.total>this.limits.total||this.wire>this.limits.total)fail('limit-exceeded','Byte limit');
        this.records.push({url:original,finalUrl:current,bytes:data.length,sha256:sha(data)});
        return {data,url:current,headers};
      }
    } catch(error) {
      if(error instanceof Failure)throw error;
      if(error.code==='ENOENT')fail('not-found','File missing');
      if(error.code==='EACCES')fail('access-denied','File denied');
      fail('unavailable','Retrieval failed');
    }
  }
  async document(url,kind){const r=await this.fetch(url,'application/json',true);return {doc:structure(strictJSON(r.data),kind),...r};}
  async discover(mode='root') {
    if(!this.entry)await this.init();let page=null,location;
    if(mode==='manifest')location=this.entry;
    else if(mode==='root'){if(!this.entry.endsWith('/'))fail('invalid-entry','Directory expected');page=this.entry;location=resolve(this.entry,'ai.json');}
    else if(mode==='page'){
      if(this.root)fail('invalid-entry','Online page required');const r=await this.fetch(this.entry,'text/html',true);page=r.url;
      const targets=[...new Set(declarations(utf8(r.data),r.headers.link??'').map(t=>{const u=new URL(resolve(page,t));u.hash='';return u.href;}))];
      if(targets.length>1)fail('ambiguous-discovery','Conflicting declarations');location=targets[0]??new URL('/ai.json',page).href;
    }else fail('invalid-entry','Unknown discovery mode');
    const seen=new Set();let expected;
    for(let depth=0;depth<=this.limits.depth;depth++) {
      const r=await this.document(location,'manifest');if(seen.has(r.url))fail('cycle','Route cycle');seen.add(r.url);
      const root=scope(r.url,r.doc.resource.scope);if(expected && expected!==root)fail('scope-mismatch','Child scope mismatch');
      const scopes=new Set(),matches=[];
      for(const route of r.doc.routes??[]) {
        const s=scope(r.url,route.scope);if(s===root||!covers(root,s))fail('invalid-scope','Invalid child scope');
        if(scopes.has(s))fail('ambiguous-discovery','Duplicate route scope');scopes.add(s);
        if(page && covers(s,page))matches.push([s,resolve(r.url,route.href)]);
      }
      if(page&&!covers(root,page))fail('scope-mismatch','Manifest does not cover page');
      if(matches.length){[expected,location]=matches.sort((a,b)=>b[0].length-a[0].length)[0];continue;}
      this.manifest=r.doc;this.base=r.url;return r.doc;
    }fail('limit-exceeded','Route depth');
  }
  async inventory(query={}) {
    const items=[],errors=[],omittedCatalogs=[],cache=new Map(),observed=new Map(),finalDigests=new Map(),ids=new Set();
    const visit=async(doc,url,stack,bounds,depth)=>{
      if(depth>this.limits.depth)fail('limit-exceeded','Catalog depth');if(stack.has(url))fail('cycle','Catalog cycle');
      if(observed.has(url)){for(const [i] of observed.get(url))if(!bounds.every(b=>within(i,b)))fail('selector-mismatch','Coverage mismatch');return observed.get(url);}
      const subtree=[];
      for(const i of doc.items??[])if(!bounds.every(b=>within(i,b)))fail('selector-mismatch','Coverage mismatch');
      for(const i of doc.items??[]){if(ids.has(i.id))fail('duplicate-id','Duplicate ID');if(ids.size>=this.limits.items)fail('limit-exceeded','Item count');ids.add(i.id);items.push([i,url]);subtree.push([i,url]);}
      for(const link of doc.catalogs??[]) {
        const target=resolve(url,link.href);if(skipped(link.select??{},query)){omittedCatalogs.push(target);continue;}
        try {
          if(stack.has(target)||target===url)fail('cycle','Catalog cycle');if(depth+1>this.limits.depth)fail('limit-exceeded','Catalog depth');
          if(!cache.has(target))cache.set(target,await this.document(target,'catalog'));const r=cache.get(target);
          if(finalDigests.has(r.url)&&finalDigests.get(r.url)!==sha(r.data))fail('revision-mismatch','Catalog changed at the same final URL');
          finalDigests.set(r.url,sha(r.data));
          if(r.doc.resourceId!==this.manifest.resource.id)fail('resource-mismatch','Catalog resource mismatch');
          if(link.revision!==undefined&&link.revision!==r.doc.revision)fail('revision-mismatch','Catalog pin mismatch');
          if(link.sha256!==undefined&&link.sha256!==sha(r.data))fail('digest-mismatch','Catalog digest mismatch');
          subtree.push(...await visit(r.doc,r.url,new Set([...stack,url]),[...bounds,link.select??{}],depth+1));
        }catch(e){if(!(e instanceof Failure)||e.code==='duplicate-id')throw e;errors.push({code:e.code,message:e.message,catalog:target});}
      }
      observed.set(url,subtree);return subtree;
    };
    await visit(this.manifest,this.base,new Set(),[],0);
    return this.report={items,errors,omittedCatalogs,completeness:errors.length?'partial':omittedCatalogs.length?'targeted':'complete'};
  }
  select({id,language,product,version,query='',kind}={}) {return this.report.items.filter(([i])=>i.status==='published'&&(!id||i.id===id)&&(!kind||i.kind===kind)&&(!language||i.language.toLowerCase()===language.toLowerCase())&&(!product||i.appliesTo?.product===product)&&(!version||i.appliesTo?.versions.includes(version))&&query.toLowerCase().split(/\s+/).every(t=>(i.title+' '+i.description).toLowerCase().includes(t)));}
  async material(item,base) {
    const warnings=[];
    for(const rep of item.representations) {
      if((rep.role??'full')!=='full'||!['text/markdown','text/plain','text/html','application/json'].includes(rep.mediaType))continue;
      try {const r=await this.fetch(resolve(base,rep.href),rep.mediaType);const digest=sha(r.data);if(rep.sha256&&rep.sha256!==digest)fail('digest-mismatch','Material digest mismatch');
        return {id:item.id,revision:item.revision,publicationRevision:this.manifest.revision,source:resolve(base,item.source),representation:r.url,mediaType:rep.mediaType,sha256:digest,text:utf8(r.data),language:item.language,completeness:this.report.completeness,errors:this.report.errors,omittedCatalogs:this.report.omittedCatalogs,warnings};
      }catch(e){if(!(e instanceof Failure)||e.code==='access-denied')throw e;warnings.push({code:e.code,message:e.message});}
    }
    fail(warnings[0]?.code??'unsupported-media','No readable full representation');
  }
}

async function main(args) {
  const [command,entry,...flags]=args;if(!['list','read'].includes(command)||!entry)fail('usage','Use list|read entry [--mode root|manifest|page]');
  const opts={},allowOrigins=[];let allowLoopback=false,ca;
  for(let i=0;i<flags.length;i++) {const key=flags[i];if(key==='--allow-loopback')allowLoopback=true;else if(key==='--allow-origin')allowOrigins.push(flags[++i]);else if(key==='--ca-file')ca=await fs.readFile(flags[++i]);else if(['--mode','--id','--language','--product','--version','--query','--kind'].includes(key))opts[key.slice(2)]=flags[++i];else fail('usage','Unknown option');}
  const r=new Reader(entry,{allowLoopback,allowOrigins,ca});await r.discover(opts.mode??'root');
  const selection={};for(const [key,dim] of [['id','ids'],['language','languages'],['product','products'],['version','versions'],['kind','kinds']])if(opts[key])selection[dim]=[opts[key]];
  await r.inventory(selection);const found=r.select(opts);let result;
  if(command==='read'){if(found.length!==1)fail(found.length?'ambiguous-selection':r.report.errors.length?'indeterminate':'no-match','Select one material');result=await r.material(...found[0]);}
  else result={...r.report,items:found.map(([i])=>i)};
  result.retrieved=r.records;console.log(JSON.stringify(result,null,2));return result.errors.length?1:0;
}
if(process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href===import.meta.url) {
  try {process.exitCode=await main(process.argv.slice(2));}
  catch(e){console.log(JSON.stringify({error:{code:e.code??'unavailable',message:e instanceof Failure?e.message:'Reader failed'}}));process.exitCode=1;}
}
