NOTE! This is still work in progress. Please reach out for any questions.

# FOLIO-backup-and-restore
## Current functionality:
* Backs up and restores reference data and more from a FOLIO tenant after reset. What data that gets reset depends on configuration.
* Populates a permission set with every single permission there is. Usable for when you want to configure Admin rights to a FOLIO user without letting them be the Admin itself

## Caveats 
Not all data and all API:s are suitable for this script. The aim if mainly for parameter/reference data settings, and not the module's data. Please report anything you find that is not compatible. 
As of now, the following things are not restoreable:
* Permissions

In order to restore ERM data, you need to use a specific script: erm_backup_and_restore.py

## Requirements
Python 3. 
[Download instructions](https://www.python.org/downloads/)

## Usage
### Populate permissions
* Create a permission set in FOLIO through the UI, Copy the ID.
* run the following command:    
`python3 populatepermissions.py [okapi_url] [tenant_id] [x-okapi-token] [permission_set_id]`

### Backup regular reference data
* Note what data you want to backup (and restore)
* Make a copy of the settings.json.template file and rename it settings.json. For syntax help, see section below.
* Using the API reference (link below), populate the settings.json with the parameter settings you like to backup. 
* run the following command:
`python3 backup_and_restore.py backup [path_to_store_date] [okapi_url] [tenant_id] [x-okapi-token] [permission_set_id]`

### Restore regular reference data
Given you have backed up your data according to the above guide. Run the following command:
`python3 backup_and_restore.py restore [path_to_store_date] [okapi_url] [tenant_id] [x-okapi-token] [permission_set_id]`

### Backup ERM (Agreements and Licenses) reference data
This script backsup both the Business objects and the reference data in ERM
* run the following command:
`python3 erm_backup_and_restore.py backup [path_to_stored_date] [okapi_url] [tenant_id] [username] [password]`

### Restore  ERM (Agreements and Licenses) reference data
Given you have backed up your data according to the above guide. Run the following command:
`python3 erm_backup_and_restore.py restore [path_to_stored_date] [okapi_url] [tenant_id] [username] [password]`

## Reference
[FOLIO API reference](https://dev.folio.org/reference/api/)
## settings.json syntax
There is a template file in the repo that reflects the current syntax.

### Backup or Restore specific settings
add the argument `-s NAME_OF_SETTING` to the argument string and the script only runs the part from the settings.json that you specify.

Every element in the settings.json file must have the following properties:
### name
Name of the element containing the actual data. This is case sensitive. 
The name is also used to name the file containing the backup

### path
The path to where the get and the put/post is being made. Must start with a "/"

### insertMethod
The http method that is used to upload new data. Only post and put can be used. Case sensitive.

### saveEntireResponse
For some data, there is only one object to backup and restore. If so, set to true.

