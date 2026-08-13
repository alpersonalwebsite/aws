# AWS

Working notes from mid-2020, six topics, each a directory or a markdown file with the commands
and their recorded output. Not an application: the point is the walkthroughs and the policy
documents beside them.

| | |
| --- | --- |
| [`security/`](security/) | A security training project: deploy a deliberately vulnerable stack, attack it, then harden it. **The infrastructure there is intentionally insecure. See the caution below.** |
| [`encryption/`](encryption/) | Server-side encryption with a KMS customer managed key, by CLI |
| [`encryption/application/`](encryption/application/) | The same thing as two Lambdas, one writing and one reading |
| [`SSM/`](SSM/) | An EC2 instance reachable only through Session Manager: no port 22, no key pair |
| [`IAM-role-for-users/`](IAM-role-for-users/) | Role switching for IAM users, with MFA required |
| [`cloudtrail.md`](cloudtrail.md) | CloudTrail to an S3 bucket, with the bucket policy CloudTrail needs |
| [`cloudwatch-alarms-billing.md`](cloudwatch-alarms-billing.md) | A billing alarm and the SNS topic it notifies |

## ⚠️ `security/` is deliberately insecure

That directory is training material. `security/infrastructure/app.yml` opens **all protocols
inbound from `0.0.0.0/0`** on the application instance, plus SSH on 22 and ports 5000 and 80, all
to the internet. `security/infrastructure/s3.yml` creates three buckets, one named
`secret-recipes`, with no encryption at rest, no public-access block and no versioning.

Four rules in that file match `IpProtocol: -1` with `0.0.0.0/0`, but only one is ingress. The
other three are egress, which is the default for every security group and is not an exposure.

**None of that has been fixed, on purpose.** The vulnerabilities are what the exercises attack,
and the hardening exercise deliberately fixes SSH inside `sshd_config` on the running instance
rather than in the template. Every file in there now carries a header saying so, because the
templates are otherwise indistinguishable from a reference someone might copy.

Everything outside `security/` is meant to be sound, and is where the corrections below apply.

## What changed, and why

**A demo about encryption was printing the plaintext to the logs.**
`encryption/application/encryption-lambda-read.js` ended with

```js
console.log(data.Body.toString('utf-8'))
```

so the last act of a function whose entire purpose is to show that an object is encrypted at
rest with KMS was to write the decrypted content into CloudWatch Logs. Logs are a different
boundary from the bucket: not encrypted with that key, readable by anyone holding
`logs:FilterLogEvents`, and persisting independently of the object. It now logs the byte count
and the SSE algorithm S3 reports, and returns the body to the caller instead, where the demo
still demonstrates what it meant to.

**Both Lambdas reported success when they had failed.** Each caught its own errors with
`console.log(err)` and returned `undefined`, so a denied `kms:Decrypt`, a missing object or a
wrong bucket produced a *successful* invocation with nothing to show. They rethrow now, which is
what makes the invocation fail, retry per its configuration and appear in metrics. Only the
error's `name` and `code` are logged, because an AWS SDK error message can carry the bucket, the
key and the whole request.

The bucket, object key and KMS key also came from the source rather than the environment, one of
them a specific key ARN that no one else can use. They come from `process.env` now.

**Two IAM policies could disable the account's own monitoring.**
`cloudwatch-alarms-billing-CloudWatchMetricsPolicyForBilling.json` granted
`cloudwatch:SetAlarmState` and `cloudwatch:DeleteAlarms` on `Resource: "*"`, which is permission
to silence or delete *every* alarm in the account. Verified against the CloudWatch
service-authorization reference: those two, plus `PutMetricAlarm` and `DescribeAlarms`, accept an
alarm ARN, while `PutMetricData`, `GetMetricStatistics` and `ListMetrics` are defined without a
resource type and can only be `*`. So the policy is split along that line and the alarm half is
scoped to `alarm:billing-*`. Same treatment for `sns:DeleteTopic`, which was on `*` and could
have deleted any topic in the account.

**`SSM/SSM.yml` could not be deployed as written.** Four separate reasons:

- `ImageId: ami-0323c3dd2da7fb37d` was hardcoded. An AMI id is valid only in the region that
  published it and Amazon deregisters old ones, so the template failed outside `us-east-1` and
  eventually failed there too. It now takes the public SSM parameter
  `/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64`. **Amazon Linux 2023,
  not 2** — AL2 reached end of support on 2026-06-30, so defaulting to it would ship an OS that
  no longer receives security updates. Which family the original used is an inference rather than
  a fact: the id cannot be resolved any more, but the template installs no SSM agent, so its image
  must have shipped one, as both AL2 and AL2023 do.
- `RoleName` was hardcoded twice, which makes the stack undeployable a second time and collides
  with anything else using those names. Both are omitted so CloudFormation generates them.
- The security group had no `VpcId`, so it landed in the default VPC and the stack failed
  outright in any account whose default VPC has been removed.
