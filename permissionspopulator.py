import requests
import json
import argparse


def make_request(headers, start, length):
    path = "/perms/permissions"
    query = '?query=(mutable==false)&length={}&start={}'
    print(args.okapi_url+path+query.format(length, start))
    req = requests.get(args.okapi_url+path+query.format(length, start),
                       headers=headers)
    if req.status_code != 200:
        print(req.text)
        raise ValueError("Request failed {}".format(req.status_code))
    return req


parser = argparse.ArgumentParser()
parser.add_argument("okapi_url", help="url of your FOLIO OKAPI endpoint.")
parser.add_argument("tenant_id", help="id of the FOLIO tenant")
parser.add_argument("okapi_token", help="the x-okapi-token")
args = parser.parse_args()
okapi_headers = {'x-okapi-token': args.okapi_token,
                 'x-okapi-tenant': args.tenant_id,
                 'content-type': 'application/json'}

page_size = 100
resp = make_request(okapi_headers, 1, page_size)
permission_resp = json.loads(resp.text)
perms = [p['permissionName'] for p in permission_resp["permissions"]]
print("Total permissions: {}, Permissions fetched:{}"
      .format(permission_resp["totalRecords"], len(perms)))


for start in range(page_size, permission_resp["totalRecords"], page_size):
    resp = make_request(okapi_headers, start, page_size)
    # print(resp.text)
    permission_resp = json.loads(resp.text)
    fetched_perms = [p['permissionName'] for p in permission_resp["permissions"]]
    perms.extend(fetched_perms)
    print("Total permissions: {}, Permissions fetched:{}"
          .format(permission_resp["totalRecords"], len(set(perms))))
# print(perms)
perm_set = {"displayName": "All permissions",
            "mutable": True,
            "subPermissions": list(set(perms)),
            "id": "08673a03-0f1b-4467-ba7c-b3d33c0e581a"}

path = "/perms/permissions"
print(args.okapi_url+path)
req = requests.post(args.okapi_url + path,
                    data=json.dumps(perm_set),
                    headers=okapi_headers)
print(req.status_code)
if str(req.status_code).startswith('4'):
    print(req.text)
