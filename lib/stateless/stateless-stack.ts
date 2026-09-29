import * as cdk from 'aws-cdk-lib';
import * as path from 'path';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigatewayv2 from 'aws-cdk-lib/aws-apigatewayv2';
import { HttpLambdaIntegration } from 'aws-cdk-lib/aws-apigatewayv2-integrations';
import * as events from 'aws-cdk-lib/aws-events';
import * as targets from 'aws-cdk-lib/aws-events-targets';
import * as logs from 'aws-cdk-lib/aws-logs';
import { Construct } from 'constructs';
import { StatelessStackProps } from '../types';

export class StatelessStack extends cdk.Stack {
  public apiEndpoint: string;
  public fastApiFunction: lambda.DockerImageFunction;
  public cronWorkerFunction: lambda.DockerImageFunction;
  public httpApi: apigatewayv2.HttpApi;

  constructor(scope: Construct, id: string, props: StatelessStackProps) {
    super(scope, id, props);

    const lambdasDir = path.join(__dirname, '../../lambdas');

    // Common environment variables for FastAPI and workers
    const commonEnv: { [key: string]: string } = {
      STAGE: props.stage,
      DATABASE_URL: props.databaseUrl || '',
      SUPABASE_URL: props.supabaseUrl || '',
      SUPABASE_JWT_SECRET: props.supabaseJwtSecret || '',
      SUPABASE_SERVICE_ROLE_KEY: props.supabaseServiceRoleKey || '',
      S3_BUCKET_NAME: 'kaagapay-assets',
    };

    // 1. FastAPI Lambda Function (Docker Container Image)
    const fastApiLogGroup = new logs.LogGroup(this, `${props.stage}-FastApiLogGroup`, {
      logGroupName: `/aws/lambda/kaagapay-${props.stage}-fastapi`,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      retention: logs.RetentionDays.ONE_WEEK,
    });

    this.fastApiFunction = new lambda.DockerImageFunction(
      this,
      `${props.stage}-FastApiFunction`,
      {
        functionName: `kaagapay-${props.stage}-fastapi`,
        code: lambda.DockerImageCode.fromImageAsset(lambdasDir),
        memorySize: 1024,
        timeout: cdk.Duration.seconds(30),
        environment: commonEnv,
        logGroup: fastApiLogGroup,
      }
    );

    // 2. API Gateway HTTP API (v2) with $default proxy route
    const fastApiIntegration = new HttpLambdaIntegration(
      `${props.stage}-FastApiIntegration`,
      this.fastApiFunction
    );

    this.httpApi = new apigatewayv2.HttpApi(this, `${props.stage}-HttpApi`, {
      apiName: `kaagapay-${props.stage}-api`,
      defaultIntegration: fastApiIntegration,
      corsPreflight: {
        allowOrigins: props.corsOrigins && props.corsOrigins.length > 0 ? props.corsOrigins : ['*'],
        allowMethods: [
          apigatewayv2.CorsHttpMethod.GET,
          apigatewayv2.CorsHttpMethod.POST,
          apigatewayv2.CorsHttpMethod.PUT,
          apigatewayv2.CorsHttpMethod.PATCH,
          apigatewayv2.CorsHttpMethod.DELETE,
          apigatewayv2.CorsHttpMethod.OPTIONS,
        ],
        allowHeaders: ['*'],
        maxAge: cdk.Duration.days(1),
      },
    });

    this.apiEndpoint = this.httpApi.apiEndpoint;

    // 3. Dedicated Cron Worker Lambda Function (Docker Image with worker_handler.handler override)
    const cronWorkerLogGroup = new logs.LogGroup(this, `${props.stage}-CronWorkerLogGroup`, {
      logGroupName: `/aws/lambda/kaagapay-${props.stage}-cron-worker`,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      retention: logs.RetentionDays.ONE_WEEK,
    });

    this.cronWorkerFunction = new lambda.DockerImageFunction(
      this,
      `${props.stage}-CronWorkerFunction`,
      {
        functionName: `kaagapay-${props.stage}-cron-worker`,
        code: lambda.DockerImageCode.fromImageAsset(lambdasDir, {
          cmd: ['worker_handler.handler'],
        }),
        memorySize: 512,
        timeout: cdk.Duration.seconds(60),
        environment: commonEnv,
        logGroup: cronWorkerLogGroup,
      }
    );

    // 4. EventBridge Scheduled Rule: Triggers every 1 minute
    const cronRule = new events.Rule(this, `${props.stage}-WorkerCronRule`, {
      ruleName: `${props.stage}-kaagapay-worker-schedule`,
      schedule: events.Schedule.rate(cdk.Duration.minutes(1)),
      description: 'Triggers ticket timeout worker and notification fanout every 1 minute',
    });

    cronRule.addTarget(new targets.LambdaFunction(this.cronWorkerFunction));

    // Stack Outputs
    new cdk.CfnOutput(this, 'ApiEndpointUrl', {
      value: this.httpApi.apiEndpoint,
      description: 'API Gateway HTTP API URL',
      exportName: `${props.stage}-ApiEndpointUrl`,
    });

    new cdk.CfnOutput(this, 'FastApiFunctionName', {
      value: this.fastApiFunction.functionName,
      description: 'FastAPI Lambda Function Name',
    });

    new cdk.CfnOutput(this, 'CronWorkerFunctionName', {
      value: this.cronWorkerFunction.functionName,
      description: 'Cron Worker Lambda Function Name',
    });
  }
}
