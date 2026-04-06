import * as cdk from 'aws-cdk-lib';
import * as s3 from 'aws-cdk-lib/aws-s3';
import { Construct } from 'constructs';
import { BaseConstructProps } from '../../types';

export interface S3ConstructProps extends BaseConstructProps {}

export class S3Construct extends Construct {
  public dataBucket: s3.Bucket;
  public assetsBucket: s3.Bucket;

  constructor(scope: Construct, id: string, props: S3ConstructProps) {
    super(scope, id);

    this.createDataBucket(props);
    this.createAssetsBucket(props);
  }

  private createDataBucket(props: S3ConstructProps): void {
    this.dataBucket = new s3.Bucket(this, `${props.stage}-S3-Bucket-Data`, {
      bucketName: `${props.stage}-s3-bucket-data`.toLowerCase(), // Note: bucket names must be globally unique
      encryption: s3.BucketEncryption.S3_MANAGED,
      versioned: true,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      removalPolicy:
        props.stage === 'dev'
          ? cdk.RemovalPolicy.DESTROY
          : cdk.RemovalPolicy.RETAIN,
      autoDeleteObjects: props.stage === 'dev',
      cors: [
        {
          allowedOrigins: ['*'], // Example: restrict in production
          allowedMethods: [
            s3.HttpMethods.GET,
            s3.HttpMethods.POST,
            s3.HttpMethods.PUT,
            s3.HttpMethods.DELETE,
            s3.HttpMethods.HEAD,
          ],
          allowedHeaders: ['*'],
          exposedHeaders: ['ETag'],
          maxAge: 3000,
        },
      ],
    });
  }

  private createAssetsBucket(props: S3ConstructProps): void {
    this.assetsBucket = new s3.Bucket(this, `${props.stage}-S3-Bucket-Assets`, {
      bucketName: `${props.stage}-s3-bucket-assets`.toLowerCase(), // Note: bucket names must be globally unique
      encryption: s3.BucketEncryption.S3_MANAGED,
      versioned: true,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      removalPolicy:
        props.stage === 'dev'
          ? cdk.RemovalPolicy.DESTROY
          : cdk.RemovalPolicy.RETAIN,
      autoDeleteObjects: props.stage === 'dev',
    });
  }
}
