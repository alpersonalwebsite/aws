# Security

## Deploying Infrastructure 

### S3 buckets

```shell
aws cloudformation create-stack --region us-east-1 --stack-name s3 --template-body file://infrastructure/s3.yml
```

*S3 created...*
S3BucketRecipesFree > cand-c3-free-recipes-your-aws-account-id
S3BucketRecipesSecret > cand-c3-secret-recipes-your-aws-account-id
S3BucketVPCFlowLogs > arn:aws:s3:::cand-c3-vpc-flow-logs-your-aws-account-id

### VPC and Subnets

```shell
aws cloudformation create-stack --region us-east-1 --stack-name vpc --template-body file://infrastructure/vpc.yml
```

### Application

```shell
aws cloudformation create-stack --region us-east-1 --stack-name app --template-body file://infrastructure/app.yml --parameters ParameterKey=KeyPair,ParameterValue=YourServiceClientKP --capabilities CAPABILITY_IAM
```

*Notes*:
You will need the Application Load Balancer endpoint to test the web service - ApplicationURL
You will need the web application EC2 instance public IP address to simulate the attack - ApplicationInstanceIP
You will need the public IP address of the attack instance from which to run the attack scripts - AttackInstanceIP


## Upload data to S3 buckets 

```shell
aws s3 cp resources/recipes/free_recipe.txt s3://cand-c3-free-recipes-your-aws-account-id/ --region us-east-1

aws s3 cp resources/recipes/secret_recipe.txt s3://cand-c3-secret-recipes-your-aws-account-id/ --region us-east-1
```

## Test application

Example: http://c1-web-service-alb-644757268.us-east-1.elb.amazonaws.com/free_recipe

... where `http://c1-web-service-alb-644757268.us-east-1.elb.amazonaws.com/` is the endpoint of the ALB
(check the `app` stack outputs > `ApplicationURL`)

Example output:
```
Banana-Nut (opt) Bread Category: Breads: Bread, muffins, rolls, etc. Classification: Public, free Quantity: one loaf (well?!) Ingredients: 1/3 cup shortening 1/2 cup sugar 2 eggs 1 3/4 cup all-purpose flour 1 tsp. baking powder 1/2 tsp. soda 1/2 tsp. salt 1 cup mashed ripe bananas 1/2 cup chopped nuts (optional) Instructions: Preheat oven to 350 degrees F. Cream shortening and sugar; add eggs and beat. Sift dry ingredients; add alternatively with banana. Blend well. Stir in nuts. Pour into well-greased 9 1/2 x 5 x 3 inch loaf pan. Bake 40-45 minutes. Cool on rack. Comments: My mom's recipe. 
```

---
---
---

## Enable Security Monitoring

### Enable AWS Config

1. Default settings plus select ` Include global resources (e.g., AWS IAM resources) ` option
2. Skip Rules
3. Confirm

### Enable AWS Security Hub

1. From the Security Hub landing page, click Go To Security Hub
2. Enable Security Hub

### Enable AWS Inspector scan

1. Keep defaults
2. Click on Advanced setup
    1. Uncheck All Instances and Install Agents.
    1. Under `Tags`, Choose Name for Key and ‘Web Service Instance - C3’ for value, click Next.
3. Remove `Common Vulnerabilities and Exposures-1.1` (x)
4. Remove `CIS Operating System Security Configuration Benchmarks-1.0` (x)
5. Duration: 15 minutes
6. Uncheck `Assessment Schedule`

### Enable AWS Guard Duty

---
---
---

## Attack Simulation

We will simulate the following attack conditions: Making an SSH connection to the application server using brute force password cracking. Capturing secret recipe files from the s3 bucket using stolen API keys.

### Brute force attack to exploit SSH ports facing the internet and an insecure configuration on the server

1. Log into the attack simulation server using your SSH key-pair.

```shell
cd .ssh/
ssh -i YourServiceClientKP.pem ubuntu@ec2-54-152-203-174.compute-1.amazonaws.com
```

2. Start attack to the server

```shell
date
hydra -l ubuntu -P rockyou.txt ssh://ec2-23-23-34-174.compute-1.amazonaws.com
```

### Accessing Secret Recipe Data File from S3

Note: Still from the Attack instance

```shell
aws s3 ls  s3://cand-c3-secret-recipes-your-aws-account-id/ --region us-east-1

aws s3 cp s3://cand-c3-secret-recipes-your-aws-account-id/secret_recipe.txt  .  --region us-east-1

cat secret_recipe.txt
```

