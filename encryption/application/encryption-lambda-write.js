const AWS = require('aws-sdk');
const s3 = new AWS.S3();

// From the environment, not hardcoded. The KMS key in particular was a specific key ARN in the
// source, which is account- and region-specific and cannot be reused.
const BUCKET = process.env.BUCKET_NAME;
const KEY = process.env.OBJECT_KEY || 'hello-world.txt';
const KMS_KEY_ID = process.env.KMS_KEY_ID;
const CONTENT = process.env.OBJECT_BODY || 'Hello World!';

exports.handler = async () => {
  if (!BUCKET) throw new Error('BUCKET_NAME is not set');
  if (!KMS_KEY_ID) {
    // Deliberately fatal. Without SSEKMSKeyId, S3 falls back to the bucket's default
    // encryption, so a missing key id would silently write the object with different (or no)
    // encryption than this demo claims to be showing.
    throw new Error('KMS_KEY_ID is not set, and this demo is specifically about SSE-KMS');
  }

  const params = {
    Bucket: BUCKET,
    Key: KEY,
    Body: CONTENT,
    ServerSideEncryption: 'aws:kms',
    SSEKMSKeyId: KMS_KEY_ID
  };

  let result;
  try {
    result = await s3.putObject(params).promise();
  } catch (err) {
    // Rethrown for the same reason as the read function: the previous version logged the error
    // and returned undefined, so a denied kms:GenerateDataKey or a missing bucket produced a
    // successful invocation that had written nothing. Only name and code are logged, because an
    // SDK error message can carry the bucket and key.
    console.error(`putObject failed: ${err.name} (code: ${err.code})`);
    throw err;
  }

  // The previous version assigned the result to `data` and never used it.
  console.log(`wrote s3://${BUCKET}/${KEY} encrypted with aws:kms (etag: ${result.ETag})`);

  return { etag: result.ETag, serverSideEncryption: 'aws:kms' };
};
