# CloudTrail

## Create group and assign policies

```shell
aws iam create-group --group-name CloudTrailAdmins

# To list all the managed policies that start with AWSCloudTrail
aws iam list-policies --query 'Policies[?starts_with(PolicyName,`AWSCloudTrail`)]'

aws iam attach-group-policy --policy-arn arn:aws:iam::aws:policy/AWSCloudTrailFullAccess --group-name CloudTrailAdmins

aws iam attach-group-policy --policy-arn arn:aws:iam::aws:policy/IAMUserChangePassword --group-name CloudTrailAdmins
```

I am adding `arn:aws:iam::aws:policy/IAMUserChangePassword` so users can change their passwords.

## Create users and provide proper access

```shell
aws iam create-user --user-name CloudTrail

aws iam create-login-profile --user-name CloudTrail --password 'your-password' --password-reset-required
```

## Add users to groups

```shell
aws iam add-user-to-group --user-name CloudTrail --group-name CloudTrailAdmins
```

## Create and configure CloudTrail Trail

### Create the policy file

cloudtrail-S3PolicyForCloudTrail.json

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AWSCloudTrailAclCheck20150319",
      "Effect": "Allow",
      "Principal": {
        "Service": [
          "cloudtrail.amazonaws.com"
        ]
      },
      "Action": "s3:GetBucketAcl",
      "Resource": "arn:aws:s3:::your-trail-logs-bucket00112233"
    },
    {
      "Sid": "AWSCloudTrailWrite20150319",
      "Effect": "Allow",
      "Principal": {
        "Service": [
          "cloudtrail.amazonaws.com"
        ]
      },
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::your-trail-logs-bucket00112233/AWSLogs/your-admin-account-id/*",
      "Condition": {
        "StringEquals": {
          "s3:x-amz-acl": "bucket-owner-full-control"
        }
      }
    }
  ]
}
```

*Notes:*
* your-trail-logs-bucket00112233 -> bucket
* your-admin-account-id -> account id (master account)

*More info:* https://docs.aws.amazon.com/awscloudtrail/latest/userguide/create-s3-bucket-policy-for-cloudtrail.html


### Create S3 bucket

```shell
aws s3api create-bucket --bucket your-trail-logs-bucket00112233 --region us-east-1
```

Note: Bucket cannot contain uppercases, nor _ And must be unique.

### Create and add policy to the bucket

```shell
aws s3api put-bucket-policy --bucket your-trail-logs-bucket00112233 --policy  file://cloudtrail-S3PolicyForCloudTrail.json
```

### Create trail

```shell
aws cloudtrail create-trail --name Your_CloudTrail_Trail --s3-bucket-name your-trail-logs-bucket00112233
```


#### Create event selector

The following example creates an event selector for a trail named 'Your_CloudTrail_Trail' that includes all events, including read-only and write-only management events, and all data events for all Amazon S3 buckets and AWS Lambda functions in the AWS account:

```shell
aws cloudtrail put-event-selectors --trail-name Your_CloudTrail_Trail \ 
  --event-selectors '[{"ReadWriteType": "All","IncludeManagementEvents": true,"DataResources": [{"Type":"AWS::S3::Object", "Values": ["arn:aws:s3:::"]},{"Type": "AWS::Lambda::Function","Values": ["arn:aws:lambda"]}]}]'
```

### Start/stop logging

```shell
aws cloudtrail start-logging --name Your_CloudTrail_Trail

aws cloudtrail stop-logging --name Your_CloudTrail_Trail
```