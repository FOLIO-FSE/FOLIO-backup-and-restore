import requests
import json
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("okapi_url", help="url of your FOLIO OKAPI endpoint.")
parser.add_argument("tenant_id", help="id of the FOLIO tenant")
parser.add_argument("okapi_token", help="the x-okapi-token")
args = parser.parse_args()
okapiHeaders = {'x-okapi-token': args.okapi_token,
                'x-okapi-tenant': args.tenant_id,
                'content-type': 'application/json'}

path = "/perms/permissions"
query = '?length=1000&query=(mutable==false)'
req = requests.get(args.okapi_url+path+query,
                   headers=okapiHeaders)
permission_resp = json.loads(req.text)
perms = [p['permissionName'] for p in permission_resp["permissions"]]
print("Total permissions: {}, Permissions fetched:{}"
      .format(permission_resp["totalRecords"], len(perms)))

perm_set = {"displayName": "All permissions",
            "mutable": True,
            "subPermissions": perms,
            "id": "08673a03-0f1b-4467-ba7c-b3d33c0e581a"}

print(args.okapi_url+path)
req = requests.post(args.okapi_url + path,
                   data=json.dumps(perm_set),
                   headers=okapiHeaders)
print(req.status_code)
print(req.text)
if str(req.status_code).startswith('4'):
    print(req.text)
