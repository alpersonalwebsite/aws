# Encryption: write data to a S3 bucket with server-side encryption enabled

## Create file to encrypt

```shell
echo "Hello World" >> hello-world.txt
```

## Create CMK in AWS KMS

```shell
aws kms create-key \
    --description "Development test key"
```

Example output:

```json
{
  "KeyMetadata": {
    "Origin": "AWS_KMS",
    "KeyId": "c9bd0eb7-cfe7-4e88-ad8d-12d130ce199d",
    "Description": "Development test key",
    "KeyManager": "CUSTOMER",
    "EncryptionAlgorithms": ["SYMMETRIC_DEFAULT"],
    "Enabled": true,
    "CustomerMasterKeySpec": "SYMMETRIC_DEFAULT",
    "KeyUsage": "ENCRYPT_DECRYPT",
    "KeyState": "Enabled",
    "CreationDate": 1593389383.576,
    "Arn": "arn:aws:kms:us-east-1:your-aws-account-id:key/c9bd0eb7-cfe7-4e88-ad8d-12d130ce199d",
    "AWSAccountId": "your-aws-account-id"
  }
}
```

## Change key policy

```shell
aws kms put-key-policy \
    --policy-name default \
    --key-id c9bd0eb7-cfe7-4e88-ad8d-12d130ce199d \
    --policy file://key-policy.json
```

_Note_: we are setting `your-user` as the `Administrator` and the only one with permissions to use this key.

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

## Write the file to S3

_Hint_: we are using server-side encryption with KMS, specifying a KMS customer master key (CMK)

```shell
aws s3 cp hello-world.txt s3://my-bucket-8200334565/ --sse aws:kms --sse-kms-key-id c9bd0eb7-cfe7-4e88-ad8d-12d130ce199d
```

Example output:

```shell
upload: ./hello-world.txt to s3://my-bucket-8200334565/hello-world.txt
```

Let's check the metadata of the uploaded object:

```shell
aws s3api head-object --bucket my-bucket-8200334565 --key hello-world.txt
```

Example output:

```json
{
  "AcceptRanges": "bytes",
  "ContentType": "text/plain",
  "LastModified": "Mon, 29 Jun 2020 00:25:59 GMT",
  "ContentLength": 12,
  "ETag": "\"5c962486475d8e4ac65d9495274b1a9d\"",
  "ServerSideEncryption": "aws:kms",
  "SSEKMSKeyId": "arn:aws:kms:us-east-1:your-aws-account-id:key/c9bd0eb7-cfe7-4e88-ad8d-12d130ce199d",
  "Metadata": {}
}
```

Great! We can see that Server Side Encryption is using `aws:kms` with the key that we provided: `arn:aws:kms:us-east-1:your-aws-account-id:key/c9bd0eb7-cfe7-4e88-ad8d-12d130ce199d`

**With this, only AWS users/roles that have permissions to use this KMS key will be able to read the object from S3.**

Try:

```shel
aws s3 cp s3://my-bucket-8200334565/hello-world.txt .
```

Example output:

```
download: s3://my-bucket-8200334565/hello-world.txt to ./hello-world.txt
```

Now, switch to any other user and try again...

```shel
aws s3 cp s3://my-bucket-8200334565/hello-world.txt .
```

Example output:

```shell
download failed: s3://my-bucket-8200334565/hello-world.txt to ./hello-world.txt An error occurred (AccessDenied) when calling the GetObject operation: Access Denied
```

Everything works as expected!

## Optional:

### Delete S3 bucket

First we need to `empty1` the bucket.
We are going to recursively delete all its objects

```shell
aws s3 rm --recursive s3://my-bucket-8200334565/
```

Now we can delete the bucket:

```shell
aws s3api delete-bucket --bucket my-bucket-8200334565 --region us-east-1
```

We can also use this short-cut to empty and delete:

```shell
aws s3 rb --force s3://your_bucket_name
```

### Schedule the deletion of the key

Note: We are going to use the smallest window period, 7 days.

```shell
aws kms schedule-key-deletion \
    --key-id arn:aws:kms:us-east-1:your-aws-account-id:key/c9bd0eb7-cfe7-4e88-ad8d-12d130ce199d \
    --pending-window-in-days 7
```

Example output:

```json
{
  "KeyId": "arn:aws:kms:us-east-1:your-aws-account-id:key/c9bd0eb7-cfe7-4e88-ad8d-12d130ce199d",
  "DeletionDate": 1594080000.0
}
```
