# Serverless App: Lambda and S3 server side encryption

We are going to create a small application to store files (objects) in S3 with SSE KMS (CMK). 

## Create Lambdas roles

```shell
aws iam create-role --role-name encryption-lambda-write --assume-role-policy-document file://trust-policy.json

aws iam create-role --role-name encryption-lambda-read --assume-role-policy-document file://trust-policy.json
```

Example output:

```json
{
    "Role": {
        "AssumeRolePolicyDocument": {
            "Version": "2012-10-17", 
            "Statement": [
                {
                    "Action": "sts:AssumeRole", 
                    "Effect": "Allow", 
                    "Principal": {
                        "Service": "lambda.amazonaws.com"
                    }
                }
            ]
        }, 
        "RoleId": "AROAYQ5AHLCL2D6HSXJLA", 
        "CreateDate": "2020-06-29T21:19:00Z", 
        "RoleName": "encryption-lambda-read", 
        "Path": "/", 
        "Arn": "arn:aws:iam::your-aws-account-id:role/encryption-lambda-read"
    }
}

```

##  Attach inline policies to the roles

```shell
aws iam put-role-policy --role-name encryption-lambda-write \
  --policy-name S3PutObject \
  --policy-document file://encryption-lambda-write-S3-putObject-policy.json
```

```shell
aws iam put-role-policy --role-name encryption-lambda-read \
  --policy-name S3GetObject \
  --policy-document file://encryption-lambda-read-S3-getObject-policy.json
```

## Create CMK and allow the roles to use the key for encryption operations

```shell
aws kms create-key \
    --description "Development test key"
```

Example output:

```json
{
    "KeyMetadata": {
        "Origin": "AWS_KMS", 
        "KeyId": "c556d894-361e-437a-8890-e70fa95a835c", 
        "Description": "Development test key", 
        "KeyManager": "CUSTOMER", 
        "EncryptionAlgorithms": [
            "SYMMETRIC_DEFAULT"
        ], 
        "Enabled": true, 
        "CustomerMasterKeySpec": "SYMMETRIC_DEFAULT", 
        "KeyUsage": "ENCRYPT_DECRYPT", 
        "KeyState": "Enabled", 
        "CreationDate": 1593465813.221, 
        "Arn": "arn:aws:kms:us-east-1:your-aws-account-id:key/c556d894-361e-437a-8890-e70fa95a835c", 
        "AWSAccountId": "your-aws-account-id"
    }
}
```

### Create alias for our CMK

*Hint*: Remember Alias must start with the prefix "alias/"

```shell
aws kms create-alias \
    --alias-name alias/encryption-test \
    --target-key-id c556d894-361e-437a-8890-e70fa95a835c
```

## Change key policy

```shell
aws kms put-key-policy \
    --policy-name default \
    --key-id c556d894-361e-437a-8890-e70fa95a835c \
    --policy file://key-policy.json
```

## Create S3 bucket with server-side encryption enabled

```shell
aws s3api create-bucket --bucket my-bucket-8200334565 --region us-east-1
```

Example output:

```shell
{
    "Location": "/my-bucket-8200334565"
}
```

## Configure server-side encryption for a bucket

```shell
aws s3api put-bucket-encryption \
    --bucket my-bucket-8200334565 \
    --server-side-encryption-configuration '{"Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]}'
```

We can check the server-side encryption configuration...

```shell
aws s3api get-bucket-encryption \
    --bucket my-bucket-8200334565
```

Example output:

```json
{
    "ServerSideEncryptionConfiguration": {
        "Rules": [
            {
                "ApplyServerSideEncryptionByDefault": {
                    "SSEAlgorithm": "AES256"
                }
            }
        ]
    }
}

```

## Create Lambdas

### Create WRITE lambda

```shell
aws lambda create-function \
    --function-name encryption-lambda-write \
    --runtime nodejs12.x \
    --zip-file fileb://encryption-lambda-write.zip \
    --handler encryption-lambda-write.handler \
    --role arn:aws:iam::your-aws-account-id:role/encryption-lambda-write

```

Then, zip your lambda:

```shell
zip -r encryption-lambda-write.zip encryption-lambda-write.js
```

### Create READ lambda

```shell
aws lambda create-function \
    --function-name encryption-lambda-read \
    --runtime nodejs12.x \
    --zip-file fileb://encryption-lambda-read.zip \
    --handler encryption-lambda-read.handler \
    --role arn:aws:iam::your-aws-account-id:role/encryption-lambda-read
```

Then, zip your lambda:

```shell
zip -r encryption-lambda-read.zip encryption-lambda-read.js
```

## Invoke Lambdas

### Invoke WRITE lambda

```shell
aws lambda invoke --function-name encryption-lambda-write --payload '{}' /dev/stdout
```

---

## Optional

### Delete roles

First, we need to detach all policies (in this case, the one we added)

```shell
aws iam delete-role-policy --role-name encryption-lambda-read --policy-name S3GetObject

aws iam delete-role-policy --role-name encryption-lambda-write --policy-name S3PutObject
```

Then...

```shell 
aws iam delete-role --role-name encryption-lambda-read 

aws iam delete-role --role-name encryption-lambda-write 
```

### Schedule the deletion of the key

Note: We are going to use the smallest window period, 7 days.

```shell
aws kms schedule-key-deletion \
    --key-id arn:aws:kms:us-east-1:your-aws-account-id:key/c556d894-361e-437a-8890-e70fa95a835c \
    --pending-window-in-days 7
```

### Delete S3 bucket

```shell
aws s3 rb --force s3://my-bucket-8200334565
```

Example output:

```shell
delete: s3://my-bucket-8200334565/hello-world.txt
remove_bucket: my-bucket-8200334565
```

### Delete Lambdas

```shell
aws lambda delete-function --function-name encryption-lambda-read

aws lambda delete-function --function-name encryption-lambda-write
```