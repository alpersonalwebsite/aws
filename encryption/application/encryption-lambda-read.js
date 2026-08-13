const AWS = require('aws-sdk');
const s3 = new AWS.S3();

// The bucket and key come from the environment rather than being hardcoded. The previous
// version embedded a specific bucket name in the source, which meant the function only worked
// against one account's bucket and the name had to be edited to reuse the demo.
const BUCKET = process.env.BUCKET_NAME;
const KEY = process.env.OBJECT_KEY || 'hello-world.txt';

exports.handler = async () => {
  if (!BUCKET) {
    // Configuration errors are thrown, not logged and ignored. See the note on errors below.
    throw new Error('BUCKET_NAME is not set');
  }

  const params = { Bucket: BUCKET, Key: KEY };

  let data;
  try {
    data = await s3.getObject(params).promise();
  } catch (err) {
    // Rethrown, not swallowed. The previous version did `console.log(err)` and returned
    // undefined, so a missing object, a denied kms:Decrypt or a wrong bucket all produced a
    // SUCCESSFUL Lambda invocation with nothing to show for it. A thrown error is what makes
    // the invocation fail, retry per the function's configuration, and appear in metrics.
    //
    // Only the error's name and code are logged. An AWS SDK error message can carry the
    // bucket, the key and the full request, and this function exists to demonstrate keeping
    // data confidential.
    console.error(`getObject failed: ${err.name} (code: ${err.code})`);
    throw err;
  }

  // The point of this demo is that the object is encrypted at rest with KMS and that this role
  // is allowed to decrypt it. Proving that does NOT require printing the plaintext.
  //
  // The previous version did `console.log(data.Body.toString('utf-8'))`, which wrote the
  // decrypted content into CloudWatch Logs. Logs are a different security boundary from the
  // bucket: they are not encrypted with the same key, they are readable by anyone with
  // logs:FilterLogEvents, and they persist independently of the object. So a demo about
  // encryption at rest was quietly defeating itself in its last line.
  //
  // What is logged instead is enough to show the decryption worked: the SSE algorithm S3
  // reports, the KMS key it used, and the size of what came back.
  console.log(
    `decrypted ${data.ContentLength} bytes from s3://${BUCKET}/${KEY} ` +
      `(sse: ${data.ServerSideEncryption || 'none'}, kms key: ${data.SSEKMSKeyId ? 'present' : 'none'})`
  );

  // Returned rather than logged, so a caller can assert on it without the content touching
  // the log group.
  return {
    bytes: data.ContentLength,
    serverSideEncryption: data.ServerSideEncryption || null,
    body: data.Body.toString('utf-8')
  };
};
