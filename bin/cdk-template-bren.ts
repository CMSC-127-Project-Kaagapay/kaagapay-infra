#!/usr/bin/env node

import * as cdk from "aws-cdk-lib";
import { setupDevEnvironment } from "./environments/dev";
import { setupStagingEnvironment } from "./environments/staging";
import { setupProdEnvironment } from "./environments/prod";

const app = new cdk.App();

// Define environments
setupDevEnvironment(app);
setupStagingEnvironment(app);
setupProdEnvironment(app);