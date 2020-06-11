# CloudWatch Billing Alarm 

## Create groups and assign policies

```shell
aws iam create-group --group-name Reviewers

aws iam list-policies --query 'Policies[?starts_with(PolicyName,`Billing`)]'

aws iam attach-group-policy --policy-arn arn:aws:iam::aws:policy/job-function/Billing --group-name Reviewers

aws iam attach-group-policy --policy-arn arn:aws:iam::aws:policy/IAMUserChangePassword --group-name Reviewers
```

I am adding `arn:aws:iam::aws:policy/IAMUserChangePassword` so users can change their passwords.

## Create custom policy for CloudWatch Metrics

```shell
aws iam create-policy --policy-name CloudWatchMetricsPolicyForBilling --policy-document file://cloudwatch-alarms-billing-CloudWatchMetricsPolicyForBilling.json
```

cloudwatch-alarms-billing-CloudWatchMetricsPolicyForBilling.json

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "cloudwatch:GetMetricStatistics",
        "cloudwatch:ListMetrics",
        "cloudwatch:PutMetricData",
        "cloudwatch:PutMetricAlarm",
        "cloudwatch:SetAlarmState",
        "cloudwatch:DescribeAlarms",
        "cloudwatch:DeleteAlarms"
      ],
      "Effect": "Allow",
      "Resource": "*"
    }
  ]
}
```

## Create policy to create and manage topics

```shell
aws iam create-policy --policy-name SNSCreateAndManageTopics --policy-document file://cloudwatch-alarms-billing-SNSCreateAndManageTopics.json
```

cloudwatch-alarms-billing-SNSCreateAndManageTopics.json

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sns:CreateTopic",
        "sns:ListTopics",
        "sns:SetTopicAttributes",
        "sns:DeleteTopic"
      ],
      "Resource": "*"
    }
  ]
}
```

## Add policies to group

```shell
aws iam attach-group-policy --policy-arn arn:aws:iam::your-admin-account-id:policy/CloudWatchMetricsPolicyForBilling --group-name Reviewers

aws iam attach-group-policy --policy-arn arn:aws:iam::your-admin-account-id:policy/SNSCreateAndManageTopics --group-name Reviewers
```

If we need to make a change in the policies, we have to create a new version (up to 5)
Example:
```shell
aws iam create-policy-version --policy-arn arn:aws:iam::your-admin-account-id:policy/CloudWatchMetricsPolicyForBilling --policy-document file://cloudwatch-alarms-billing-CloudWatchMetricsPolicyForBilling.json --set-as-default
```

## Create users and provide proper access

```shell
aws iam create-user --user-name Accountant
aws iam create-login-profile --user-name Accountant --password 'your-password' --password-reset-required
```

## Add users to groups

```shell
aws iam add-user-to-group --user-name Accountant --group-name Reviewers
```

## Cost Monitoring

1. Configure CloudWatch billing alarm
2. Set up a Billing alarm with a $5 threshold
3. Set up notification so that you get an email alert when the alarm is triggered.

### Create SNS topic

```shell
aws sns create-topic --name billing-alarm-topic
```

This will return our topic's ARN:

```shell
{
    "TopicArn": "arn:aws:sns:us-east-1:your-admin-account-id:billing-alarm-topic"
}
```

### Subscribe to that topic

```shell
aws sns subscribe --topic-arn arn:aws:sns:us-east-1:your-admin-account-id:billing-alarm-topic \
  --protocol email \
  --notification-endpoint your-email@email.com
```

Amazon SNS returns the following:

```shell
{
    "SubscriptionArn": "pending confirmation"
}
```

Then, **open the email** and click on **Confirm subscription** 

You should see **Subscription confirmed!**

Alternatively, you can check with the cli the current status of your subscription:

```shell
aws sns list-subscriptions-by-topic \
  --topic-arn arn:aws:sns:us-east-1:your-admin-account-id:billing-alarm-topic
```

To be sure everything is working as expected we can publish a message to that topic.

```shell
aws sns publish --message "Testing" \
  --topic arn:aws:sns:us-east-1:your-admin-account-id:billing-alarm-topic
```

You should receive an email like this:

```html
AWS Notifications <no-reply@sns.amazonaws.com>
Mié 10/06/2020 10:10 AM

Testing
```

### Create alarm

*Note:* List of namespaces... https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/aws-services-cloudwatch-metrics.html

```shell
aws cloudwatch put-metric-alarm --alarm-name aws-billing-alarm \
  --alarm-description 'AWS Billing Alarm' \
  --metric-name EstimatedCharges \
  --namespace AWS/Billing \
  --statistic Maximum \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --period 21600 \
  --evaluation-periods 1 \
  --treat-missing-data missing \
  --alarm-actions arn:aws:sns:us-east-1:your-admin-account-id:billing-alarm-topic \
  --dimensions "Name=Currency,Value=USD"
```