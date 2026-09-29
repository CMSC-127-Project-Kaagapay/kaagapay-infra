import * as cdk from 'aws-cdk-lib';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';
import * as origins from 'aws-cdk-lib/aws-cloudfront-origins';
import { Construct } from 'constructs';
import { GlobalStackProps } from '../types';

export class GlobalStack extends cdk.Stack {
  public websiteBucket: s3.Bucket;
  public distribution: cloudfront.Distribution;

  constructor(scope: Construct, id: string, props: GlobalStackProps) {
    super(scope, id, props);

    // Private S3 website bucket to host the React SPA
    this.websiteBucket = new s3.Bucket(this, `${props.stage}-S3-Bucket-Website`, {
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      removalPolicy:
        props.stage === 'dev'
          ? cdk.RemovalPolicy.DESTROY
          : cdk.RemovalPolicy.RETAIN,
      autoDeleteObjects: props.stage === 'dev',
    });

    // CloudFront distribution fronting the S3 website bucket with Origin Access Control (OAC)
    this.distribution = new cloudfront.Distribution(
      this,
      `${props.stage}-CloudFrontDistribution`,
      {
        comment: `${props.stage} CloudFront distribution for Kaagapay frontend`,
        defaultRootObject: 'index.html',
        defaultBehavior: {
          origin: origins.S3BucketOrigin.withOriginAccessControl(this.websiteBucket),
          viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
          cachePolicy: cloudfront.CachePolicy.CACHING_OPTIMIZED,
          allowedMethods: cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
        },
        // Single Page Application (SPA) custom error responses
        errorResponses: [
          {
            httpStatus: 403,
            responseHttpStatus: 200,
            responsePagePath: '/index.html',
            ttl: cdk.Duration.minutes(0),
          },
          {
            httpStatus: 404,
            responseHttpStatus: 200,
            responsePagePath: '/index.html',
            ttl: cdk.Duration.minutes(0),
          },
        ],
      }
    );

    // Outputs for CI/CD and Frontend deployment
    new cdk.CfnOutput(this, 'WebsiteBucketName', {
      value: this.websiteBucket.bucketName,
      description: 'S3 Website Bucket Name for Frontend Assets',
      exportName: `${props.stage}-WebsiteBucketName`,
    });

    new cdk.CfnOutput(this, 'CloudFrontDistributionId', {
      value: this.distribution.distributionId,
      description: 'CloudFront Distribution ID for Cache Invalidation',
      exportName: `${props.stage}-CloudFrontDistributionId`,
    });

    new cdk.CfnOutput(this, 'CloudFrontDomainName', {
      value: this.distribution.distributionDomainName,
      description: 'CloudFront Distribution Domain URL',
      exportName: `${props.stage}-CloudFrontDomainName`,
    });
  }
}
