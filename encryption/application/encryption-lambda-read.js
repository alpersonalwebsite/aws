const AWS = require('aws-sdk');
const s3 = new AWS.S3();

exports.handler = async (event) => {

  const bucketName = 'my-bucket-8200334565';
  const keyName = 'hello-world.txt';

  const params = {
    'Bucket': bucketName,
    'Key': keyName
  };

  try {
    const data = await s3.getObject(params).promise();
    console.log(data.Body.toString('utf-8'))
  } catch (err) {
    console.log(err)
  }
}