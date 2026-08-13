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
    "KeyId": "YOUR-KMS-KEY-ID",
    "Description": "Development test key",
    "KeyManager": "CUSTOMER",
    "EncryptionAlgorithms": ["SYMMETRIC_DEFAULT"],
    "Enabled": true,
    "CustomerMasterKeySpec": "SYMMETRIC_DEFAULT",
    "KeyUsage": "ENCRYPT_DECRYPT",
    "KeyState": "Enabled",
    "CreationDate": 1593389383.576,
    "Arn": "arn:aws:kms:us-east-1:YOUR-ACCOUNT-ID:key/YOUR-KMS-KEY-ID",
    "AWSAccountId": "YOUR-ACCOUNT-ID"
  }
}
```

## Change key policy

```shell
aws kms put-key-policy \
    --policy-name default \
    --key-id YOUR-KMS-KEY-ID \
    --policy file://key-policy.json
```

_Note_: we are setting `your-user` as the `Administrator` and the only one with permissions to use this key.

## Create S3 bucket with server-side encryption enabled

```shell
aws s3api create-bucket --bucket YOUR-BUCKET-NAME --region us-east-1
```

Example output:

```shell
{
    "Location": "/YOUR-BUCKET-NAME"
}
```

## Configure server-side encryption for a bucket

```shell
aws s3api put-bucket-encryption \
    --bucket YOUR-BUCKET-NAME \
    --server-side-encryption-configuration '{"Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]}'
```

We can check the server-side encryption configuration...

```shell
aws s3api get-bucket-encryption \
    --bucket YOUR-BUCKET-NAME
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
aws s3 cp hello-world.txt s3://YOUR-BUCKET-NAME/ --sse aws:kms --sse-kms-key-id YOUR-KMS-KEY-ID
```

Example output:

```shell
upload: ./hello-world.txt to s3://YOUR-BUCKET-NAME/hello-world.txt
```

Let's check the metadata of the uploaded object:

```shell
aws s3api head-object --bucket YOUR-BUCKET-NAME --key hello-world.txt
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
  "SSEKMSKeyId": "arn:aws:kms:us-east-1:YOUR-ACCOUNT-ID:key/YOUR-KMS-KEY-ID",
  "Metadata": {}
}
```

Great! We can see that Server Side Encryption is using `aws:kms` with the key that we provided: `arn:aws:kms:us-east-1:YOUR-ACCOUNT-ID:key/YOUR-KMS-KEY-ID`

**With this, only AWS users/roles that have permissions to use this KMS key will be able to read the object from S3.**

Try:

```shel
aws s3 cp s3://YOUR-BUCKET-NAME/hello-world.txt .
```

Example output:

```
download: s3://YOUR-BUCKET-NAME/hello-world.txt to ./hello-world.txt
```

Now, switch to any other user and try again...

```shel
aws s3 cp s3://YOUR-BUCKET-NAME/hello-world.txt .
```

Example output:

```text
download failed: s3://YOUR-BUCKET-NAME/hello-world.txt to ./hello-world.txt An error occurred (AccessDenied) when calling the GetObject operation: Access Denied
```

Everything works as expected!

## Optional:

### Delete S3 bucket

First we need to `empty1` the bucket.
We are going to recursively delete all its objects

```shell
aws s3 rm --recursive s3://YOUR-BUCKET-NAME/
```

Now we can delete the bucket:

```shell
aws s3api delete-bucket --bucket YOUR-BUCKET-NAME --region us-east-1
```

We can also use this short-cut to empty and delete:

```shell
aws s3 rb --force s3://your_bucket_name
```

### Schedule the deletion of the key

Note: We are going to use the smallest window period, 7 days.

```shell
aws kms schedule-key-deletion \
    --key-id arn:aws:kms:us-east-1:YOUR-ACCOUNT-ID:key/YOUR-KMS-KEY-ID \
    --pending-window-in-days 7
```

Example output:

```json
{
  "KeyId": "arn:aws:kms:us-east-1:YOUR-ACCOUNT-ID:key/YOUR-KMS-KEY-ID",
  "DeletionDate": 1594080000.0
}
```
