import unittest
from unittest.mock import patch
from canonical_url_checker import check_url,exit_code,normalize_url

class FakeResponse:
    def __init__(self,url,body,status=200,content_type="text/html; charset=utf-8",history=None):
        self.url=url; self.status_code=status; self.headers={"Content-Type":content_type}; self.history=history or []; self.encoding="utf-8"; self._body=body.encode()
    def iter_content(self,chunk_size=65536): yield self._body
    def close(self): pass

class FakeSession:
    def __init__(self,responses): self.responses=responses; self.headers={}
    def get(self,url,**kwargs): return self.responses[url]

class CanonicalCheckerTests(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(normalize_url("HTTPS://Example.COM#section"),"https://example.com/")
        self.assertEqual(normalize_url("/page#x","https://example.com/base"),"https://example.com/page")
    def test_self_canonical(self):
        url="https://example.com/page"; session=FakeSession({url:FakeResponse(url,'<link rel="canonical" href="https://example.com/page">')})
        with patch("canonical_url_checker.requests.Session",return_value=session): result=check_url(url)
        self.assertEqual(result.summary["errors"],0); self.assertIn("self-canonical",{x.code for x in result.issues}); self.assertEqual(exit_code(result),0)
    def test_missing_canonical(self):
        url="https://example.com/page"; session=FakeSession({url:FakeResponse(url,"<html><head><title>Test</title></head></html>")})
        with patch("canonical_url_checker.requests.Session",return_value=session): result=check_url(url)
        self.assertIn("missing-canonical",{x.code for x in result.issues}); self.assertEqual(exit_code(result),2)
    def test_multiple_canonicals(self):
        url="https://example.com/page"; body='<link rel="canonical" href="/page"><link rel="canonical" href="/other">'
        with patch("canonical_url_checker.requests.Session",return_value=FakeSession({url:FakeResponse(url,body)})): result=check_url(url)
        self.assertIn("multiple-canonicals",{x.code for x in result.issues}); self.assertEqual(exit_code(result),2)
    def test_http_canonical_on_https(self):
        url="https://example.com/page"; body='<link rel="canonical" href="http://example.com/page">'
        with patch("canonical_url_checker.requests.Session",return_value=FakeSession({url:FakeResponse(url,body)})): result=check_url(url,fetch_target=False)
        self.assertIn("http-canonical-on-https",{x.code for x in result.issues})
    def test_different_target(self):
        page="https://example.com/page"; target="https://example.com/preferred"
        responses={page:FakeResponse(page,f'<link rel="canonical" href="{target}">'),target:FakeResponse(target,"<title>Target</title>")}
        with patch("canonical_url_checker.requests.Session",return_value=FakeSession(responses)): result=check_url(page)
        self.assertIsNotNone(result.canonical_target); self.assertEqual(result.canonical_target.status,200); self.assertIn("cross-url-canonical",{x.code for x in result.issues})
    def test_bad_target(self):
        page="https://example.com/page"; target="https://example.com/missing"; responses={page:FakeResponse(page,f'<link rel="canonical" href="{target}">'),target:FakeResponse(target,"not found",404)}
        with patch("canonical_url_checker.requests.Session",return_value=FakeSession(responses)): result=check_url(page)
        self.assertIn("canonical-target-error",{x.code for x in result.issues}); self.assertEqual(exit_code(result),2)
    def test_invalid_scheme(self):
        with self.assertRaises(ValueError): normalize_url("ftp://example.com/page")

if __name__=="__main__": unittest.main()
