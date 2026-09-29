import * as cdk from "aws-cdk-lib";
import { StatelessStack } from "../../lib/stateless/stateless-stack";
import { GlobalStack } from "../../lib/global/global-stack";

export interface EnvironmentConfig {
  Stateless: any;
  Global: any;
  Stateful?: any;
}

export function setupEnvironment(
  app: cdk.App,
  envConfig: EnvironmentConfig,
): {
  statelessStack: StatelessStack;
  globalStack: GlobalStack;
} {
  const statelessStack = new StatelessStack(
    app,
    `${envConfig.Stateless.stage}-StatelessStack`,
    {
      ...envConfig.Stateless,
      corsOrigins: envConfig.Stateless.corsOrigins,
      databaseUrl:
        app.node.tryGetContext("databaseUrl") ||
        process.env.DATABASE_URL ||
        envConfig.Stateless.databaseUrl,
      supabaseUrl:
        app.node.tryGetContext("supabaseUrl") ||
        process.env.SUPABASE_URL ||
        envConfig.Stateless.supabaseUrl,
      supabaseJwtSecret:
        app.node.tryGetContext("supabaseJwtSecret") ||
        process.env.SUPABASE_JWT_SECRET ||
        envConfig.Stateless.supabaseJwtSecret,
      supabaseServiceRoleKey:
        app.node.tryGetContext("supabaseServiceRoleKey") ||
        process.env.SUPABASE_SERVICE_ROLE_KEY ||
        envConfig.Stateless.supabaseServiceRoleKey,
    },
  );

  const globalStack = new GlobalStack(
    app,
    `${envConfig.Global.stage}-GlobalStack`,
    {
      ...envConfig.Global,
      apiEndpoint: statelessStack.apiEndpoint,
    },
  );

  return { statelessStack, globalStack };
}
