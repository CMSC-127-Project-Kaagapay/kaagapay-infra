import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { StatelessStackProps } from '../types';

export class StatelessStack extends cdk.Stack {
  // Public properties to expose resources to other stacks (like GlobalStack)
  // public apiEndpoint: string;
  // public websiteBucket: s3.IBucket;

  constructor(scope: Construct, id: string, props: StatelessStackProps) {
    super(scope, id, props);

    // Initialize stateless constructs here (e.g., Lambda, API Gateway)
    // Pass references from StatefulStack via props
    
    // Example:
    // this.createApiGatewayConstruct(props);
  }
}