- The login role trusted `Principal: root`, meaning every identity in the account. It now
  requires MFA, which is the same condition the sibling `IAM-role-for-users/test-trust-policy.json`
  already applied, so the repository had been inconsistent with itself.

**Both managed policies are dropped from that role**, and the second one mattered as much as the
first. `AmazonEC2ReadOnlyAccess` grants read on every EC2 resource in the account.
`AmazonSSMReadOnlyAccess` grants `ssm:Describe*`, `ssm:Get*` and `ssm:List*` on every Systems
Manager resource, which includes reading unrelated Parameter Store values. Everything the workflow
needs is enumerated in one inline policy instead, and `SSM/README.md` tabulates it.

**The session policy was also incomplete, so the documented command would have failed.** Checked
against AWS's own sample end-user policy for Session Manager:

- `ssm:StartSession` needs the **document** `SSM-SessionManagerRunShell` as well as the instance.
  With only the instance ARN, `aws ssm start-session` fails, because Session Manager reads its
  configuration from that document.
- `ssmmessages:OpenDataChannel` is a **user** permission, not only an instance one. The instance
  side comes from `AmazonSSMManagedInstanceCore`; the caller needs this for the data channel.
- The session ARN used `${aws:username}`, which **can never match here**. Per the IAM
  condition-key reference, `aws:username` is "always included in the request context for IAM
  users" while "requests that are made using ... IAM roles do not include this key". This role
  exists to be assumed, so terminate and resume would always have been denied. It is
  `${aws:userid}` now, which is what AWS's current samples use.

That last one is worth being blunt about: the previous revision of this README defended the
`${aws:username}` line at length, verified carefully that it must not be wrapped in `!Sub`, and
never asked whether the variable was the right one for an assumed role. The `!Sub` reasoning was
correct and the variable was wrong.

One thing in that file is **deliberately** not a `!Sub`:

```yaml
Resource: arn:aws:ssm:*:*:session/${aws:username}-*
```

`${aws:username}` is an IAM policy variable that IAM expands at evaluation time, so it has to
reach IAM as a literal. Wrapping it in `!Sub` makes CloudFormation try to resolve it: verified
with `cfn-lint`, which reports `E1019 'aws:username' is not one of [...]`.

**Placeholders were spelled three different ways** — `your-aws-account-id` (54 occurrences),
`your-admin-account-id` (11) and `your-account-id` (1) — alongside a concrete bucket name and two
real KMS key ids that read as placeholders but were not. All now `YOUR-ACCOUNT-ID`,
`YOUR-BUCKET-NAME` and `YOUR-KMS-KEY-ID`. The exercise answers under `security/txt/` are left
exactly as written, being the author's own work.

Recorded command output keeps its original identifiers on purpose, such as the load-balancer
hostname in `security/README.md`, so those are a stated exception rather than a miss.

**`validate-policies.py`** checks every `*.json` policy in the repository against the IAM
grammar, which is a *closed* set of keys: a stray element is rejected with
`MalformedPolicyDocument`, so it makes the file unusable rather than untidy. It also requires a
valid `Version`, a non-empty `Statement`, each statement to be an object, `Effect` to be exactly
`Allow` or `Deny`, exactly one of `Action`/`NotAction`, and a `Resource` on identity policies.

The first version checked only the key names, so it passed `"Effect": "allow"`, an empty
`Statement: []`, a statement with both `Action` and `NotAction`, and one with neither — and a
non-object statement crashed it with `AttributeError`, which meant one malformed file hid every
other file in the run. All seven rules are poison-tested individually.

```shell
python3 validate-policies.py
```

That check exists because writing this README broke two policies. Explanatory `"Comment"` keys
were added to five statements, which IAM does not permit, and JSON has no comment syntax to use
instead — which is why every explanation lives here rather than in the policy files.

The first version of the checker was also over-strict, and that is worth recording: it applied
the alphanumeric-only `Sid` rule to the KMS key policies and reported six valid statements as
broken. That rule is for IAM *identity* policies; resource policies permit more, and the AWS
console itself generates `Sid: "Allow access for Key Administrators"`. The rule is now applied
only to statements without a `Principal`. A linter that reports valid input is worse than none,
because the next person changes the input to satisfy it.

## Not covered

- **Nothing here has been run against AWS.** There are no credentials in this environment. The
  policies are validated against the IAM grammar, the templates with `cfn-lint`, and the Lambda
  sources with `node --check`; the recorded command output is from 2020.
- **`security/` is unchanged apart from the warnings.** Hardening it would destroy the exercises.
- **The two key policies under `encryption/` differ on purpose.** The one in `application/` is the
  same as the top-level one plus permission for the two Lambda roles to use the key, because the
  serverless walkthrough is the later stage. Neither is stale.
- **`cloudtrail.md` and `cloudwatch-alarms-billing.md` keep their recorded output**, including
  timestamps and resource ids from the original run.
