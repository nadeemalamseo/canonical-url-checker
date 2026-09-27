#!/usr/bin/env python3
"""Inspect canonical URL signals in HTML pages."""

from __future__ import annotations
import argparse, json, sys
from dataclasses import asdict, dataclass, field
from urllib.parse import urldefrag, urljoin, urlparse, urlunparse
import requests
from bs4 import BeautifulSoup

USER_AGENT="canonical-url-checker/1.0"
DEFAULT_TIMEOUT=15
DEFAULT_MAX_BYTES=2*1024*1024

@dataclass
class Issue:
    severity:str
    code:str
    message:str

@dataclass
class FetchInfo:
    requested_url:str
    status:int|None
    final_url:str|None
    redirect_chain:list[str]=field(default_factory=list)
    content_type:str|None=None
    bytes_read:int=0

@dataclass
class CanonicalResult:
    requested_url:str
    page:FetchInfo
    canonical_urls:list[str]
    canonical_absolute_urls:list[str]
    canonical_target:FetchInfo|None
    issues:list[Issue]
    summary:dict

def normalize_url(value:str,base_url:str|None=None)->str:
    absolute=urljoin(base_url or "",value.strip())
    absolute,_=urldefrag(absolute)
    p=urlparse(absolute)
    if p.scheme.lower() not in {"http","https"} or not p.netloc: raise ValueError(f"Not a valid HTTP(S) URL: {value}")
    host=(p.hostname or "").lower()
    if not host: raise ValueError(f"URL has no hostname: {value}")
    if p.port: host=f"{host}:{p.port}"
    return urlunparse((p.scheme.lower(),host,p.path or "/","",p.query,""))

def _fetch(session,url,timeout,max_bytes):
    response=session.get(url,timeout=timeout,allow_redirects=True,stream=True)
    chain=[url]
    for history in response.history:
        location=history.headers.get("Location")
        if location: chain.append(urljoin(history.url,location))
    if response.url not in chain: chain.append(response.url)
    chunks=[]; total=0
    for chunk in response.iter_content(chunk_size=64*1024):
        if not chunk: continue
        total+=len(chunk)
        if total>max_bytes:
            response.close()
            raise ValueError(f"Response exceeds the {max_bytes} byte safety limit.")
        chunks.append(chunk)
    body=b"".join(chunks)
    encoding=response.encoding or "utf-8"
    info=FetchInfo(url,response.status_code,response.url,chain,response.headers.get("Content-Type"),len(body))
    response.close()
    return info,body.decode(encoding,errors="replace")

