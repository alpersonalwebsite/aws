# SSM: How to securely connect to an EC2 instance in AWS

## Instance Profile

We are going to create an instance role with the policy `AmazonSSMManagedInstanceCore` and attach it to the EC2 instances.
For this, we first create the `role`, then the `instance profile` and finally the EC2 instance (where we associate the instance profile)

The `security group` of the EC2 instance should not allow inbound connections.

*Note:* `AmazonSSMManagedInstanceCore` allows the SSM agent that is installed on the instance to work with AWS System Manager service.

## IAM role to assume

We also need the `IAM role` that we will use to login into the instance.

This `role` carries **no managed policies**, and that is a change from how it was first
written. It used to attach two:

```text
AmazonEC2ReadOnlyAccess   read on EVERY EC2 resource in the account
AmazonSSMReadOnlyAccess   ssm:Describe*, ssm:Get*, ssm:List* on EVERY SSM resource,
                          which includes reading unrelated Parameter Store values
```

Both are far wider than starting a session on one instance needs, so everything is enumerated
in a single inline policy instead:

| action | scoped to |
| --- | --- |
| `ssm:StartSession` | this instance **and** `document/SSM-SessionManagerRunShell` |
| `ssmmessages:OpenDataChannel` | `session/${aws:userid}-*` |
| `ssm:TerminateSession`, `ssm:ResumeSession` | `session/${aws:userid}-*` |
| `ec2:DescribeInstances`, `ssm:DescribeInstanceInformation`, `ssm:DescribeInstanceProperties`, `ssm:DescribeSessions`, `ssm:GetConnectionStatus` | `*`, because AWS defines these without a resource type |

`StartSession` needs the session **document** as well as the instance: with only the instance
ARN the command fails, because Session Manager reads its configuration from
`SSM-SessionManagerRunShell`.

`${aws:userid}` rather than `${aws:username}`, which the first version used. Per the IAM
condition-key reference, `aws:username` is "always included in the request context for IAM
users" while "requests that are made using ... IAM roles do not include this key". This role
exists to be assumed, so `aws:username` is never present and terminate/resume could never
match their own session.

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

**The role name is generated, not fixed.** `SSM.yml` deliberately omits `RoleName` so the
stack can be deployed more than once, so take the name from the stack's `LoginRoleArn` output
rather than searching for a literal:

```shell
aws cloudformation describe-stacks --stack-name ssm \
  --query "Stacks[0].Outputs[?OutputKey=='LoginRoleArn'].OutputValue" --output text
```

1. Go to IAM > Roles and search for the role name from that ARN (the part after `role/`)

2. Click on the link of the key `Give this link to users who can switch roles in the console`
Example: `https://signin.aws.amazon.com/switchrole?roleName=<the-generated-name>&account=myOrganization`

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

[profile ssm-login]
region = us-east-1
role_arn = <the LoginRoleArn output from the stack>
source_profile = default
```

2. List EC2 instances

```shell
aws ec2 describe-instances --profile ssm-login
```

3. Try something outside the scope of the role

Anything outside what we are allowing should be denied. 

Let's try to list users.

```shell
aws iam list-users --profile ssm-login
```

Result:
```
An error occurred (AccessDenied) when calling the ListUsers operation: User: arn:aws:sts::YOUR-ACCOUNT-ID:assumed-role/<the-generated-name>/botocore-session-********** is not authorized to perform: iam:ListUsers on resource: arn:aws:iam::YOUR-ACCOUNT-ID:user/
```

Great! Everything works as expected!




