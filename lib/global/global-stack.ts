import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { GlobalStackProps } from '../types';

export class GlobalStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: GlobalStackProps) {
    super(scope, id, props);

    // Initialize global constructs here (e.g., CloudFront, ACM Certificates, Route53)
    // Note: Global stack should typically be deployed in us-east-1 for AWS resources like WAF or ACM that attach to CloudFront
  }
}