Result:
```
Baklava
Category: Desserts:  Cake, cookies, mousse, puddings, etc..
Classification:     Paid, Secret
Quantity: (makes about 100 2 1/2 inch long diamonds)

Ingredients:
Simmer a syrup of:              1/2 cup sugar or honey
  3/4 cup water                 1/2 lemon
until it is thick enough to
coat the back of a spoon.
Remove the lemon.  Add:         1 Tbsp. orange-blossom
                              water
and simmer a few minutes
longer.  Cool and
refrigerate.
Prepare a filling of:           1 1/2 cups coarsely
                              chopped nuts: almonds,
                              pistachios and walnuts in
                              any proportion

sprinkle the nuts with a        2 Tbsp. sugar
mixture of:
  1 tsp. cinnamon               1/8 tsp. cloves
Melt
  1 cup sweet butter          Have ready 24 sheets phyllo
                              dough (1 lb.)


Instructions:
Layer 12 of them on an 11 x 15 inch buttered baklava pan,
brushing the sheets of dough with about half the butter.
Spread the filling on top and cover with the remaining 12
similarly buttered sheets. Preheat oven to 350 F. Cut the
top layered sheets and filling diagonally into 2 inch long
diamonds, but leave the bottom few layers uncut.  Bake about
30 minutes.  Raise oven temperature to 475 F. and bake about
15 minutes longer or until golden.  Remove from oven.  Pour
the refrigerated syrup over the top of puffed dough. Cut,
using the same diagonals, through the uncut layer of dough
and serve the diamond-shaped slices when cooled.
```

---
---
---

## Hardening

### Remove SSH Vulnerability on the Application Instance

Disable SSH password login on the application server instance.

*Note*: We should SSH the server instance, not the attacker.
 
```shell
cd .ssh/
ssh -i YourServiceClientKP.pem ubuntu@ec2-23-23-34-174.compute-1.amazonaws.com

sudo vi /etc/ssh/sshd_config
```

Replace `PasswordAuthentication yes` with `PasswordAuthentication no`

Hints:
1. Hit any character to start edition.
2. Once you finish editing, press `Esc`, type `:wq!` and hit `Enter` (to save and exit)



### Restart SSH server

```shell
sudo service ssh restart
```

### Attack again

First, exit and SSH into the attacker instance.

```shell
exit
ssh -i YourServiceClientKP.pem ubuntu@ec2-54-152-203-174.compute-1.amazonaws.com
```

Then, start attack to the server

```shell
hydra -l ubuntu -P rockyou.txt ssh://ec2-23-23-34-174.compute-1.amazonaws.com
```

Expected output:
```shell
Hydra v8.6 (c) 2017 by van Hauser/THC - Please do not use in military or secret service organizations, or for illegal purposes.

Hydra (http://www.thc.org/thc-hydra) starting at 2020-07-03 01:00:21
[WARNING] Many SSH configurations limit the number of parallel tasks, it is recommended to reduce the tasks: use -t 4
[WARNING] Restorefile (you have 10 seconds to abort... (use option -I to skip waiting)) from a previous session found, to prevent overwriting, ./hydra.restore
[DATA] max 16 tasks per 1 server, overall 16 tasks, 14344400 login tries (l:1/p:14344400), ~896525 tries per task
[DATA] attacking ssh://ec2-23-23-34-174.compute-1.amazonaws.com:22/
[ERROR] target ssh://10.192.10.13:22/ does not support password authentication.
```

### Update the security group

Our `Web Instance` has the SG `sg-02a07eee0db50dd42` or `WebAppSG` (by name), with the following `inbound rules`

```
HTTP -> TCP -> 80 -> 0.0.0.0/0
All traffic -> All -> All -> 0.0.0.0/0
SSH -> TCP -> 22 -> 0.0.0.0/0
Custom TCP -> TCP -> 5000 -> 0.0.0.0/0
```

We are going to remove ALL and add a new one with port 5000 and our `Load Balancer SG` as source.

Example:

```
Custom TCP -> TCP -> 5000 -> sg-0b3a674138514e054 (AppLoadBalancerSG)
```

Now, you should not be able to `SSH` into the `Web Instance`

```shell
ssh -i YourServiceClientKP.pem ubuntu@ec2-23-23-34-174.compute-1.amazonaws.com
```

Expected output:

```shell
ssh: connect to host ec2-23-23-34-174.compute-1.amazonaws.com port 22: Operation timed out
```

### Least Privilege Access to S3

#### Update the IAM policy for the instance profile role used by the web application instance to only allow read access to the free recipes S3 bucket.

Go to the policy `InstanceRolePolicy-C3`

Current:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": "s3:*",
            "Resource": "*",
            "Effect": "Allow"
        }
    ]
}
```

NEW policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::cand-c3-free-recipes-your-aws-account-id/*",
            "Effect": "Allow"
        }
    ]
}
```

Let's try that our policy is working as expected.

#### SSH into the attacker instance

```shell
cd .ssh/
ssh -i YourServiceClientKP.pem ubuntu@ec2-54-152-203-174.compute-1.amazonaws.com
```

#### Try to access the secret bucket


```shell
aws s3 ls  s3://cand-c3-secret-recipes-your-aws-account-id/ --region us-east-1

aws s3 cp s3://cand-c3-secret-recipes-your-aws-account-id/secret_recipe.txt  .  --region us-east-1
```

Expected output:
```shell
An error occurred (AccessDenied) when calling the ListObjects operation: Access Denied

fatal error: An error occurred (403) when calling the HeadObject operation: Forbidden
```

### Apply Default Server-side Encryption to the S3 Bucket

```shell
aws s3api put-bucket-encryption \
    --bucket cand-c3-secret-recipes-your-aws-account-id \
    --server-side-encryption-configuration '{"Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]}'
```

### Run AWS Inspector (again)

1. Go to AWS Inspector
2. Click on Assessment runs
3. Select you assessment
4. Click on Run


