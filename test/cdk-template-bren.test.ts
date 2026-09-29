import * as cdk from 'aws-cdk-lib';
import { Template } from 'aws-cdk-lib/assertions';
import { setupDevEnvironment } from '../bin/environments/dev';

test('Dev Environment Stacks Synthesize Correctly', () => {
  const app = new cdk.App();
  const { statelessStack, globalStack } = setupDevEnvironment(app);

  const statelessTemplate = Template.fromStack(statelessStack);
  const globalTemplate = Template.fromStack(globalStack);

  // Assert API Gateway HTTP API, Lambdas, and EventBridge Rule created in Stateless
  statelessTemplate.resourceCountIs('AWS::ApiGatewayV2::Api', 1);
  statelessTemplate.resourceCountIs('AWS::Lambda::Function', 2);
  statelessTemplate.resourceCountIs('AWS::Events::Rule', 1);

  // Assert S3 Website Bucket and CloudFront Distribution created in Global
  globalTemplate.resourceCountIs('AWS::S3::Bucket', 1);
  globalTemplate.resourceCountIs('AWS::CloudFront::Distribution', 1);
});
