# CloudFormation Stack Rename

The following script will programmatically perform the following steps:

* Get resource import IDs from drift results
* Set all resources in the stack to retain on delete
* Delete the stack, whilst retaining the resource
* Create a new stack, importing the resources with their current state back into the stack

As the stack is recreated entirely, the history of the stack will not be retained. Note that not all stacks will support a stack rename, only those that exclusively contain importable types.

> :exclamation: This script is not thoroughly tested and you should attempt to use this on a non-critical resource before real-world usage as some resources refuse to re-import for a variety of reasons. I am not responsible for your data loss.

* This is the refactored build and works slightly differently

## Installation

To install please run the following:

```
./setup.sh
```
This will configure a python virtual env and install all dependant packages in there.


## Usage

```
$ ./stack_rename --help
usage: stack_rename [options]
Version: 0.1

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  -c CONFIG, --config CONFIG
                        specify the location of the config file, defaults to 'configs/config.yaml'
  -L, --auth            Authentication required, default False
  -M MFA, --mfa MFA     MFA device id - this should be available in your aws account
  -A PRIMARY_ACCOUNT, --primary-account PRIMARY_ACCOUNT
                        Your primary account, this should be your main primary account
  -S SWITCH_ACCOUNT, --switch-account SWITCH_ACCOUNT
                        AWS Secondary Account number to switch into
  -R ROLE_NAME, --role-name ROLE_NAME
                        AWS role name, this is used for switching
  -r REGION, --region REGION
                        Specify the aws region, defaults to "eu-west-2"
  -p PROFILE, --profile PROFILE
                        Specify the aws profile, defaults to "default"
  -s STACK_NAME, --stack_name STACK_NAME
                        Specify the current cloudformation stack name to import resources from
  -n NEW_STACK, --new_stack NEW_STACK
                        Specify the new cloudformation stack name
```

```
$ ./stack_recover --help
usage: stack_recover [options]
Version: 0.99beta1

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  -c CONFIG, --config CONFIG
                        specify the location of the config file, defaults to 'configs/config.yaml'
  -T TIME_STAMP, --time_stamp TIME_STAMP
                        Specify the timestamp for state, defaults to the value stored in state/current_state.json, the format should be: ddMonthyyyy-hhmmss, for example: 20Sep2022-184722
```

Typical usage is as follows:

```
source env/bin/activate # This is to enter into the virtual env
stack_rename -r <region> -s <old_stack_name> -n <new_stack_name> # without s3 support
stack_rename -r <region> -s <old_stack_name> -n <new_stack_name> -E -B <s3_bucket_name>
stack_recover # to run the recovery if the create changeset / execute changeset fails
deactivate # This exists the python virtual env
```

## Supported Functions
* s3 support - This utility now supports uploading to s3 bucket if template is greater than 50KB.
* Stack Recovery  - There is a stack_recover script included which tries to recover if the stack does fail to rename. A state snapshot is built as the stack_rename is run - It works by allowing you to remove resources which may have caused the failure, it is advised to closely monitor in aws console, resources that are removed will need to be manually removed before this can fully complete, as they are still retained in aws. 
* better drift handling
* ability to import resources that dont support drift
* ability to import resources that support multiple parameters for changeset creation.

There is a bunch of other updates made as well, your mileage may vary with this tool, it all depends on how complex the stack to rename is. Lambda functions unfortunately can be very difficult, even though technically they should work. 


## Supported Resources

The following resources are supported for stack rename (if other resources are within the stack, the script will attempt to recreate them in the new stack):

They are not listed here but can be viewed here: [cloudformation importable config](configs/cloudformation.yaml)

This is in line with what is listed here: [Former 2 - importable.txt](https://github.com/iann0036/former2/blob/master/util/importable.txt)

Please note if they are not listed above they will be recreated - The tool does warn about this and provides the option to exit.

## Known Issues

* Stacks that have an `Fn::ImportValue` reference against it - will warn about which other stacks are importing them and ask you to manually decouple
* Some transforms may affect the RetainPolicy - check if this affects you before executing.
* If using SAM or Lambdas this will most likely not work with errors like the following: `Validation failed for resource xxx with message #: required key [Code] not found` when trying to execute the changeset - be warned.
