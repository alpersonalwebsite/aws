# Handling permissions for Users

1. Create user 

```shell
aws iam create-user --user-name test-us-1
```

Example output:
```json
{
    "User": {
        "UserName": "test-us-1", 
        "Path": "/", 
        "CreateDate": "2020-06-22T16:42:13Z", 
        "UserId": "***", 
        "Arn": "arn:aws:iam::your-aws-account-id:user/test-us-1"
    }
}
```

2. Create a virtual MFA device

```shell
aws iam create-virtual-mfa-device --virtual-mfa-device-name test-us-1-virtual-mfa --outfile /Users/your-user/Downloads/test-us-1-virtual-mfa-QRCode.png --bootstrap-method QRCodePNG
```

Example output:
```json
{
    "VirtualMFADevice": {
        "SerialNumber": "arn:aws:iam::your-aws-account-id:mfa/test-us-1-virtual-mfa"
    }
}
```

3. Enable MFA in the user account

First, open your `Authenticator`, for example: `Google Authenticator` and scan the QR code `QRCode.png`. This will add a new entry to your GA list. In this case, `Amazon Web Services (test-us-1-virtual...)`

Then, add 2 codes...

```shell
aws iam enable-mfa-device --user-name test-us-1 --serial-number arn:aws:iam::your-aws-account-id:mfa/test-us-1-virtual-mfa --authentication-code-1 360431 --authentication-code-2 874344
```

Then, we are going to list all MFA devices for our user and ensure 

```shell
aws iam list-mfa-devices --user-name test-us-1
```

We should see something like:
```json
{
    "MFADevices": [
        {
            "UserName": "test-us-1", 
            "SerialNumber": "arn:aws:iam::your-aws-account-id:mfa/test-us-1-virtual-mfa", 
            "EnableDate": "2020-06-22T17:05:12Z"
        }
    ]
}
```

## Option 1: API keys and policy attached to the user or group where the user belongs

1. Create Access key

```shell
aws iam create-access-key --user-name test-us-1
```

Example output:
```json
{
    "AccessKey": {
        "UserName": "test-us-1", 
        "Status": "Active", 
        "CreateDate": "2020-06-22T17:34:42Z", 
        "SecretAccessKey": "***", 
        "AccessKeyId": "***"
    }
}
```

2. Assign policy to user

First, let's check if the user has current policies attached

```shell
aws iam list-attached-user-policies --user-name test-us-1
```

In our case, we expect the following response
```
{
    "AttachedPolicies": []
}
```

Let's assign the `AWS Managed policy` > `AmazonS3ReadOnlyAccess`

```shell
aws iam attach-user-policy --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess --user-name test-us-1
```

Now, let's check again...
```shell
aws iam list-attached-user-policies --user-name test-us-1
```

Result:
```json
{
    "AttachedPolicies": [
        {
            "PolicyName": "AmazonS3ReadOnlyAccess", 
            "PolicyArn": "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
        }
    ]
}
```

Great! So, this user, should be able to use his `Access key` and `Secret Access Key` to retrieve objects in S3 buckets. 

Let's check...

List all buckets: `aws s3api list-buckets`
List all object inside a bucket `aws s3api list-objects --bucket your-bucket --query 'Contents[].{Key: Key, Size: Size}'`

Now, if we try: `aws iam list-users` we should see...

```shell
An error occurred (AccessDenied) when calling the ListUsers operation: User: arn:aws:iam::your-aws-account-id:user/test-us-1 is not authorized to perform: iam:ListUsers on resource: arn:aws:iam::your-aws-account-id:user/
```

## Option 2: Create a role the user can utilize

1. Create IAM policy

```shell
aws iam create-policy --policy-name test-user-policy --policy-document file://policy.json
```

Result:
```json
{
    "Policy": {
        "PolicyName": "test-user-policy", 
        "PermissionsBoundaryUsageCount": 0, 
        "CreateDate": "2020-06-22T18:09:45Z", 
        "AttachmentCount": 0, 
        "IsAttachable": true, 
        "PolicyId": "***", 
        "DefaultVersionId": "v1", 
        "Path": "/", 
        "Arn": "arn:aws:iam::your-aws-account-id:policy/test-user-policy", 
        "UpdateDate": "2020-06-22T18:09:45Z"
    }
}
```

2. Assign policy to user

First, let's check if the user has current policies attached

```shell
aws iam list-attached-user-policies --user-name test-us-1
```

In our case, we expect the following response
```
{
    "AttachedPolicies": []
}
```

Let's assign the policy `test-user-policy` that we created in the previous step.

```shell
aws iam attach-user-policy --policy-arn arn:aws:iam::your-aws-account-id:policy/test-user-policy --user-name test-us-1
```

And... Ensure the user now has the proper policy

```shell
aws iam list-attached-user-policies --user-name test-us-1
```

Result:

```json
{
    "AttachedPolicies": [
        {
            "PolicyName": "test-user-policy", 
            "PolicyArn": "arn:aws:iam::your-aws-account-id:policy/test-user-policy"
        }
    ]
}
```

*Note:* we need to associate two policies with the role: a trust policy that controls who can assume the role, and an access policy that controls which actions can be performed on which resources by assuming the role.

3. Create an IAM role and attach the previously created policy
(with the name you specified in your policy's resource)

```shell
aws iam create-role --role-name test-user-role --assume-role-policy-document file://policy.json
```


### Optionals...

8. Detach a policy from a user

```shell
aws iam detach-user-policy --user-name test-us-1 --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess
```

9. Remove MFA device

First we need to deactivate, then delete.

```shell
aws iam deactivate-mfa-device --user-name test-us-1 --serial-number arn:aws:iam::your-aws-account-id:mfa/test-us-1-virtual-mfa

aws iam delete-virtual-mfa-device --serial-number arn:aws:iam::your-aws-account-id:mfa/test-us-1-virtual-mfa
```

10. Delete user

<!--
Hacer
Eliminar usuarios
Eliminar virtual devices
Crear usuario, crear MFA pero no assignar y ver que apaece cuando listo
Delete policy
Delete role
-->