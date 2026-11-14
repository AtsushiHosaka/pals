"""Deterministic auth boundary tests; no real credentials, Cognito or paid requests."""
import json
import subprocess
import os
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]

SETUP = r'''
const assert = require('node:assert/strict');
const helper = require(process.argv[1]);
const issuer = 'https://cognito-idp.ap-northeast-1.amazonaws.com/ap-northeast-1_Fixture';
const client = 'fixtureclient', user = 'fixtureuser';
const jwt = claims => 'e30.' + Buffer.from(JSON.stringify(claims)).toString('base64url') + '.c2ln';
const access = extra => jwt({token_use:'access',iss:issuer,sub:user,client_id:client,
  exp:Math.floor(Date.now()/1000)+1800,...extra});
const prefix = `CognitoIdentityServiceProvider.${client}.`;
const storage = {
  [prefix+'LastAuthUser']:user,
  [prefix+user+'.idToken']:jwt({token_use:'id',iss:issuer,sub:user,aud:client,exp:1}),
  [prefix+user+'.accessToken']:access(),
  [prefix+user+'.refreshToken']:'FIXTURE-REFRESH-VALUE-NOT-A-CREDENTIAL',
  [prefix+user+'.deviceKey']:'ap-northeast-1_fixture-device',
};
const init = {auth_origin:'https://cognito-idp.ap-northeast-1.amazonaws.com',
  refresh_policy:{region:'ap-northeast-1',account_id:'123456789012'}};
const session = {session_storage:storage};
const descriptor = helper.refreshDescriptor(init,session);
const body = {AuthFlow:'REFRESH_TOKEN_AUTH',ClientId:client,
  AuthParameters:{REFRESH_TOKEN:storage[prefix+user+'.refreshToken']}};
const req = (b=body,over={}) => ({method:()=> 'POST',
  headers:()=>({'x-amz-target':'AWSCognitoIdentityProviderService.InitiateAuth'}),
  postData:()=>JSON.stringify(b), redirectedFrom:()=>null,...over});
const url = new URL(init.auth_origin+'/');
'''


