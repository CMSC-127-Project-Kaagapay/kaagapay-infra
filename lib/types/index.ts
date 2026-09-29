import * as cdk from "aws-cdk-lib";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as cognito from "aws-cdk-lib/aws-cognito";

export interface BaseConstructProps {
  stage: string;
}

export interface BaseStackProps extends cdk.StackProps {
  stage: string;
}

export interface StatefulStackProps extends BaseStackProps {}

export interface StatelessStackProps extends BaseStackProps {
  corsOrigins?: string[];
  databaseUrl?: string;
  supabaseUrl?: string;
  supabaseJwtSecret?: string;
  supabaseServiceRoleKey?: string;
}

export interface GlobalStackProps extends BaseStackProps {
  apiEndpoint?: string;
}
