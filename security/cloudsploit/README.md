# CloudSploit Scans

## Create IAM user `cloudsploit` and attach the policy `SecurityAudit`

```shell
aws iam create-user --user-name cloudsploit \
  --permissions-boundary arn:aws:iam::aws:policy/SecurityAudit
```

Note: You could create a role and attach the policy to that role or a group.

Example output:
```json
{
    "User": {
        "UserName": "cloudsploit", 
        "PermissionsBoundary": {
            "PermissionsBoundaryType": "Policy", 
            "PermissionsBoundaryArn": "arn:aws:iam::aws:policy/SecurityAudit"
        }, 
        "CreateDate": "2020-07-02T16:47:05Z", 
        "UserId": "AI*****Q**5R**********J4I", 
        "Path": "/", 
        "Arn": "arn:aws:iam::your-aws-account-id:user/cloudsploit"
    }
}
```

## Create access key for the user 

```shell
aws iam create-access-key --user-name cloudsploit
```

Example output:

```json
{
    "AccessKey": {
        "UserName": "cloudsploit", 
        "Status": "Active", 
        "CreateDate": "2020-07-02T16:48:35Z", 
        "SecretAccessKey": "****", 
        "AccessKeyId": "****"
    }
}
```

## Clone CloudSploit repo

```shell
git clone git@github.com:cloudsploit/scans.git
```

*Note*: You need to have `Node` and `npm`

## Install CloudSploit

```shell
cd scans
npm install
```

## Edit CloudSploit configuration 

Open `/Users/aldiaz/repo/aws/security/cloudsploit/scans/index.js`, uncomment and fill...

Example configuration:
```js
AWSConfig = {
 accessKeyId: '****',
 secretAccessKey: '****',
 //sessionToken: '',
 region: 'us-east-1'
};
```

## Run CloudSploit

```shell
node index.js
```
... alternatively you can `output results in all supported formats for any test that is not OK`

```shell
node index.js --console --junit=./out.xml --csv=./out.csv --ignore-ok
```