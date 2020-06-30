const AWS = require('aws-sdk');
const s3 = new AWS.S3();

exports.handler = async (event) => {

  const bucketName = 'my-bucket-8200334565';
  const keyName = 'hello-world.txt';
  const content = 'Hello World!';

  const params = {
    'Bucket': bucketName,
    'Key': keyName,
    'Body': content,
    'ServerSideEncryption': 'aws:kms',
    'SSEKMSKeyId': 'arn:aws:kms:us-east-1:your-aws-account-id:key/c556d894-361e-437a-8890-e70fa95a835c'
  };

  try {
    const data = await s3.putObject(params).promise();
  } catch (err) {
    console.log(err)
  }
}