def check_url(url,timeout=DEFAULT_TIMEOUT,max_bytes=DEFAULT_MAX_BYTES,fetch_target=True):
    session=requests.Session()
    session.headers.update({"User-Agent":USER_AGENT,"Accept":"text/html,application/xhtml+xml;q=0.9,*/*;q=0.1"})
    requested=normalize_url(url)
    page,html=_fetch(session,requested,timeout,max_bytes)
    issues=[]
    if page.status is None or page.status>=400: issues.append(Issue("error","http-error",f"Page returned HTTP {page.status}."))
    if len(page.redirect_chain)>2: issues.append(Issue("warning","redirects-before-page",f"Page required {len(page.redirect_chain)-1} redirect(s) before reaching the final URL."))
    if "html" not in (page.content_type or "").lower() and html: issues.append(Issue("warning","non-html-content-type","The response does not identify itself as HTML."))
    soup=BeautifulSoup(html,"html.parser")
    links=[]
    for tag in soup.find_all("link"):
        rel=tag.get("rel",[])
        rel=[str(x).lower() for x in rel] if isinstance(rel,list) else [str(rel).lower()]
        if "canonical" in rel:
            href=tag.get("href")
            links.append(href.strip() if isinstance(href,str) else "")
    absolute=[]
    for href in links:
        if not href:
            issues.append(Issue("error","empty-canonical","A canonical link element has an empty href."))
            continue
        try: absolute.append(normalize_url(href,page.final_url or requested))
        except ValueError: issues.append(Issue("error","invalid-canonical",f"Canonical href is not a valid HTTP(S) URL: {href}"))
    if not links: issues.append(Issue("error","missing-canonical","No canonical link element was found."))
    elif len(links)>1: issues.append(Issue("error","multiple-canonicals",f"Found {len(links)} canonical link elements."))
    if len(set(absolute))<len(absolute): issues.append(Issue("warning","duplicate-canonical","Multiple canonical elements resolve to the same URL."))
    target_info=None
    if absolute:
        canonical=absolute[0]
        final=normalize_url(page.final_url or requested)
        if urlparse(canonical).scheme=="http" and urlparse(final).scheme=="https": issues.append(Issue("warning","http-canonical-on-https","The page resolves over HTTPS but declares an HTTP canonical URL."))
        if urlparse(canonical).netloc!=urlparse(final).netloc: issues.append(Issue("warning","canonical-domain-differs","The canonical URL uses a different hostname from the final page URL."))
        issues.append(Issue("info","self-canonical","The canonical URL matches the normalized final page URL.") if canonical==final else Issue("info","cross-url-canonical","The canonical URL differs from the normalized final page URL."))
        if fetch_target and canonical!=final:
            target_info,target_html=_fetch(session,canonical,timeout,max_bytes)
            if target_info.status is None or target_info.status>=400: issues.append(Issue("error","canonical-target-error",f"Canonical target returned HTTP {target_info.status}."))
            if len(target_info.redirect_chain)>1: issues.append(Issue("warning","canonical-target-redirects",f"Canonical target redirects {len(target_info.redirect_chain)-1} time(s)."))
            if "html" not in (target_info.content_type or "").lower() and target_html: issues.append(Issue("warning","canonical-target-non-html","The canonical target does not identify itself as HTML."))
    summary={"errors":sum(i.severity=="error" for i in issues),"warnings":sum(i.severity=="warning" for i in issues),"info":sum(i.severity=="info" for i in issues),"canonical_count":len(links),"redirect_count":max(0,len(page.redirect_chain)-1)}
    return CanonicalResult(requested,page,links,absolute,target_info,issues,summary)

def result_to_dict(result): return asdict(result)
def exit_code(result): return 2 if result.summary["errors"] else 1 if result.summary["warnings"] else 0

def main(argv=None):
    parser=argparse.ArgumentParser(description="Inspect canonical URL implementation and related HTTP signals.")
    parser.add_argument("urls",nargs="+",help="one or more HTTP(S) page URLs")
    parser.add_argument("--json",action="store_true")
    parser.add_argument("--timeout",type=int,default=DEFAULT_TIMEOUT)
    parser.add_argument("--max-bytes",type=int,default=DEFAULT_MAX_BYTES)
    parser.add_argument("--no-target-fetch",action="store_true")
    args=parser.parse_args(argv)
    if args.timeout<=0 or args.max_bytes<=0: parser.error("--timeout and --max-bytes must be positive")
    results=[]; failed=False
    for url in args.urls:
        try: result=check_url(url,args.timeout,args.max_bytes,not args.no_target_fetch)
        except (ValueError,requests.RequestException) as exc:
            failed=True
            if args.json: results.append({"requested_url":url,"error":str(exc)})
            else: print(f"{url}: Error: {exc}",file=sys.stderr)
            continue
        results.append(result_to_dict(result))
        if not args.json:
            print(f"URL: {result.requested_url}\nHTTP: {result.page.status} | Final: {result.page.final_url}\nCanonical(s): {', '.join(result.canonical_absolute_urls) or 'none'}\nIssues: {len(result.issues)}")
            for issue in result.issues: print(f"- [{issue.severity}] {issue.code}: {issue.message}")
            print()
    if args.json: print(json.dumps(results,indent=2))
    return 2 if failed or any(x.get("summary",{}).get("errors",0) for x in results if isinstance(x,dict)) else 1 if any(x.get("summary",{}).get("warnings",0) for x in results if isinstance(x,dict)) else 0

if __name__=="__main__": raise SystemExit(main())
