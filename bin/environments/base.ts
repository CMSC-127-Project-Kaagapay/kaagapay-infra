import * as cdk from "aws-cdk-lib";
import { StatelessStack } from "../../lib/stateless/stateless-stack";
import { StatefulStack } from "../../lib/stateful/stateful-stack";
import { GlobalStack } from "../../lib/global/global-stack";

export interface EnvironmentConfig {
  Stateful: any;
  Stateless: any;
  Global: any;
}

export function setupEnvironment(
  app: cdk.App,
  envConfig: EnvironmentConfig,
): {
  statefulStack: StatefulStack;
  statelessStack: StatelessStack;
  globalStack: GlobalStack;
} {
  const statefulStack = new StatefulStack(
    app,
    `${envConfig.Stateful.stage}-StatefulStack`,
    {
      ...envConfig.Stateful,
    },
  );

  const statelessStack = new StatelessStack(
    app,
    `${envConfig.Stateless.stage}-StatelessStack`,
    {
      ...envConfig.Stateless,
      crossRegionReferences: true,
      // Uncomment and pass props from statefulStack here when implemented
      // dataBucket: statefulStack.s3Construct.dataBucket,
      // dynamodbTable: statefulStack.dynamoDbConstruct.dataDb,
      // userPool: statefulStack.cognitoConstruct.userPool,
      // userPoolClient: statefulStack.cognitoConstruct.userPoolClient,
      corsOrigins: envConfig.Stateless.corsOrigins,
    },
  );

  const globalStack = new GlobalStack(
    app,
    `${envConfig.Global.stage}-GlobalStack`,
    {
      ...envConfig.Global,
      crossRegionReferences: true,
      // Uncomment and pass props from statelessStack here when implemented
      // apiEndpoint: statelessStack.apiEndpoint,
      // websiteBucket: statelessStack.websiteBucket,
    },
  );

  return { statefulStack, statelessStack, globalStack };
}
