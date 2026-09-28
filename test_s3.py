import boto3
from botocore.client import Config

s3_client = boto3.client(
    's3',
    endpoint_url="https://br-lingering-credit-b5d7aobn.storage.c-7.us-east-2.aws.neon.tech",
    aws_access_key_id="nak_live_a984330bcfae4e7c8092fa5a572e104a",
    aws_secret_access_key="nsk_live_c8c2c85e127f181994b0ec8e9982c10bbca142eac706ce1394671caed4f2d674",
    region_name="us-east-2",
    config=Config(signature_version='s3v4', s3={'addressing_style': 'path'})
)

try:
    url = s3_client.generate_presigned_url(
        'get_object',
        Params={'Bucket': 'screenshots', 'Key': 'test.jpg'},
        ExpiresIn=3600
    )
    print("URL:", url)
except Exception as e:
    print("ERROR:", e)
