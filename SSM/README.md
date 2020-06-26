# SSM: How to securely connect to an EC2 instance in AWS

## Instance Profile

We are going to create an instance role with the policy `AmazonSSMManagedInstanceCore` and attach it to the EC2 instances.
For this, we first create the `role`, then the `instance profile` and finally the EC2 instance (where we associate the instance profile)

The `security group` of the EC2 instance should not allow inbound connections.

*Note:* `AmazonSSMManagedInstanceCore` allows the SSM agent that is installed on the instance to work with AWS System Manager service.

## IAM role to assume

We also need the `IAM role` that we will use to login into the instance.

This `role` will have the following managed policies...

```
AmazonEC2ReadOnlyAccess
AmazonSSMReadOnlyAccess
```

... plus, a custom policy to start an terminate sessions (SSM)

```
Effect: Allow
Action ssm:StartSession
Resource: EC2-arn

Effect: Allow
Action: ssm:TerminateSession
Resource: arn:aws:ssm:*:*:session/${aws:username}-*
```

## Creating SSM stack
```terminal
aws cloudformation create-stack --stack-name SSM --template-body file://SSM.yml --capabilities CAPABILITY_NAMED_IAM
```

## Update SSM stack
```terminal
aws cloudformation update-stack --stack-name SSM --template-body file://SSM.yml --capabilities CAPABILITY_NAMED_IAM
```

## Deleting stacks
```terminal
aws cloudformation delete-stack --stack-name SSM
```

## Assuming the role

### AWS console

1. Go to IAM > Roles > Search for IAMroleToLoginIntoInstance and select it

2. Click on the link of the key `Give this link to users who can switch roles in the console`
Example: https://signin.aws.amazon.com/switchrole?roleName=IAMroleToLoginIntoInstance&account=myOrganization

3. On the new window, click on `Switch Role`

4. Go to EC2 > Running instances

5. If you want to log into the instance, go to `Systems Manager`

6. Click on `Session Manager`

7. Click on `Start Session`

8. You will all the instances available for your role

9. Select the instance and click on `Start Session`

10. Once you finish, click on `Terminate`

11. Select the instance and click on `Terminate`

### Programmatically

1. Add to ` ~/.aws/config`

```
[default]
region = us-east-1

[profile IAMroleToLoginIntoInstance]
region = us-east-1
role_arn = arn:aws:iam::your-aws-account-id:role/IAMroleToLoginIntoInstance
source_profile = default
```

2. List EC2 instances

```shell
aws ec2 describe-instances --profile IAMroleToLoginIntoInstance
```

3. Try something outside the scope of the role

Anything outside what we are allowing should be denied. 

Let's try to list users.

```shell
aws iam list-users --profile IAMroleToLoginIntoInstance
```

Result:
```
An error occurred (AccessDenied) when calling the ListUsers operation: User: arn:aws:sts::your-aws-account-id:assumed-role/IAMroleToLoginIntoInstance/botocore-session-********** is not authorized to perform: iam:ListUsers on resource: arn:aws:iam::your-aws-account-id:user/
```

Great! Everything works as expected!