class RefreshBrowserTests(unittest.TestCase):
    def node(self, source):
        result = subprocess.run(['node', '-e', SETUP + source,
                                 str(HERE / 'release-post-request-browser.cjs')],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, '')

    def test_expired_id_session_allows_only_its_normal_refresh(self):
        self.node(r'''
assert.equal(helper.allowedRefresh(req(),url,init,descriptor),true);
assert.equal(helper.allowedRefresh(req({...body,AuthParameters:{...body.AuthParameters,
  DEVICE_KEY:storage[prefix+user+'.deviceKey']}}),url,init,descriptor),true);
assert.equal(helper.allowedRefresh(req({...body,AuthParameters:{...body.AuthParameters,
  DEVICE_KEY:null}}),url,init,{...descriptor,device:undefined}),true);
assert.equal(helper.allowedRefresh(req({...body,AuthParameters:{...body.AuthParameters,
  DEVICE_KEY:null}}),url,init,descriptor),false);
assert.equal(helper.freshBearer('Bearer '+access(),descriptor),true);
assert.equal(helper.freshBearer('Bearer '+access({exp:1}),descriptor),false);
assert.equal(helper.freshBearer('Bearer '+access({sub:'another'}),descriptor),false);
assert.equal(helper.freshBearer('Bearer '+access({client_id:'another'}),descriptor),false);
assert.equal(helper.freshBearer('Bearer '+access({iss:'https://elsewhere.invalid'}),descriptor),false);
assert.equal(helper.freshBearer('Bearer '+access({token_use:'id'}),descriptor),false);
assert.equal(helper.freshBearer('Bearer '+jwt(null),descriptor),false);
''')

    def test_other_auth_flows_credentials_and_redirects_are_refused(self):
        self.node(r'''
for (const b of [{...body,AuthFlow:'USER_PASSWORD_AUTH'}, {...body,ClientId:'another'},
  {...body,ClientMetadata:{}}, {...body,AuthParameters:{REFRESH_TOKEN:'another'}},
  {...body,AuthParameters:{...body.AuthParameters,DEVICE_KEY:'another'}},
  {...body,AuthParameters:{...body.AuthParameters,SECRET_HASH:'fixture'}}]) {
  assert.equal(helper.allowedRefresh(req(b),url,init,descriptor),false);
}
for (const target of [init.auth_origin+'/?query=1',init.auth_origin+'/oauth2/token',
  'https://elsewhere.invalid/',init.auth_origin+'/#fragment']) {
  assert.equal(helper.allowedRefresh(req(),new URL(target),init,descriptor),false);
}
for (const over of [{method:()=> 'GET'}, {redirectedFrom:()=> ({})},
  {headers:()=>({'x-amz-target':'AWSCognitoIdentityProviderService.GetTokensFromRefreshToken'})},
  {postData:()=>'{bad'}]) {
  assert.equal(helper.allowedRefresh(req(body,over),url,init,descriptor),false);
}
assert.equal(helper.allowedRefresh(req(),url,init,null),false);
''')

    def test_untrusted_session_cannot_choose_authority_or_another_client(self):
        self.node(r'''
const reject = s => assert.throws(()=>helper.refreshDescriptor(init,{session_storage:s}),
  error=>error.message==='refresh_session_invalid');
reject({...storage,[prefix+user+'.idToken']:jwt({token_use:'id',iss:issuer,sub:user,aud:'other'})});
reject({...storage,[prefix+user+'.accessToken']:access({iss:issuer+'-other'})});
reject({...storage,[prefix+'LastAuthUser']:'other'});
reject({...storage,'CognitoIdentityServiceProvider.other.LastAuthUser':user});
assert.throws(()=>helper.refreshDescriptor({...init,auth_origin:'https://elsewhere.invalid'},session),
  error=>error.message==='refresh_authority_invalid');
assert.equal(helper.refreshDescriptor({...init,refresh_policy:null},session),null);
''')

    def test_guard_failure_or_noncanonical_output_denies_refresh(self):
        self.node(r'''
const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const temp=fs.mkdtempSync(path.join(os.tmpdir(),'pals-refresh-policy-test-'));
try {
  const guard=path.join(temp,'guard.cjs');
  init.refresh_policy.python=process.execPath;init.refresh_policy.guard=guard;
  for (const source of ['process.exit(2)', 'process.stdout.write("{}")',
    'process.stdout.write(JSON.stringify({allowed:true,extra:true}))']) {
    fs.writeFileSync(guard,source);
    assert.throws(()=>helper.checkRefreshPolicy(init,descriptor),
      error=>error.message==='refresh_policy_not_verified');
  }
  fs.writeFileSync(guard,'let b="";process.stdin.on("data",x=>b+=x);process.stdin.on("end",()=>{'+
    'const d=JSON.parse(b);if(Object.keys(d).sort().join(",")!=="account_id,client_id,region,user_pool_id")process.exit(2);'+
    'process.stdout.write(\'{"allowed":true}\');});');
  helper.checkRefreshPolicy(init,descriptor);
} finally {fs.rmSync(temp,{recursive:true,force:true});}
''')

    def test_expired_session_app_refresh_precedes_fresh_product_read(self):
        # The fake browser models app traffic only; the real helper controls routing/capture.
        # A baseline helper can be supplied for a red run without changing production code.
        script = SETUP.replace("const descriptor = helper.refreshDescriptor(init,session);", "") + r'''
const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const temp=fs.mkdtempSync(path.join(os.tmpdir(),'pals-refresh-browser-test-'));
const fresh=access(), expired=access({exp:1});
const fakeBrowser=`
const assert=require('node:assert/strict');
exports.chromium={launch:async()=>({close:async()=>{},newContext:async()=>{
  let routeHandler, listener;
  return {addInitScript:async()=>{},route:async(_p,h)=>{routeHandler=h;},newPage:async()=>({
    setDefaultTimeout(){},on(_e,h){listener=h;},off(){listener=null;},
    waitForTimeout:async()=>{},goto:async()=>{
      let admitted=false, fetched=0;
      const request={method:()=> 'POST',url:()=> '${init.auth_origin}/',
        headers:()=>({'x-amz-target':'AWSCognitoIdentityProviderService.InitiateAuth'}),
        postData:()=> '${JSON.stringify(body)}',redirectedFrom:()=>null};
      const route={request:()=>request,abort:async()=>{},continue:async()=>{admitted=true;},
        fetch:async options=>{assert.equal(options.maxRedirects,0);fetched++;return {status:()=>200};},
        fulfill:async()=>{admitted=true;}};
      await routeHandler(route);
      assert.equal(admitted,true,'normal refresh was blocked');
      admitted=false;await routeHandler(route);assert.equal(admitted,false,'second refresh admitted');
      assert.equal(fetched,1);
      for(const token of ['${expired}','${fresh}']) if(listener) listener({method:()=> 'GET',
        url:()=> 'https://api.example.test/v1/chats',headers:()=>({authorization:'Bearer '+token})});
    }
  })};
}})};`;
try {
  const stub=path.join(temp,'node_modules','playwright');fs.mkdirSync(stub,{recursive:true});
  fs.writeFileSync(path.join(stub,'index.js'),fakeBrowser);
  const guard=path.join(temp,'guard.cjs');fs.writeFileSync(guard,'process.stdout.write(\'{"allowed":true}\')');
  init.refresh_policy.python=process.execPath;init.refresh_policy.guard=guard;
  Object.assign(init,{web_root:temp,web_origin:'https://web.example.test',api_origin:'https://api.example.test',start_ms:1000});
  helper.bearerFromBrowser(init,session).then(value=>{
    assert.equal(value,'Bearer '+fresh);fs.rmSync(temp,{recursive:true,force:true});
  },()=>{fs.rmSync(temp,{recursive:true,force:true});process.exit(2);});
} catch {fs.rmSync(temp,{recursive:true,force:true});process.exit(2);}
'''
        helper = os.environ.get('PALS_REFRESH_TEST_HELPER', str(HERE / 'release-post-request-browser.cjs'))
        result = subprocess.run(['node', '-e', script, helper], capture_output=True, text=True, timeout=30)
        self.assertEqual((result.returncode, result.stdout), (0, ''), result.stderr)


if __name__ == '__main__':
    unittest.main()
