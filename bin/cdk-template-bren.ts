#!/usr/bin/env node

import * as cdk from "aws-cdk-lib";
import { setupDevEnvironment } from "./environments/dev";
import { setupStagingEnvironment } from "./environments/staging";
import { setupProdEnvironment } from "./environments/prod";

const app = new cdk.App();

// Determine target stage from context (-c stage=dev) or environment variable (STAGE=dev)
const targetStage = app.node.tryGetContext("stage") || process.env.STAGE;

if (targetStage === "prod") {
  setupProdEnvironment(app);
} else if (targetStage === "staging") {
  setupStagingEnvironment(app);
} else if (targetStage === "dev") {
  setupDevEnvironment(app);
} else {
  // Default / fallback: define all environments for multi-stack commands
  setupDevEnvironment(app);
  setupStagingEnvironment(app);
  setupProdEnvironment(app);
}