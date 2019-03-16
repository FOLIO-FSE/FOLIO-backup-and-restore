import requests
import json
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("okapi_url", help="url of your FOLIO OKAPI endpoint.")
parser.add_argument("tenant_id", help="id of the FOLIO tenant")
parser.add_argument("okapi_token", help="the x-okapi-token")
parser.add_argument("perm_id", help="Id of set to get permissions")
args = parser.parse_args()
okapiHeaders = {'x-okapi-token': args.okapi_token,
                'x-okapi-tenant': args.tenant_id,
                'content-type': 'application/json'}

path = "/perms/permissions?length=1000&query=(mutable==false)"
req = requests.get(args.okapi_url+path,
                   headers=okapiHeaders)
permission_resp = json.loads(req.text)
perms = [p['permissionName'] for p in permission_resp["permissions"]
         if 'instance' in p['permissionName']]
print("Total permissions: {}, Permissions fetched:{}"
      .format(permission_resp["totalRecords"], len(perms)))
print(perms)
path = "/perms/permissions/{}".format(args.perm_id)
req = requests.get(args.okapi_url + path,
                   headers=okapiHeaders)
perm_set = json.loads(req.text)
perm_set["subPermissions"] = perms
del perm_set["childOf"]
del perm_set["grantedTo"]
del perm_set["dummy"]
req = requests.put(args.okapi_url + path,
                   data=json.dumps(perm_set),
                   headers=okapiHeaders)
print(req.status_code)
if(req.status_code == 422):
    print(req.text)
